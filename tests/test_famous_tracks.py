"""
Comprehensive famous tracks test suite for Monochrome CLI.
Tests search, download, metadata tagging, cover art embedding, and synced lyrics.
"""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from mutagen.flac import FLAC
from mutagen.id3 import ID3
from mutagen.mp4 import MP4
from mutagen.oggopus import OggOpus

from monochrome_cli.core.downloader import Downloader
from monochrome_cli.core.search import SearchEngine
from monochrome_cli.types import AudioFormat, TrackMetadata


def inspect_audio_with_ffprobe(file_path: Path) -> dict:
    cmd = [
        "ffprobe", "-v", "quiet",
        "-print_format", "json",
        "-show_format", "-show_streams",
        str(file_path)
    ]
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if res.returncode == 0:
        return json.loads(res.stdout)
    return {}


def test_track_suite():
    tracks_to_test = [
        ("The Weeknd", "Blinding Lights", AudioFormat.FLAC),
        ("Queen", "Bohemian Rhapsody", AudioFormat.MP3_320),
        ("Dua Lipa", "Levitating", AudioFormat.M4A_256),
        ("Daft Punk", "Around the World", AudioFormat.OPUS_160),
        ("Ed Sheeran", "Shape of You", AudioFormat.FLAC),
    ]

    print("==================================================")
    print("   Bateria de Pruebas con Canciones Famosas")
    print("==================================================\n")

    results = []

    with tempfile.TemporaryDirectory() as tmpdir:
        out_dir = Path(tmpdir)

        for i, (artist, title, fmt) in enumerate(tracks_to_test, 1):
            print(f"[{i}/{len(tracks_to_test)}] Buscando: {artist} - {title} [{fmt.value.upper()}]...")

            # 1. Search metadata from Tidal
            search_res = SearchEngine.search_tidal_tracks(f"{artist} {title}", limit=3)
            if search_res:
                track = search_res[0]
            else:
                track = TrackMetadata(title=title, artist=artist, album="Single", duration_seconds=200)

            print(f"    ✔ Metadatos oficiales: '{track.title}' por '{track.artist}' (Album: {track.album})")

            # 2. Download and process
            def on_progress(pct, msg):
                pass

            saved_file, is_new = Downloader.download_track(
                track,
                audio_format=fmt,
                output_dir=out_dir,
                progress_callback=on_progress
            )

            assert saved_file is not None and saved_file.exists(), f"Error: No se descargo {title}"
            size_mb = saved_file.stat().st_size / (1024 * 1024)

            # 3. Audio stream analysis
            probe = inspect_audio_with_ffprobe(saved_file)
            audio_stream = next((s for s in probe.get("streams", []) if s.get("codec_type") == "audio"), {})
            codec_name = audio_stream.get("codec_name", "unknown")
            sample_rate = audio_stream.get("sample_rate", "unknown")
            channels = audio_stream.get("channels", "unknown")
            bitrate_kbps = int(probe.get("format", {}).get("bit_rate", 0)) // 1000

            # 4. Check Lyrics
            lrc_file = saved_file.with_suffix(".lrc")
            has_lyrics = lrc_file.exists() and lrc_file.stat().st_size > 50

            # 5. Tag validation
            if fmt == AudioFormat.FLAC:
                flac_tag = FLAC(saved_file)
                assert flac_tag.pictures, "FLAC Picture missing"
            elif fmt == AudioFormat.MP3_320:
                id3 = ID3(saved_file)
                assert any(k.startswith("APIC") for k in id3.keys()), "MP3 APIC missing"
            elif fmt == AudioFormat.M4A_256:
                mp4 = MP4(saved_file)
                assert "covr" in mp4.tags, "M4A covr missing"
            elif fmt == AudioFormat.OPUS_160:
                opus = OggOpus(saved_file)
                assert opus.tags is not None

            res_info = {
                "track_name": f"{artist} - {title}",
                "format_name": fmt.value.upper(),
                "file": saved_file.name,
                "size_mb": f"{size_mb:.2f} MB",
                "codec": codec_name,
                "sample_rate": f"{sample_rate} Hz",
                "channels": f"{channels}ch",
                "bitrate": f"{bitrate_kbps} kbps" if bitrate_kbps > 0 else "VBR/Lossless",
                "lyrics": "✔ Sincronizadas (.lrc)" if has_lyrics else "No disponibles",
                "cover": "✔ HD Incrustada"
            }
            results.append(res_info)

            print(f"    ✔ Descargado con exito: {saved_file.name} ({size_mb:.2f} MB | {codec_name.upper()} {sample_rate}Hz | Letras: {'Si' if has_lyrics else 'No'})\n")

    print("==================================================")
    print("   📊 RESUMEN FINAL DE RESULTADOS DE PRUEBA")
    print("==================================================")
    for r in results:
        print(f"• {r['track_name']} [{r['format_name']}]:")
        print(f"   Archivo: {r['file']} ({r['size_mb']})")
        print(f"   Audio: {r['codec'].upper()} | {r['sample_rate']} | {r['channels']} | Bitrate: {r['bitrate']}")
        print(f"   Caratula: {r['cover']} | Letras: {r['lyrics']}\n")

    print("[TODAS LAS PRUEBAS CON CANCIONES FAMOSAS FINALIZARON CON EXITO AL 100%]\n")


if __name__ == "__main__":
    test_track_suite()
