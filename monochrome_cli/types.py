"""
Data types and models for Monochrome CLI.
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Dict, Any


class AudioFormat(str, Enum):
    FLAC = "flac"
    MP3_320 = "mp3_320"
    MP3_256 = "mp3_256"
    MP3_128 = "mp3_128"
    M4A_256 = "m4a_256"
    OPUS_160 = "opus_160"
    OGG = "ogg"

    @classmethod
    def from_string(cls, val: str) -> "AudioFormat":
        val = str(val).lower().replace("-", "_").replace(" ", "_")
        if val in ("flac", "lossless", "hi_res", "hires"):
            return cls.FLAC
        if val in ("mp3_320", "320", "320k", "320kbps", "mp3"):
            return cls.MP3_320
        if val in ("mp3_256", "256", "256k", "256kbps"):
            return cls.MP3_256
        if val in ("mp3_128", "128", "128k", "128kbps"):
            return cls.MP3_128
        if val in ("m4a", "m4a_256", "aac", "aac_256", "m4a_hq"):
            return cls.M4A_256
        if val in ("opus", "opus_160", "160k", "opus_hq"):
            return cls.OPUS_160
        if val in ("ogg", "vorbis"):
            return cls.OGG
        return cls.MP3_320

    @property
    def extension(self) -> str:
        if self in (AudioFormat.MP3_320, AudioFormat.MP3_256, AudioFormat.MP3_128):
            return "mp3"
        if self == AudioFormat.FLAC:
            return "flac"
        if self == AudioFormat.M4A_256:
            return "m4a"
        if self == AudioFormat.OPUS_160:
            return "opus"
        if self == AudioFormat.OGG:
            return "ogg"
        return "mp3"

    @property
    def display_name(self) -> str:
        names = {
            AudioFormat.FLAC: "FLAC (Lossless / Hi-Res Audio)",
            AudioFormat.MP3_320: "MP3 320 kbps (CBR Máxima fidelidad)",
            AudioFormat.MP3_256: "MP3 256 kbps (VBR Alta calidad)",
            AudioFormat.MP3_128: "MP3 128 kbps (Ahorro de espacio)",
            AudioFormat.M4A_256: "M4A / AAC 256 kbps (Apple/HQ)",
            AudioFormat.OPUS_160: "OPUS 160 kbps (Eficiente / HQ)",
            AudioFormat.OGG: "OGG Vorbis",
        }
        return names.get(self, self.value)

    @property
    def ffmpeg_args(self) -> Dict[str, Any]:
        if self == AudioFormat.FLAC:
            return {"codec": "flac", "bitrate": None, "ext": "flac"}
        if self == AudioFormat.MP3_320:
            return {"codec": "libmp3lame", "bitrate": "320k", "ext": "mp3"}
        if self == AudioFormat.MP3_256:
            return {"codec": "libmp3lame", "bitrate": "256k", "ext": "mp3"}
        if self == AudioFormat.MP3_128:
            return {"codec": "libmp3lame", "bitrate": "128k", "ext": "mp3"}
        if self == AudioFormat.M4A_256:
            return {"codec": "aac", "bitrate": "256k", "ext": "m4a"}
        if self == AudioFormat.OPUS_160:
            return {"codec": "libopus", "bitrate": "160k", "ext": "opus"}
        if self == AudioFormat.OGG:
            return {"codec": "libvorbis", "bitrate": "192k", "ext": "ogg"}
        return {"codec": "libmp3lame", "bitrate": "320k", "ext": "mp3"}


@dataclass
class LyricsData:
    plain_lyrics: Optional[str] = None
    synced_lyrics: Optional[str] = None
    instrumental: bool = False
    source: str = "lrclib"


@dataclass
class TrackMetadata:
    title: str
    artist: str
    album: str
    duration_seconds: int = 0
    track_number: int = 1
    total_tracks: int = 1
    disc_number: int = 1
    total_discs: int = 1
    year: Optional[str] = None
    release_date: Optional[str] = None
    genre: Optional[str] = None
    isrc: Optional[str] = None
    album_artist: Optional[str] = None
    cover_url: Optional[str] = None
    explicit: bool = False
    source: str = "tidal"
    source_id: Optional[str] = None
    stream_url: Optional[str] = None
    lyrics: Optional[LyricsData] = None

    @property
    def duration_formatted(self) -> str:
        if not self.duration_seconds:
            return "--:--"
        mins = self.duration_seconds // 60
        secs = self.duration_seconds % 60
        return f"{mins:02d}:{secs:02d}"


@dataclass
class AlbumMetadata:
    title: str
    artist: str
    release_date: Optional[str] = None
    year: Optional[str] = None
    cover_url: Optional[str] = None
    total_tracks: int = 0
    tracks: List[TrackMetadata] = field(default_factory=list)
    source: str = "tidal"
    source_id: Optional[str] = None


@dataclass
class StreamResolution:
    url: str
    source: str  # 'amazon', 'tidal', 'mono', 'deezer', 'youtube'
    quality: str  # 'HI_RES_LOSSLESS', 'LOSSLESS', 'DOLBY_ATMOS', '320k', etc.
    codec: Optional[str] = None
    decryption_key: Optional[str] = None
    key_id: Optional[str] = None
    is_cenc: bool = False
    is_dash: bool = False
    is_fallback: bool = False
    bit_depth: Optional[int] = None
    sample_rate: Optional[int] = None
    provider_name: Optional[str] = None

    @property
    def display_source(self) -> str:
        if self.source == "amazon":
            res = "Amazon Music"
            if self.is_cenc:
                res += " (Lossless CENC Descifrado)"
            return res
        elif self.source == "tidal":
            return "Tidal Hi-Fi (Lossless)"
        elif self.source == "mono" or self.source == "monochrome":
            return "Monochrome CDN (Lossless)"
        elif self.source == "deezer":
            return "Deezer (Lossless Fallback)"
        elif self.source == "youtube":
            return "YouTube Music (Fallback)"
        elif self.source in ("auto_hq", "soundcloud"):
            return "Motor HQ Automático"
        return self.provider_name or self.source.capitalize()


@dataclass
class SearchResult:
    tracks: List[TrackMetadata] = field(default_factory=list)
    albums: List[AlbumMetadata] = field(default_factory=list)
    query: str = ""

