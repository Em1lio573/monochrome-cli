"""
Live download and verification test for Tainy and David Guetta songs.
"""
import os
import sys
from pathlib import Path

# Add cli to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from mutagen.id3 import ID3
from mutagen.flac import FLAC
from mutagen.mp4 import MP4

from monochrome_cli.core.search import SearchEngine
from monochrome_cli.core.downloader import Downloader
from monochrome_cli.types import AudioFormat


def run_artist_tests():
    output_base = Path("/tmp/mono_artist_tests")
    output_base.mkdir(parents=True, exist_ok=True)
    
    test_cases = [
        {
            "query": "Tainy Bad Bunny MOJABI GHOST",
            "format": AudioFormat.MP3_320,
            "artist_label": "Tainy / Bad Bunny",
            "expected_ext": ".mp3"
        },
        {
            "query": "David Guetta Sia Titanium",
            "format": AudioFormat.FLAC,
            "artist_label": "David Guetta (Titanium)",
            "expected_ext": ".flac"
        },
        {
            "query": "David Guetta Bebe Rexha I'm Good Blue",
            "format": AudioFormat.M4A_256,
            "artist_label": "David Guetta (I'm Good)",
            "expected_ext": ".m4a"
        }
    ]

    downloaded_files = []

    for case in test_cases:
        query = case["query"]
        fmt = case["format"]
        label = case["artist_label"]
        print(f"\n==================================================")
        print(f"🔍 Buscando {query} para prueba [{fmt.value.upper()}]...")
        print(f"==================================================")

        res = SearchEngine.search(query, limit=1)
        assert len(res.tracks) > 0, f"No tracks found for {query}"
        track = res.tracks[0]

        print(f"✔ Pista encontrada: {track.artist} - {track.title} (Álbum: {track.album})")
        print(f"  Portada URL: {track.cover_url}")

        print(f"⬇ Descargando en {fmt.display_name}...")
        saved_file = Downloader.download_track(track, audio_format=fmt, output_dir=output_base)
        assert saved_file is not None and saved_file.exists(), f"Failed to download {track.title}"
        assert saved_file.suffix == case["expected_ext"], f"Expected {case[expected_ext]}, got {saved_file.suffix}"

        size_mb = saved_file.stat().st_size / (1024 * 1024)
        print(f"✔ Archivo generado: {saved_file} ({size_mb:.2f} MB)")
        downloaded_files.append((saved_file, track, fmt))

    print(f"\n==================================================")
    print(f"🔬 INSPECIONANDO METADATOS, PORTADAS Y LETRAS")
    print(f"==================================================")

    for file_path, track, fmt in downloaded_files:
        print(f"\n📁 Archivo: {file_path.name}")
        print(f"   Ruta completa: {file_path}")
        print(f"   Tamaño: {file_path.stat().st_size / (1024*1024):.2f} MB")

        ext = file_path.suffix.lower()
        if ext == ".mp3":
            audio = ID3(file_path)
            print(f"   [ID3v2] Título: {audio.get("TIT2")}")
            print(f"   [ID3v2] Artista: {audio.get("TPE1")}")
            print(f"   [ID3v2] Álbum: {audio.get("TALB")}")
            apic = [v for k, v in audio.items() if k.startswith("APIC")]
            if apic:
                print(f"   [Portada HD] Incrustada: {len(apic[0].data)} bytes ({apic[0].mime})")
            uslt = [v for k, v in audio.items() if k.startswith("USLT")]
            if uslt:
                snippet = uslt[0].text[:80].replace("\n", " ")
                print(f"   [Letras ID3] Incrustadas: \"{snippet}...\"")

        elif ext == ".flac":
            audio = FLAC(file_path)
            print(f"   [FLAC] Título: {audio.get("TITLE", [None])[0]}")
            print(f"   [FLAC] Artista: {audio.get("ARTIST", [None])[0]}")
            print(f"   [FLAC] Álbum: {audio.get("ALBUM", [None])[0]}")
            if audio.pictures:
                pic = audio.pictures[0]
                print(f"   [Portada HD] Incrustada: {len(pic.data)} bytes ({pic.mime})")
            if "LYRICS" in audio:
                snippet = audio["LYRICS"][0][:80].replace("\n", " ")
                print(f"   [Letras FLAC] Incrustadas: \"{snippet}...\"")

        elif ext == ".m4a":
            audio = MP4(file_path)
            print(f"   [MP4] Título: {audio.get("©nam", [None])[0]}")
            print(f"   [MP4] Artista: {audio.get("©ART", [None])[0]}")
            print(f"   [MP4] Álbum: {audio.get("©alb", [None])[0]}")
            if "covr" in audio:
                print(f"   [Portada HD] Incrustada: {len(audio["covr"][0])} bytes")
            if "©lyr" in audio:
                snippet = audio["©lyr"][0][:80].replace("\n", " ")
                print(f"   [Letras MP4] Incrustadas: \"{snippet}...\"")

        # Comprobar archivo compañero .lrc
        lrc_file = file_path.with_suffix(".lrc")
        if lrc_file.exists():
            print(f"   [Letras .lrc] Archivo generado: {lrc_file.name} ({lrc_file.stat().st_size} bytes)")
            with open(lrc_file, "r", encoding="utf-8") as f:
                first_lines = [f.readline().strip() for _ in range(2) if f]
                print(f"   [Letras .lrc Muestra] {" | ".join(first_lines)}")

    print(f"\n>>> TODAS LAS PRUEBAS DE DESCARGA E INSPECCIÓN FINALIZARON CON ÉXITO 100% <<<")


if __name__ == "__main__":
    run_artist_tests()
