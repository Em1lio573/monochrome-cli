"""
Configuration management for Monochrome CLI.
"""
import json
from pathlib import Path
from typing import Any, Dict
from monochrome_cli.types import AudioFormat
from monochrome_cli.utils.platform import get_config_dir, get_default_music_dir


class Config:
    DEFAULT_CONFIG = {
        "download_directory": str(get_default_music_dir()),
        "default_format": AudioFormat.FLAC.value,
        "embed_cover": True,
        "cover_resolution": 1280,
        "embed_lyrics": True,
        "save_lrc_file": True,
        "folder_template": "{album_artist}/{album}/{track_number:02d} - {title}",
        "search_limit": 10,
        "tidal_client_id": "txNoH4kkV41MfH25",
        "tidal_client_secret": "dQjy0MinCEvxi1O4UmxvxWnDjt4cgHBPw8ll6nYBk98=",
        "unified_api_base_url": "https://music-api.geeked.wtf",
        "unified_api_token": "amp_29b2lIr4mze4tK-P8QDOxfMZ9anCgJ9_uGTUks3nIyo",
        "deezer_api_base_url": "https://dzr.tabs-vs-spaces.wtf",
        "prefer_lossless_source": True,
        "allow_youtube_fallback": True,
        "notify_fallback_source": True,
    }

    def __init__(self):
        self.config_path = get_config_dir() / "config.json"
        self._data = dict(self.DEFAULT_CONFIG)
        self.load()

    def load(self) -> None:
        if self.config_path.exists():
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                    self._data.update(loaded)
            except Exception as e:
                print(f"[Aviso] No se pudo leer la configuración existente: {e}")
        else:
            self.save()

    def save(self) -> None:
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(self._data, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"[Error] No se pudo guardar la configuración: {e}")

    def get(self, key: str, default: Any = None) -> Any:
        return self._data.get(key, default)

    def set(self, key: str, value: Any) -> None:
        self._data[key] = value
        self.save()

    @property
    def download_directory(self) -> Path:
        p = Path(self.get("download_directory", str(get_default_music_dir()))).expanduser()
        p.mkdir(parents=True, exist_ok=True)
        return p

    @download_directory.setter
    def download_directory(self, val: str) -> None:
        self.set("download_directory", str(val))

    @property
    def default_format(self) -> AudioFormat:
        val = self.get("default_format", AudioFormat.MP3_320.value)
        return AudioFormat.from_string(val)

    @default_format.setter
    def default_format(self, fmt: AudioFormat) -> None:
        self.set("default_format", fmt.value)

    @property
    def embed_cover(self) -> bool:
        return bool(self.get("embed_cover", True))

    @property
    def cover_resolution(self) -> int:
        return int(self.get("cover_resolution", 1280))

    @property
    def embed_lyrics(self) -> bool:
        return bool(self.get("embed_lyrics", True))

    @property
    def save_lrc_file(self) -> bool:
        return bool(self.get("save_lrc_file", True))

    @property
    def folder_template(self) -> str:
        return str(self.get("folder_template", "{album_artist}/{album}/{track_number:02d} - {title}"))

    @property
    def search_limit(self) -> int:
        return int(self.get("search_limit", 10))

    @property
    def unified_api_base_url(self) -> str:
        return str(self.get("unified_api_base_url", "https://music-api.geeked.wtf"))

    @unified_api_base_url.setter
    def unified_api_base_url(self, val: str) -> None:
        self.set("unified_api_base_url", str(val))

    @property
    def unified_api_token(self) -> str:
        return str(self.get("unified_api_token", "amp_29b2lIr4mze4tK-P8QDOxfMZ9anCgJ9_uGTUks3nIyo"))

    @unified_api_token.setter
    def unified_api_token(self, val: str) -> None:
        self.set("unified_api_token", str(val))

    @property
    def deezer_api_base_url(self) -> str:
        return str(self.get("deezer_api_base_url", "https://dzr.tabs-vs-spaces.wtf"))

    @deezer_api_base_url.setter
    def deezer_api_base_url(self, val: str) -> None:
        self.set("deezer_api_base_url", str(val))

    @property
    def prefer_lossless_source(self) -> bool:
        return bool(self.get("prefer_lossless_source", True))

    @prefer_lossless_source.setter
    def prefer_lossless_source(self, val: bool) -> None:
        self.set("prefer_lossless_source", bool(val))

    @property
    def allow_youtube_fallback(self) -> bool:
        return bool(self.get("allow_youtube_fallback", True))

    @allow_youtube_fallback.setter
    def allow_youtube_fallback(self, val: bool) -> None:
        self.set("allow_youtube_fallback", bool(val))

    @property
    def notify_fallback_source(self) -> bool:
        return bool(self.get("notify_fallback_source", True))

    @notify_fallback_source.setter
    def notify_fallback_source(self, val: bool) -> None:
        self.set("notify_fallback_source", bool(val))

    @property
    def turnstile_jwt(self) -> Optional[str]:
        val = self.get("turnstile_jwt", "")
        return str(val).strip() if val else None

    @turnstile_jwt.setter
    def turnstile_jwt(self, val: Optional[str]) -> None:
        self.set("turnstile_jwt", str(val).strip() if val else "")


# Global singleton instance
config = Config()
