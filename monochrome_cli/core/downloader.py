"""
Audio stream downloader and post-processor using yt-dlp, FFmpeg, and Mutagen.
"""
import os
import shutil
import tempfile
from pathlib import Path
from typing import Callable, Optional, Tuple

import yt_dlp

from monochrome_cli.config import config
from monochrome_cli.core.lyrics import LyricsManager
from monochrome_cli.core.tagger import MetadataTagger
from monochrome_cli.types import AudioFormat, TrackMetadata
from monochrome_cli.utils.template import format_track_path


class Downloader:
    @staticmethod
    def _create_yt_dlp_params(
        temp_dir: Path,
        audio_format: AudioFormat,
        progress_hook: Optional[Callable[[dict], None]] = None
    ) -> dict:
        ffmpeg_info = audio_format.ffmpeg_args
        ext = ffmpeg_info["ext"]
        preferred_codec = ffmpeg_info["codec"]
        bitrate = ffmpeg_info.get("bitrate")

        postprocessors = [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": ext,
        }]
        if bitrate:
            postprocessors[0]["preferredquality"] = bitrate.rstrip("k")

        ydl_opts = {
            "format": "bestaudio/best",
            "outtmpl": str(temp_dir / "%(id)s.%(ext)s"),
            "quiet": True,
            "no_warnings": True,
            "noprogress": True,
            "postprocessors": postprocessors,
            "prefer_ffmpeg": True,
            "extractor_args": {
                "youtube": {
                    "player_client": ["web", "android"]
                }
            },
        }

        if progress_hook:
            ydl_opts["progress_hooks"] = [progress_hook]

        return ydl_opts

    @classmethod
    def download_track(
        cls,
        track: TrackMetadata,
        audio_format: Optional[AudioFormat] = None,
        output_dir: Optional[Path] = None,
        progress_callback: Optional[Callable[[float, str], None]] = None,
        overwrite: bool = False,
        include_lyrics: Optional[bool] = None,
        include_cover: Optional[bool] = None,
    ) -> Tuple[Optional[Path], bool]:
        """
        Downloads a track, converts it, embeds metadata & cover art, and writes .lrc.
        """
        fmt = audio_format or config.default_format
        dest_dir = output_dir or config.download_directory
        final_path = format_track_path(track, dest_dir, fmt, config.folder_template)

        # Duplicate check
        if not overwrite and final_path.exists() and final_path.stat().st_size > 1024:
            if progress_callback:
                progress_callback(100.0, f"Ya existe en disco: {final_path.name}")
            return final_path, False

        # Resolve lyrics & cover flags
        should_embed_cover = config.embed_cover if include_cover is None else include_cover
        should_get_lyrics = (config.embed_lyrics or config.save_lrc_file) if include_lyrics is None else include_lyrics

        # Construct query for highest precision match
        query = f"ytsearch1:{track.artist} - {track.title} audio"
        if track.album and track.album != track.title:
            query = f"ytsearch1:{track.artist} - {track.title} {track.album} audio"

        with tempfile.TemporaryDirectory() as temp_dir_str:
            temp_dir = Path(temp_dir_str)

            def ytdl_hook(d):
                if progress_callback and d.get("status") == "downloading":
                    total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
                    downloaded = d.get("downloaded_bytes", 0)
                    percent = (downloaded / total * 100) if total > 0 else 50.0
                    speed = d.get("_speed_str", "")
                    progress_callback(percent, f"Descargando stream {speed}...")
                elif progress_callback and d.get("status") == "finished":
                    progress_callback(90.0, "Procesando audio y metadatos...")

            opts = cls._create_yt_dlp_params(temp_dir, fmt, ytdl_hook)

            try:
                with yt_dlp.YoutubeDL(opts) as ydl:
                    if progress_callback:
                        progress_callback(10.0, "Buscando mejor stream de audio...")
                    info = ydl.extract_info(query, download=True)
                    if not info or "entries" not in info or len(info["entries"]) == 0:
                        fallback_query = f"ytsearch1:{track.artist} {track.title}"
                        info = ydl.extract_info(fallback_query, download=True)

                # Locate converted file in temp_dir
                temp_files = list(temp_dir.glob(f"*.{fmt.extension}"))
                if not temp_files:
                    temp_files = list(temp_dir.glob("*.*"))

                if not temp_files:
                    raise FileNotFoundError("No se encontró el archivo de audio procesado por FFmpeg")

                source_temp_file = temp_files[0]

                # Move to final path
                final_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(source_temp_file), str(final_path))

                # Fetch and embed lyrics if enabled
                if should_get_lyrics:
                    if progress_callback:
                        progress_callback(95.0, "Obteniendo letras sincronizadas...")
                    lyrics_data = LyricsManager.fetch_lyrics(track)
                    if lyrics_data:
                        track.lyrics = lyrics_data
                        if config.save_lrc_file:
                            LyricsManager.save_lrc_file(lyrics_data, final_path)

                # Tag metadata and cover art
                if progress_callback:
                    progress_callback(98.0, "Incrustando portada HD y metadatos...")
                MetadataTagger.apply_metadata(
                    final_path,
                    track,
                    fmt,
                    embed_cover=should_embed_cover,
                    embed_lyrics=(config.embed_lyrics and should_get_lyrics)
                )

                if progress_callback:
                    progress_callback(100.0, f"Completado: {final_path.name}")

                return final_path, True

            except Exception as e:
                if progress_callback:
                    progress_callback(0.0, f"Error: {e}")
                print(f"[Error] Falló la descarga de {track.title}: {e}")
                return None, False
