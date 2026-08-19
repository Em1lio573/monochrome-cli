"""
Lyrics fetcher and .lrc file manager for Monochrome CLI.
"""
import urllib.request
import urllib.parse
import json
from pathlib import Path
from typing import Optional
from monochrome_cli.types import LyricsData, TrackMetadata


class LyricsManager:
    LRCLIB_API = "https://lrclib.net/api"

    @classmethod
    def fetch_lyrics(cls, track: TrackMetadata) -> Optional[LyricsData]:
        """
        Fetches synced (.lrc) and plain lyrics from LRCLIB.
        """
        try:
            # 1. Try exact match by track_name, artist_name, album_name, duration
            params = {
                "track_name": track.title,
                "artist_name": track.artist,
            }
            if track.album:
                params["album_name"] = track.album
            if track.duration_seconds > 0:
                params["duration"] = str(track.duration_seconds)

            url = f"{cls.LRCLIB_API}/get?{urllib.parse.urlencode(params)}"
            req = urllib.request.Request(url, headers={"User-Agent": "MonochromeCLI/1.0"})

            try:
                with urllib.request.urlopen(req, timeout=6) as response:
                    if response.status == 200:
                        data = json.loads(response.read().decode("utf-8"))
                        return LyricsData(
                            plain_lyrics=data.get("plainLyrics"),
                            synced_lyrics=data.get("syncedLyrics"),
                            instrumental=bool(data.get("instrumental", False)),
                            source="lrclib_exact"
                        )
            except urllib.error.HTTPError as e:
                if e.code != 404:
                    pass

            # 2. Fallback: Search by free-form query
            search_query = f"{track.artist} {track.title}"
            search_url = f"{cls.LRCLIB_API}/search?{urllib.parse.urlencode({'q': search_query})}"
            sreq = urllib.request.Request(search_url, headers={"User-Agent": "MonochromeCLI/1.0"})

            with urllib.request.urlopen(sreq, timeout=6) as sresponse:
                if sresponse.status == 200:
                    results = json.loads(sresponse.read().decode("utf-8"))
                    if isinstance(results, list) and len(results) > 0:
                        # Pick best match
                        best = results[0]
                        return LyricsData(
                            plain_lyrics=best.get("plainLyrics"),
                            synced_lyrics=best.get("syncedLyrics"),
                            instrumental=bool(best.get("instrumental", False)),
                            source="lrclib_search"
                        )
        except Exception:
            pass

        return None

    @classmethod
    def save_lrc_file(cls, lyrics: LyricsData, audio_file_path: Path) -> Optional[Path]:
        """
        Saves a .lrc file alongside the audio file if synced lyrics exist.
        """
        content = lyrics.synced_lyrics or lyrics.plain_lyrics
        if not content:
            return None

        lrc_path = audio_file_path.with_suffix(".lrc")
        try:
            with open(lrc_path, "w", encoding="utf-8") as f:
                f.write(content.strip() + "\n")
            return lrc_path
        except Exception:
            return None
