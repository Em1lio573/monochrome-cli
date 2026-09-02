"""
Unit and Integration tests for Unified Lossless Engine & Downloader in Monochrome CLI.
"""
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add parent directory to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from monochrome_cli.config import config
from monochrome_cli.core.downloader import Downloader
from monochrome_cli.core.unified import UnifiedEngine
from monochrome_cli.types import AudioFormat, StreamResolution, TrackMetadata


class TestUnifiedEngine(unittest.TestCase):
    def test_quality_mapping(self):
        self.assertEqual(UnifiedEngine._map_quality(AudioFormat.FLAC), "HI_RES_LOSSLESS")
        self.assertEqual(UnifiedEngine._map_quality(AudioFormat.MP3_320), "LOSSLESS")
        self.assertEqual(UnifiedEngine._map_quality(AudioFormat.MP3_128), "HIGH")

        self.assertEqual(UnifiedEngine._map_deezer_format(AudioFormat.FLAC), "FLAC")
        self.assertEqual(UnifiedEngine._map_deezer_format(AudioFormat.MP3_320), "MP3_320")
        self.assertEqual(UnifiedEngine._map_deezer_format(AudioFormat.MP3_128), "MP3_128")

    @patch("urllib.request.urlopen")
    def test_resolve_unified_playback_amazon_cenc(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.read.return_value = json.dumps({
            "schema_version": "2.0",
            "selected_source": "amazon",
            "playback": [{
                "source": "amazon",
                "kind": "audio",
                "delivery": "direct",
                "url": "https://amz-stream.example.com/track.mp4",
                "quality": "HI_RES_LOSSLESS",
                "codec": "flac",
                "decryption_key": "0123456789abcdef0123456789abcdef",
                "key_id": "fedcba9876543210fedcba9876543210",
                "bit_depth": 24,
                "sample_rate": 96000
            }]
        }).encode("utf-8")
        mock_cm = MagicMock()
        mock_cm.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_cm

        track = TrackMetadata(
            title="Blinding Lights",
            artist="The Weeknd",
            album="After Hours",
            isrc="USUM71900764",
            duration_seconds=200
        )

        res = UnifiedEngine.resolve_stream(track, AudioFormat.FLAC)
        self.assertIsNotNone(res)
        self.assertEqual(res.source, "amazon")
        self.assertTrue(res.is_cenc)
        self.assertEqual(res.decryption_key, "0123456789abcdef0123456789abcdef")
        self.assertIn("Amazon Music", res.display_source)
        print("  ✔ Unified Playback Amazon CENC resolution verified!")

    @patch("urllib.request.urlopen")
    def test_resolve_deezer_fallback(self, mock_urlopen):
        def urlopen_side_effect(req, *args, **kwargs):
            url = req.full_url if hasattr(req, "full_url") else str(req)
            if "music-api.geeked.wtf" in url:
                mock_err = MagicMock()
                mock_err.status = 404
                mock_err.read.return_value = b"{}"
                mock_cm = MagicMock()
                mock_cm.__enter__.return_value = mock_err
                return mock_cm
            elif "dzr.tabs-vs-spaces.wtf" in url:
                mock_dzr = MagicMock()
                mock_dzr.status = 200
                mock_cm = MagicMock()
                mock_cm.__enter__.return_value = mock_dzr
                return mock_cm
            raise ValueError(f"Unexpected url {url}")

        mock_urlopen.side_effect = urlopen_side_effect

        track = TrackMetadata(
            title="Some Rare Track",
            artist="Indie Artist",
            album="Indie Album",
            isrc="GBDUW0000053",
            duration_seconds=180
        )

        res = UnifiedEngine.resolve_stream(track, AudioFormat.FLAC)
        self.assertIsNotNone(res)
        self.assertEqual(res.source, "deezer")
        self.assertEqual(res.quality, "FLAC")
        self.assertIn("Deezer", res.display_source)
        print("  ✔ Deezer ISRC Fallback resolution verified!")

    @patch("monochrome_cli.core.unified.UnifiedEngine.resolve_stream")
    @patch("monochrome_cli.core.downloader.Downloader._download_from_soundcloud")
    @patch("monochrome_cli.core.tagger.MetadataTagger.apply_metadata")
    def test_downloader_fallback_to_soundcloud(self, mock_tagger, mock_sc, mock_resolve):
        mock_resolve.return_value = None  # Lossless not available
        mock_sc.return_value = True  # SoundCloud succeeds

        with tempfile.TemporaryDirectory() as tmpdir:
            track = TrackMetadata(
                title="Unreleased Leak",
                artist="Artist X",
                album="Unknown",
                duration_seconds=150
            )

            status_messages = []
            def progress(pct, msg):
                status_messages.append(msg)

            dest, is_new = Downloader.download_track(
                track,
                AudioFormat.FLAC,
                output_dir=Path(tmpdir),
                progress_callback=progress
            )

            self.assertTrue(is_new)
            self.assertIsNotNone(track.stream_resolution)
            self.assertEqual(track.stream_resolution.source, "auto_hq")
            self.assertIn("Motor HQ", track.stream_resolution.display_source)
            print("  ✔ Motor HQ Automático and metadata tracking verified!")


if __name__ == "__main__":
    unittest.main()
