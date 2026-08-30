"""
Rich tables rendering for tracks, albums, formats, and settings.
"""
from typing import List
from rich.console import Console
from rich.table import Table
from rich import box
from monochrome_cli.types import TrackMetadata, AlbumMetadata, AudioFormat
from monochrome_cli.config import config

console = Console()


def display_tracks_table(tracks: List[TrackMetadata], title: str = "Resultados de Canciones"):
    table = Table(
        title=f"[bold cyan]{title}[/bold cyan]",
        box=box.ROUNDED,
        header_style="bold magenta",
        title_justify="left",
        expand=True
    )
    table.add_column("#", justify="right", style="bold yellow", width=4)
    table.add_column("Título", style="bold white", min_width=20)
    table.add_column("Artista", style="cyan", min_width=18)
    table.add_column("Álbum", style="dim white", min_width=18)
    table.add_column("Duración", justify="center", style="green", width=10)
    table.add_column("Año", justify="center", style="dim", width=6)
    table.add_column("Calidad", justify="center", style="bold bright_blue", width=10)

    for i, t in enumerate(tracks, 1):
        expl_badge = " [bold red][E][/bold red]" if t.explicit else ""
        table.add_row(
            str(i),
            f"{t.title}{expl_badge}",
            t.artist,
            t.album or "—",
            t.duration_formatted,
            str(t.year or "—"),
            "Lossless" if t.source == "tidal" else "320k"
        )
    console.print(table)


def display_albums_table(albums: List[AlbumMetadata], title: str = "Resultados de Álbumes"):
    if not albums:
        return
    table = Table(
        title=f"[bold yellow]{title}[/bold yellow]",
        box=box.ROUNDED,
        header_style="bold magenta",
        title_justify="left",
        expand=True
    )
    table.add_column("Álbum #", justify="right", style="bold yellow", width=8)
    table.add_column("Título del Álbum", style="bold white", min_width=25)
    table.add_column("Artista", style="cyan", min_width=20)
    table.add_column("Pistas", justify="center", style="green", width=8)
    table.add_column("Año", justify="center", style="dim", width=6)

    for i, a in enumerate(albums, 1):
        table.add_row(
            f"A{i}",
            a.title,
            a.artist,
            str(a.total_tracks or "—"),
            str(a.year or "—")
        )
    console.print(table)


def display_formats_table():
    table = Table(
        title="[bold green]Seleccionar Formato de Audio[/bold green]",
        box=box.ROUNDED,
        header_style="bold magenta",
        title_justify="left"
    )
    table.add_column("#", justify="right", style="bold yellow", width=4)
    table.add_column("Formato", style="bold white", width=15)
    table.add_column("Descripción", style="cyan", width=38)
    table.add_column("Activo", justify="center", style="bold green", width=8)

    formats = [
        (1, AudioFormat.FLAC, "Lossless / Hi-Res Audio (Sin pérdida de calidad)"),
        (2, AudioFormat.MP3_320, "MP3 320 kbps (Máxima compatibilidad y calidad MP3)"),
        (3, AudioFormat.MP3_256, "MP3 256 kbps (VBR Alta fidelidad)"),
        (4, AudioFormat.M4A_256, "M4A / AAC 256 kbps (HQ formato Apple/AAC)"),
        (5, AudioFormat.OPUS_160, "OPUS 160 kbps (Codec ultra-eficiente HQ)"),
        (6, AudioFormat.MP3_128, "MP3 128 kbps (Ahorro máximo de espacio)"),
    ]

    current_fmt = config.default_format
    for num, fmt, desc in formats:
        is_active = "✓" if fmt == current_fmt else ""
        table.add_row(str(num), fmt.value.upper(), desc, is_active)

    console.print(table)


def display_settings_table():
    table = Table(
        title="[bold cyan]Configuración Actual de Monochrome CLI[/bold cyan]",
        box=box.ROUNDED,
        header_style="bold magenta",
        title_justify="left"
    )
    table.add_column("Opción", style="bold white", width=25)
    table.add_column("Valor Actual", style="yellow", min_width=35)
    table.add_column("Descripción", style="dim", min_width=30)

    table.add_row("Directorio de Descargas", str(config.download_directory), "Carpeta donde se guardará la música")
    table.add_row("Formato por Defecto", config.default_format.display_name, "Calidad y extensión de audio")
    table.add_row("Motor Lossless Nativo", "Activado (Amazon/Tidal/Deezer)" if config.prefer_lossless_source else "Desactivado", "Descarga Lossless de alta fidelidad")
    table.add_row("Fallback de YouTube", "Activado" if config.allow_youtube_fallback else "Desactivado", "Descarga alternativa si no hay Lossless")
    table.add_row("Incrustar Portadas HD", "Sí" if config.embed_cover else "No", "Guarda la carátula en el archivo")
    table.add_row("Resolución de Portada", f"{config.cover_resolution}x{config.cover_resolution} px", "Tamaño de imagen álbum")
    table.add_row("Incrustar Letras", "Sí" if config.embed_lyrics else "No", "Etiqueta ID3 de letras sincronizadas")
    table.add_row("Guardar archivo .lrc", "Sí" if config.save_lrc_file else "No", "Crea archivo de letras para reproductores")
    table.add_row("Plantilla de Carpetas", config.folder_template, "Estructura de guardado")

    console.print(table)
