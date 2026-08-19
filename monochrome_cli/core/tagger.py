"""
Audio metadata tagger using Mutagen for MP3, FLAC, M4A, and OPUS.
Embeds High-Res covers, ID3v2.4 / Vorbis / MP4 atoms, lyrics and tags.
"""
import io
import urllib.request
from pathlib import Path
from typing import Optional

from mutagen.id3 import (
    ID3,
    TIT2,
    TPE1,
    TPE2,
    TALB,
    TRCK,
    TPOS,
    TDRC,
    TCON,
    TSRC,
    USLT,
    APIC,
    ID3NoHeaderError,
)
from mutagen.flac import FLAC, Picture
from mutagen.mp4 import MP4, MP4Cover
from mutagen.oggopus import OggOpus
from mutagen.oggvorbis import OggVorbis

from monochrome_cli.types import TrackMetadata, AudioFormat


def is_png(data: bytes) -> bool:
    return len(data) >= 8 and data[:8] == b"\x89PNG\r\n\x1a\n"


class MetadataTagger:
    @classmethod
    def fetch_cover_bytes(cls, cover_url: str) -> Optional[bytes]:
        if not cover_url:
            return None
        try:
            req = urllib.request.Request(
                cover_url,
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
            )
            with urllib.request.urlopen(req, timeout=10) as res:
                if res.status == 200:
                    return res.read()
        except Exception:
            pass
        return None

    @classmethod
    def apply_metadata(
        cls,
        file_path: Path,
        track: TrackMetadata,
        audio_format: AudioFormat,
        embed_cover: bool = True,
        embed_lyrics: bool = True
    ) -> bool:
        if not file_path.exists():
            return False

        ext = file_path.suffix.lower().lstrip(".")
        cover_bytes = cls.fetch_cover_bytes(track.cover_url) if (embed_cover and track.cover_url) else None

        lyrics_text = None
        if embed_lyrics and track.lyrics:
            lyrics_text = track.lyrics.synced_lyrics or track.lyrics.plain_lyrics

        try:
            if ext == "mp3":
                cls._tag_mp3(file_path, track, cover_bytes, lyrics_text)
            elif ext == "flac":
                cls._tag_flac(file_path, track, cover_bytes, lyrics_text)
            elif ext in ("m4a", "mp4", "aac"):
                cls._tag_m4a(file_path, track, cover_bytes, lyrics_text)
            elif ext == "opus":
                cls._tag_opus(file_path, track, cover_bytes, lyrics_text)
            elif ext == "ogg":
                cls._tag_ogg(file_path, track, cover_bytes, lyrics_text)
            return True
        except Exception as e:
            print(f"[Aviso] No se pudieron incrustar todos los metadatos en {file_path.name}: {e}")
            return False

    @staticmethod
    def _tag_mp3(file_path: Path, track: TrackMetadata, cover_bytes: Optional[bytes], lyrics: Optional[str]):
        try:
            audio = ID3(file_path)
        except ID3NoHeaderError:
            audio = ID3()

        audio.add(TIT2(encoding=3, text=track.title))
        audio.add(TPE1(encoding=3, text=track.artist))
        if track.album_artist or track.artist:
            audio.add(TPE2(encoding=3, text=track.album_artist or track.artist))
        if track.album:
            audio.add(TALB(encoding=3, text=track.album))
        if track.track_number:
            trck_str = f"{track.track_number}/{track.total_tracks}" if track.total_tracks > 1 else str(track.track_number)
            audio.add(TRCK(encoding=3, text=trck_str))
        if track.disc_number:
            tpos_str = f"{track.disc_number}/{track.total_discs}" if track.total_discs > 1 else str(track.disc_number)
            audio.add(TPOS(encoding=3, text=tpos_str))
        if track.year:
            audio.add(TDRC(encoding=3, text=str(track.year)))
        if track.genre:
            audio.add(TCON(encoding=3, text=track.genre))
        if track.isrc:
            audio.add(TSRC(encoding=3, text=track.isrc))

        if lyrics:
            audio.add(USLT(encoding=3, lang="eng", desc="Lyrics", text=lyrics))

        if cover_bytes:
            mime = "image/png" if is_png(cover_bytes) else "image/jpeg"
            audio.add(APIC(
                encoding=3,
                mime=mime,
                type=3,  # Front Cover
                desc="Cover",
                data=cover_bytes
            ))

        audio.save(file_path, v2_version=4)

    @staticmethod
    def _tag_flac(file_path: Path, track: TrackMetadata, cover_bytes: Optional[bytes], lyrics: Optional[str]):
        audio = FLAC(file_path)
        audio["TITLE"] = track.title
        audio["ARTIST"] = track.artist
        if track.album_artist or track.artist:
            audio["ALBUMARTIST"] = track.album_artist or track.artist
        if track.album:
            audio["ALBUM"] = track.album
        if track.track_number:
            audio["TRACKNUMBER"] = str(track.track_number)
        if track.total_tracks:
            audio["TRACKTOTAL"] = str(track.total_tracks)
        if track.disc_number:
            audio["DISCNUMBER"] = str(track.disc_number)
        if track.total_discs:
            audio["DISCTOTAL"] = str(track.total_discs)
        if track.year:
            audio["DATE"] = str(track.year)
        if track.genre:
            audio["GENRE"] = track.genre
        if track.isrc:
            audio["ISRC"] = track.isrc
        if lyrics:
            audio["LYRICS"] = lyrics

        if cover_bytes:
            pic = Picture()
            pic.data = cover_bytes
            pic.type = 3
            pic.mime = "image/png" if is_png(cover_bytes) else "image/jpeg"
            pic.desc = "Cover"
            audio.clear_pictures()
            audio.add_picture(pic)

        audio.save()

    @staticmethod
    def _tag_m4a(file_path: Path, track: TrackMetadata, cover_bytes: Optional[bytes], lyrics: Optional[str]):
        audio = MP4(file_path)
        audio["\xa9nam"] = track.title
        audio["\xa9ART"] = track.artist
        audio["aART"] = track.album_artist or track.artist
        if track.album:
            audio["\xa9alb"] = track.album
        if track.track_number:
            audio["trkn"] = [(track.track_number, track.total_tracks or 0)]
        if track.disc_number:
            audio["disk"] = [(track.disc_number, track.total_discs or 0)]
        if track.year:
            audio["\xa9day"] = str(track.year)
        if track.genre:
            audio["\xa9gen"] = track.genre
        if lyrics:
            audio["\xa9lyr"] = lyrics

        if cover_bytes:
            fmt = MP4Cover.FORMAT_PNG if is_png(cover_bytes) else MP4Cover.FORMAT_JPEG
            audio["covr"] = [MP4Cover(cover_bytes, imageformat=fmt)]

        audio.save()

    @staticmethod
    def _tag_opus(file_path: Path, track: TrackMetadata, cover_bytes: Optional[bytes], lyrics: Optional[str]):
        audio = OggOpus(file_path)
        audio["title"] = track.title
        audio["artist"] = track.artist
        if track.album_artist or track.artist:
            audio["albumartist"] = track.album_artist or track.artist
        if track.album:
            audio["album"] = track.album
        if track.track_number:
            audio["tracknumber"] = str(track.track_number)
        if track.year:
            audio["date"] = str(track.year)
        if track.genre:
            audio["genre"] = track.genre
        if lyrics:
            audio["lyrics"] = lyrics
        audio.save()

    @staticmethod
    def _tag_ogg(file_path: Path, track: TrackMetadata, cover_bytes: Optional[bytes], lyrics: Optional[str]):
        audio = OggVorbis(file_path)
        audio["title"] = track.title
        audio["artist"] = track.artist
        if track.album_artist or track.artist:
            audio["albumartist"] = track.album_artist or track.artist
        if track.album:
            audio["album"] = track.album
        if track.track_number:
            audio["tracknumber"] = str(track.track_number)
        if track.year:
            audio["date"] = str(track.year)
        if track.genre:
            audio["genre"] = track.genre
        if lyrics:
            audio["lyrics"] = lyrics
        audio.save()
