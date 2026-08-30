"""
Unified Playback and Lossless Stream Resolver for Monochrome CLI.
Implements the same architecture as Monochrome Web:
- Unified Playback API (music-api.geeked.wtf)
- Amazon Music CENC decryption via FFmpeg -decryption_key
- Tidal / Mono DASH manifests and direct FLAC streams
- Deezer Fallback with ISRC (dzr.tabs-vs-spaces.wtf)
"""
import json
import os
import shutil
import subprocess
import tempfile
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Callable, Dict, Optional, Tuple

from monochrome_cli.config import config
from monochrome_cli.types import AudioFormat, StreamResolution, TrackMetadata


class UnifiedEngine:
    DEFAULT_USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64; rv:128.0) Gecko/20100101 Firefox/128.0"
    DEFAULT_HEADERS = {
        "User-Agent": DEFAULT_USER_AGENT,
        "Accept": "application/json",
        "Origin": "https://monochrome.tf",
        "Referer": "https://monochrome.tf/",
    }

    @classmethod
    def _map_quality(cls, audio_format: AudioFormat) -> str:
        if audio_format == AudioFormat.FLAC:
            return "HI_RES_LOSSLESS"
        elif audio_format in (AudioFormat.MP3_320, AudioFormat.M4A_256):
            return "LOSSLESS"
        return "HIGH"

    @classmethod
    def _map_deezer_format(cls, audio_format: AudioFormat) -> str:
        if audio_format == AudioFormat.FLAC:
            return "FLAC"
        elif audio_format in (AudioFormat.MP3_320, AudioFormat.M4A_256):
            return "MP3_320"
        return "MP3_128"

    @classmethod
    def resolve_stream(
        cls,
        track: TrackMetadata,
        audio_format: AudioFormat
    ) -> Optional[StreamResolution]:
        """
        Attempts to resolve a high-fidelity lossless audio stream
        first from Unified Playback API, then fallback to Deezer with ISRC.
        """
        if not config.prefer_lossless_source:
            return None

        # 1. Try Unified Playback API (Amazon Music HD / Tidal / Mono)
        unified_res = cls._resolve_unified_playback(track, audio_format)
        if unified_res:
            return unified_res

        # 2. Try Deezer Fallback with ISRC
        if track.isrc:
            deezer_res = cls._resolve_deezer_fallback(track.isrc, audio_format)
            if deezer_res:
                return deezer_res

        return None

    @classmethod
    def _resolve_unified_playback(
        cls,
        track: TrackMetadata,
        audio_format: AudioFormat
    ) -> Optional[StreamResolution]:
        base_url = config.unified_api_base_url.rstrip("/")
        token = config.unified_api_token.strip()
        if not base_url or not token:
            return None

        quality = cls._map_quality(audio_format)
        params = {
            "track": track.title,
            "artist": track.artist,
            "quality": quality,
            "intent": "download"
        }
        if track.album:
            params["album"] = track.album
        if track.isrc:
            params["isrc"] = track.isrc.strip().upper()
        if track.duration_seconds > 0:
            params["duration"] = str(round(track.duration_seconds))

        url = f"{base_url}/api/v2/track/?{urllib.parse.urlencode(params)}"
        headers = dict(cls.DEFAULT_HEADERS)
        headers["Authorization"] = f"Bearer {token}"

        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=12) as response:
                if response.status != 200:
                    return None
                data = json.loads(response.read().decode("utf-8"))

            playbacks = data.get("playback", [])
            if not isinstance(playbacks, list) or len(playbacks) == 0:
                return None

            # Find suitable playable audio resource
            for resource in playbacks:
                stream_url = resource.get("url")
                if not stream_url:
                    continue

                source = str(resource.get("source") or data.get("selected_source") or "mono").lower()
                if source == "mono":
                    source = "monochrome"

                decryption_key = resource.get("decryption_key") or resource.get("key")
                key_id = resource.get("key_id") or resource.get("kid")
                mime_type = resource.get("mime_type", "")
                delivery = resource.get("delivery", "direct")
                is_dash = delivery == "dash" or ".mpd" in stream_url or "dash" in mime_type
                is_cenc = bool(source == "amazon" and decryption_key)

                return StreamResolution(
                    url=stream_url,
                    source=source,
                    quality=resource.get("quality", quality),
                    codec=resource.get("codec"),
                    decryption_key=decryption_key,
                    key_id=key_id,
                    is_cenc=is_cenc,
                    is_dash=is_dash,
                    is_fallback=False,
                    bit_depth=resource.get("bit_depth"),
                    sample_rate=resource.get("sample_rate"),
                    provider_name="Unified Playback"
                )
        except Exception:
            return None

        return None

    @classmethod
    def _resolve_deezer_fallback(
        cls,
        isrc: str,
        audio_format: AudioFormat
    ) -> Optional[StreamResolution]:
        base_url = config.deezer_api_base_url.rstrip("/")
        if not base_url or not isrc:
            return None

        fmt = cls._map_deezer_format(audio_format)
        url = f"{base_url}/stream/?isrc={urllib.parse.quote(isrc)}&format={urllib.parse.quote(fmt)}"

        try:
            req = urllib.request.Request(url, headers=cls.DEFAULT_HEADERS, method="HEAD")
            with urllib.request.urlopen(req, timeout=8) as response:
                if response.status not in (200, 206, 302, 307):
                    return None
        except urllib.error.HTTPError as e:
            if e.code not in (405, 501):
                return None
        except Exception:
            return None

        return StreamResolution(
            url=url,
            source="deezer",
            quality=fmt,
            codec="flac" if fmt == "FLAC" else "mp3",
            is_cenc=False,
            is_dash=False,
            is_fallback=False,
            provider_name="Deezer"
        )

    @classmethod
    def download_stream(
        cls,
        resolution: StreamResolution,
        dest_path: Path,
        target_format: AudioFormat,
        progress_callback: Optional[Callable[[float, str], None]] = None
    ) -> bool:
        """
        Downloads and decrypts/transcodes audio directly from the resolved stream.
        """
        with tempfile.TemporaryDirectory() as temp_dir_str:
            temp_dir = Path(temp_dir_str)
            raw_temp_file = temp_dir / f"raw_stream.{target_format.extension}"

            if progress_callback:
                progress_callback(20.0, f"Conectando a {resolution.display_source}...")

            # Scenario 1: Amazon Music CENC Decryption
            if resolution.is_cenc and resolution.decryption_key:
                if progress_callback:
                    progress_callback(40.0, "Descargando stream cifrado CENC...")

                # Download encrypted raw file first
                encrypted_file = temp_dir / "encrypted.mp4"
                if not cls._download_file_with_progress(resolution.url, encrypted_file, progress_callback, 40.0, 75.0):
                    return False

                if progress_callback:
                    progress_callback(80.0, "Descifrando audio Lossless con FFmpeg (-decryption_key)...")

                dest_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Use ffmpeg with decryption_key
                ffmpeg_cmd = [
                    "ffmpeg", "-y", "-loglevel", "error",
                    "-decryption_key", resolution.decryption_key,
                    "-i", str(encrypted_file),
                ]
                if target_format == AudioFormat.FLAC:
                    ffmpeg_cmd.extend(["-c:a", "copy", str(dest_path)])
                else:
                    args = target_format.ffmpeg_args
                    ffmpeg_cmd.extend(["-c:a", args["codec"]])
                    if args.get("bitrate"):
                        ffmpeg_cmd.extend(["-b:a", args["bitrate"]])
                    ffmpeg_cmd.append(str(dest_path))

                result = subprocess.run(ffmpeg_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                if result.returncode != 0:
                    # Fallback transcoding if copy fails due to container format
                    fallback_cmd = [
                        "ffmpeg", "-y", "-loglevel", "error",
                        "-decryption_key", resolution.decryption_key,
                        "-i", str(encrypted_file),
                        "-c:a", "flac" if target_format == AudioFormat.FLAC else target_format.ffmpeg_args["codec"],
                        str(dest_path)
                    ]
                    res_fb = subprocess.run(fallback_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    if res_fb.returncode != 0:
                        return False

                return dest_path.exists() and dest_path.stat().st_size > 1024

            # Scenario 2: MPEG-DASH Stream Manifest
            elif resolution.is_dash:
                if progress_callback:
                    progress_callback(40.0, "Descargando y ensamblando stream DASH...")

                dest_path.parent.mkdir(parents=True, exist_ok=True)
                ffmpeg_cmd = [
                    "ffmpeg", "-y", "-loglevel", "error",
                    "-i", resolution.url,
                ]
                if target_format == AudioFormat.FLAC:
                    ffmpeg_cmd.extend(["-c:a", "flac", str(dest_path)])
                else:
                    args = target_format.ffmpeg_args
                    ffmpeg_cmd.extend(["-c:a", args["codec"]])
                    if args.get("bitrate"):
                        ffmpeg_cmd.extend(["-b:a", args["bitrate"]])
                    ffmpeg_cmd.append(str(dest_path))

                result = subprocess.run(ffmpeg_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                return result.returncode == 0 and dest_path.exists() and dest_path.stat().st_size > 1024

            # Scenario 3: Direct Stream (Deezer FLAC, Tidal direct, Monochrome CDN)
            else:
                if progress_callback:
                    progress_callback(40.0, f"Descargando stream directo desde {resolution.source.upper()}...")

                dest_path.parent.mkdir(parents=True, exist_ok=True)
                if not cls._download_file_with_progress(resolution.url, raw_temp_file, progress_callback, 40.0, 85.0):
                    return False

                if target_format == AudioFormat.FLAC and (resolution.codec == "flac" or resolution.source == "deezer"):
                    shutil.move(str(raw_temp_file), str(dest_path))
                else:
                    if progress_callback:
                        progress_callback(88.0, "Ajustando formato de audio con FFmpeg...")
                    args = target_format.ffmpeg_args
                    ffmpeg_cmd = [
                        "ffmpeg", "-y", "-loglevel", "error",
                        "-i", str(raw_temp_file),
                        "-c:a", args["codec"]
                    ]
                    if args.get("bitrate"):
                        ffmpeg_cmd.extend(["-b:a", args["bitrate"]])
                    ffmpeg_cmd.append(str(dest_path))
                    res = subprocess.run(ffmpeg_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    if res.returncode != 0:
                        shutil.move(str(raw_temp_file), str(dest_path))

                return dest_path.exists() and dest_path.stat().st_size > 1024

    @classmethod
    def _download_file_with_progress(
        cls,
        url: str,
        dest_file: Path,
        progress_callback: Optional[Callable[[float, str], None]],
        start_pct: float,
        end_pct: float
    ) -> bool:
        try:
            req = urllib.request.Request(url, headers=cls.DEFAULT_HEADERS)
            with urllib.request.urlopen(req, timeout=30) as response, open(dest_file, "wb") as out_f:
                total_size = int(response.headers.get("Content-Length", 0))
                downloaded = 0
                chunk_size = 64 * 1024

                while True:
                    chunk = response.read(chunk_size)
                    if not chunk:
                        break
                    out_f.write(chunk)
                    downloaded += len(chunk)
                    if progress_callback and total_size > 0:
                        fraction = downloaded / total_size
                        current_pct = start_pct + fraction * (end_pct - start_pct)
                        speed_mb = downloaded / (1024 * 1024)
                        total_mb = total_size / (1024 * 1024)
                        progress_callback(current_pct, f"Descargando {speed_mb:.1f}/{total_mb:.1f} MB...")

            return dest_file.exists() and dest_file.stat().st_size > 0
        except Exception:
            return False
