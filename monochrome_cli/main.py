"""
Main entry point and Interactive TUI for Monochrome CLI.
"""
import argparse
import sys
from pathlib import Path
from typing import List, Optional

from rich.console import Console
from rich.prompt import Prompt

from monochrome_cli.config import config
from monochrome_cli.core.downloader import Downloader
from monochrome_cli.core.search import SearchEngine
from monochrome_cli.types import AudioFormat, TrackMetadata
from monochrome_cli.ui.banner import print_banner
from monochrome_cli.ui.tables import (
    display_albums_table,
    display_formats_table,
    display_settings_table,
    display_tracks_table,
)

console = Console()


def download_single_track(
    track: TrackMetadata,
    audio_format: Optional[AudioFormat] = None,
    output_dir: Optional[Path] = None,
    overwrite: bool = False,
    include_lyrics: Optional[bool] = None,
):
    fmt = audio_format or config.default_format
    lyrics_active = config.embed_lyrics if include_lyrics is None else include_lyrics
    lyrics_str = "Con Letras (.lrc)" if lyrics_active else "Sin Letras"
    console.print(f"\n[bold green]⬇ Iniciando descarga:[/bold green] [white]{track.artist} - {track.title}[/white] [{fmt.value.upper()} | {lyrics_str}]")
    
    with console.status("[bold cyan]Procesando stream y metadatos...", spinner="dots") as status:
        def update_status(pct: float, msg: str):
            status.update(f"[bold cyan]{msg} ({pct:.0f}%)[/bold cyan]")
        
        saved_file, is_new = Downloader.download_track(
            track,
            fmt,
            output_dir=output_dir,
            progress_callback=update_status,
            overwrite=overwrite,
            include_lyrics=include_lyrics
        )
    
    if saved_file:
        if is_new:
            res = getattr(track, "stream_resolution", None)
            if res:
                console.print(f"[bold green]✔ Fuente de Audio:[/bold green] [bold cyan]{res.display_source}[/bold cyan]")
            console.print(f"[bold green]✔ Guardado con éxito en:[/bold green] [yellow]{saved_file}[/yellow]\n")
        else:
            console.print(f"[bold yellow]⚡ Ya descargada (Omitida para evitar duplicados):[/bold yellow] [dim]{saved_file}[/dim]\n")
    else:
        console.print(f"[bold red]✗ No se pudo completar la descarga de {track.title}[/bold red]\n")


def download_batch_tracks(
    tracks: List[TrackMetadata],
    audio_format: Optional[AudioFormat] = None,
    output_dir: Optional[Path] = None,
    overwrite: bool = False,
    include_lyrics: Optional[bool] = None,
):
    fmt = audio_format or config.default_format
    total = len(tracks)
    lyrics_active = config.embed_lyrics if include_lyrics is None else include_lyrics
    lyrics_str = "Con Letras (.lrc)" if lyrics_active else "Sin Letras"
    console.print(f"\n[bold cyan]📦 Descargando lote de {total} canciones en formato {fmt.value.upper()} [{lyrics_str}]...[/bold cyan]\n")

    new_count = 0
    skipped_count = 0

    for i, track in enumerate(tracks, 1):
        console.print(f"[bold yellow][{i}/{total}][/bold yellow] [white]{track.artist} - {track.title}[/white]")
        with console.status(f"[bold cyan]Descargando [{i}/{total}]...", spinner="dots") as status:
            def update_status(pct: float, msg: str):
                status.update(f"[bold cyan]{msg} ({pct:.0f}%)[/bold cyan]")
            saved_file, is_new = Downloader.download_track(
                track,
                fmt,
                output_dir=output_dir,
                progress_callback=update_status,
                overwrite=overwrite,
                include_lyrics=include_lyrics
            )
        
        if saved_file:
            res = getattr(track, "stream_resolution", None)
            if is_new:
                new_count += 1
                if res:
                    console.print(f"  [cyan]✔ [{res.display_source}][/cyan] [green]Descargado:[/green] [dim]{saved_file.name}[/dim]")
                else:
                    console.print(f"  [green]✔ Descargado:[/green] [dim]{saved_file.name}[/dim]")
            else:
                skipped_count += 1
                console.print(f"  [yellow]⚡ Ya existía (Omitido):[/yellow] [dim]{saved_file.name}[/dim]")
        else:
            console.print(f"  [red]✗ Error al descargar pista {i}[/red]")
    
    console.print(f"\n[bold green]✔ ¡Lote finalizado! Nuevas: {new_count} | Omitidas: {skipped_count}[/bold green]\n")


def select_format_menu(prompt_title: str = "Selecciona Formato") -> AudioFormat:
    display_formats_table()
    choice = Prompt.ask(f"[bold yellow]{prompt_title} (1-6)[/bold yellow]", choices=["1", "2", "3", "4", "5", "6"], default="1")
    mapping = {
        "1": AudioFormat.FLAC,
        "2": AudioFormat.MP3_320,
        "3": AudioFormat.MP3_256,
        "4": AudioFormat.M4A_256,
        "5": AudioFormat.OPUS_160,
        "6": AudioFormat.MP3_128,
    }
    return mapping.get(choice, AudioFormat.MP3_320)


def change_format_interactive():
    selected_fmt = select_format_menu("Elige el nuevo formato por defecto")
    config.default_format = selected_fmt
    console.print(f"[bold green]✔ Formato predeterminado establecido a: {config.default_format.display_name}[/bold green]\n")


def configure_settings_interactive():
    while True:
        display_settings_table()
        console.print("[bold cyan]Menú de Configuración y Preferencias:[/bold cyan]")
        console.print("  [yellow]1[/yellow] - Cambiar Carpeta de Descargas Predeterminada")
        console.print("  [yellow]2[/yellow] - Cambiar Formato y Calidad de Audio Predeterminada")
        console.print("  [yellow]3[/yellow] - Activar / Desactivar Letras Sincronizadas (.lrc e incrustadas)")
        console.print("  [yellow]4[/yellow] - Activar / Desactivar Incrustación de Portadas HD")
        console.print("  [yellow]5[/yellow] - Cambiar Resolución de Portada (1280x1280, 1400x1400, 640x640)")
        console.print("  [yellow]6[/yellow] - Cambiar Plantilla de Carpetas y Nombres")
        console.print("  [yellow]8[/yellow] - Activar / Desactivar Motor Lossless Nativo (Amazon/Tidal/Deezer)")
        console.print("  [yellow]9[/yellow] - Activar / Desactivar Fallback a YouTube Music")
        console.print("  [yellow]10[/yellow] - Configurar Token de Amazon Music Ultra HD (Opcional)")
        console.print("  [yellow]7[/yellow] - Restaurar Valores de Fábrica")
        console.print("  [yellow]q[/yellow] - Volver al Menú Principal\n")

        ans = Prompt.ask("[bold yellow]Selecciona una opción (1-10 o q)[/bold yellow]", default="q").strip()
        if ans == "1":
            new_dir = Prompt.ask("Nueva ruta de descargas", default=str(config.download_directory))
            config.download_directory = new_dir
            console.print(f"[bold green]✔ Carpeta predeterminada: {config.download_directory}[/bold green]\n")
        elif ans == "2":
            change_format_interactive()
        elif ans == "3":
            new_state = not config.embed_lyrics
            config.set("embed_lyrics", new_state)
            config.set("save_lrc_file", new_state)
            status_text = "ACTIVADA (Guardará archivo .lrc e incrustará en audio)" if new_state else "DESACTIVADA"
            console.print(f"[bold green]✔ Descarga de Letras Sincronizadas: {status_text}[/bold green]\n")
        elif ans == "4":
            new_state = not config.embed_cover
            config.set("embed_cover", new_state)
            status_text = "ACTIVADO" if new_state else "DESACTIVADO"
            console.print(f"[bold green]✔ Incrustar portadas HD: {status_text}[/bold green]\n")
        elif ans == "5":
            res_choice = Prompt.ask("Resolución de carátula", choices=["640", "1280", "1400"], default="1280")
            config.set("cover_resolution", int(res_choice))
            console.print(f"[bold green]✔ Resolución de portada establecida a: {config.cover_resolution}x{config.cover_resolution} px[/bold green]\n")
        elif ans == "6":
            console.print("[dim]Variables: {album_artist}, {artist}, {album}, {title}, {year}, {track_number:02d}[/dim]")
            new_tmpl = Prompt.ask("Nueva plantilla", default=config.folder_template)
            config.set("folder_template", new_tmpl)
            console.print(f"[bold green]✔ Plantilla actualizada: {config.folder_template}[/bold green]\n")
        elif ans == "8":
            new_state = not config.prefer_lossless_source
            config.prefer_lossless_source = new_state
            status_text = "ACTIVADO (Priorizará Amazon HD / Tidal / Deezer)" if new_state else "DESACTIVADO (Sólo YouTube)"
            console.print(f"[bold green]✔ Motor Lossless Nativo: {status_text}[/bold green]\n")
        elif ans == "9":
            new_state = not config.allow_youtube_fallback
            config.allow_youtube_fallback = new_state
            status_text = "ACTIVADO (Descargará de YouTube si no hay Lossless)" if new_state else "DESACTIVADO (Fallará si no hay Lossless)"
            console.print(f"[bold green]✔ Fallback a YouTube: {status_text}[/bold green]\n")
        elif ans == "10":
            console.print("\n[dim]Token Turnstile JWT de Monochrome Web (monochrome.tf -> localStorage.unified_turnstile_jwt)[/dim]")
            token_input = Prompt.ask("Pega tu Token Turnstile (o presiona Enter para limpiar)", default=config.turnstile_jwt or "")
            config.turnstile_jwt = token_input.strip() or None
            if config.turnstile_jwt:
                console.print("[bold green]✔ Token de Amazon Music Ultra HD configurado.[/bold green]\n")
            else:
                console.print("[yellow]Token eliminado. Se usarán las fuentes de alta calidad por defecto.[/yellow]\n")
        elif ans == "7":
            confirm = Prompt.ask("[bold red]¿Restaurar toda la configuración por defecto? (s/n)[/bold red]", default="n")
            if confirm.lower() in ("s", "si", "y", "yes"):
                for k, v in config.DEFAULT_CONFIG.items():
                    config.set(k, v)
                console.print("[bold green]✔ Configuración restaurada a valores de fábrica.[/bold green]\n")
        elif ans.lower() in ("q", "quit", "exit", "volver"):
            break



def ask_download_customization() -> tuple:
    """
    Allows customizing format and lyrics for a specific download on-the-fly.
    """
    lyrics_status = "Sí" if config.embed_lyrics else "No"
    console.print(f"\n[bold cyan]Opciones de Descarga Actuales:[/bold cyan] Formato=[yellow]{config.default_format.display_name}[/yellow] | Letras=[yellow]{lyrics_status}[/yellow]")
    custom_ans = Prompt.ask(
        "[bold yellow]¿Descargar con opciones actuales [Enter] o [c]ustomizar formato/letras?[/bold yellow]",
        default="d"
    ).strip().lower()

    if custom_ans == "c":
        chosen_fmt = select_format_menu("Elige el formato para esta descarga")
        lyrics_choice = Prompt.ask("¿Descargar letras sincronizadas (.lrc)? (s/n)", default="s").lower() in ("s", "si", "y", "yes")
        make_default = Prompt.ask("¿Guardar estas opciones como tus nuevas opciones predeterminadas? (s/n)", default="n").lower() in ("s", "si", "y", "yes")
        if make_default:
            config.default_format = chosen_fmt
            config.set("embed_lyrics", lyrics_choice)
            config.set("save_lrc_file", lyrics_choice)
            console.print("[bold green]✔ ¡Nuevos valores guardados como predeterminados![/bold green]")
        return chosen_fmt, lyrics_choice
    
    return config.default_format, config.embed_lyrics


def interactive_search_loop():
    print_banner()

    while True:
        try:
            query = Prompt.ask("\n[bold cyan]🔍 Buscar canción / álbum / artista (o 'config' para ajustes, 'fmt' para formato, 'q' para salir)[/bold cyan]").strip()
            
            if not query or query.lower() in ("q", "quit", "exit"):
                console.print("[dim]¡Hasta luego![/dim]")
                break

            if query.lower() in ("fmt", "format", "formato"):
                change_format_interactive()
                continue

            if query.lower() in ("config", "settings", "ajustes", "opciones"):
                configure_settings_interactive()
                continue

            with console.status(f"[bold cyan]Buscando '{query}' en catálogo Hi-Res...", spinner="dots"):
                res = SearchEngine.search(query)

            if not res.tracks and not res.albums:
                console.print("[bold red]No se encontraron resultados.[/bold red] Intenta con otro término.")
                continue

            # Display tracks and albums
            if res.tracks:
                display_tracks_table(res.tracks, title=f"Resultados para '{query}'")
            if res.albums:
                display_albums_table(res.albums, title=f"Álbumes para '{query}'")

            # User Selection Prompt
            while True:
                prompt_text = "[bold yellow]Selecciona # (1-" + str(len(res.tracks)) + "), 'all', rango (ej: 1-3), Álbum (A1) o 's' para buscar de nuevo[/bold yellow]"
                selection = Prompt.ask(prompt_text, default="1").strip()

                if selection.lower() in ("s", "search", "n"):
                    break
                if selection.lower() in ("q", "quit", "exit"):
                    return

                if selection.lower() == "all" and res.tracks:
                    fmt, lyr = ask_download_customization()
                    download_batch_tracks(res.tracks, audio_format=fmt, include_lyrics=lyr)
                    break

                # Check for Album selection (e.g. A1, A2)
                if selection.upper().startswith("A") and selection[1:].isdigit():
                    idx = int(selection[1:]) - 1
                    if 0 <= idx < len(res.albums):
                        album = res.albums[idx]
                        console.print(f"\n[bold cyan]Cargando pistas del álbum '{album.title}' - {album.artist}...[/bold cyan]")
                        with console.status("[bold cyan]Obteniendo lista de canciones del álbum...", spinner="dots"):
                            album_tracks = SearchEngine.get_album_tracks(album.source_id)
                        if album_tracks:
                            display_tracks_table(album_tracks, title=f"Álbum: {album.title} ({len(album_tracks)} pistas)")
                            confirm = Prompt.ask("[bold yellow]¿Descargar álbum completo? (s/n)[/bold yellow]", default="s")
                            if confirm.lower() in ("s", "y", "si", "yes"):
                                fmt, lyr = ask_download_customization()
                                download_batch_tracks(album_tracks, audio_format=fmt, include_lyrics=lyr)
                        else:
                            console.print("[red]No se pudieron cargar las pistas de este álbum.[/red]")
                    else:
                        console.print("[red]Número de álbum inválido.[/red]")
                    break

                # Check for range selection (e.g. 1-3)
                if "-" in selection:
                    try:
                        start_str, end_str = selection.split("-", 1)
                        start, end = int(start_str.strip()), int(end_str.strip())
                        selected_tracks = [res.tracks[i - 1] for i in range(start, end + 1) if 1 <= i <= len(res.tracks)]
                        if selected_tracks:
                            fmt, lyr = ask_download_customization()
                            download_batch_tracks(selected_tracks, audio_format=fmt, include_lyrics=lyr)
                            break
                    except Exception:
                        console.print("[red]Rango inválido. Usa formato como 1-3.[/red]")
                        continue

                # Check for comma-separated list (e.g. 1, 3, 5)
                if "," in selection:
                    try:
                        indices = [int(x.strip()) for x in selection.split(",") if x.strip().isdigit()]
                        selected_tracks = [res.tracks[i - 1] for i in indices if 1 <= i <= len(res.tracks)]
                        if selected_tracks:
                            fmt, lyr = ask_download_customization()
                            download_batch_tracks(selected_tracks, audio_format=fmt, include_lyrics=lyr)
                            break
                    except Exception:
                        console.print("[red]Selección inválida.[/red]")
                        continue

                # Single track number
                if selection.isdigit():
                    idx = int(selection) - 1
                    if 0 <= idx < len(res.tracks):
                        fmt, lyr = ask_download_customization()
                        download_single_track(res.tracks[idx], audio_format=fmt, include_lyrics=lyr)
                        break
                    else:
                        console.print(f"[red]Número fuera de rango (1-{len(res.tracks)}).[/red]")
                else:
                    console.print("[red]Opción no reconocida.[/red]")

        except KeyboardInterrupt:
            console.print("\n[dim]Saliendo...[/dim]")
            break
        except Exception as e:
            console.print(f"[bold red]Ocurrió un error inesperado:[/bold red] {e}")


def cli_entrypoint():
    parser = argparse.ArgumentParser(
        prog="monochrome",
        description="Monochrome CLI: Buscador y descargador de música Hi-Res para Termux y Linux."
    )
    parser.add_argument("query", nargs="?", help="Término de búsqueda, título o enlace")
    parser.add_argument("-d", "--download", action="store_true", help="Descargar automáticamente el primer resultado")
    parser.add_argument("-f", "--format", help="Formato de audio: flac, mp3_320, mp3_256, m4a, opus, mp3_128")
    parser.add_argument("-o", "--output", help="Carpeta de destino de las descargas")
    parser.add_argument("-a", "--album", action="store_true", help="Buscar y descargar álbum completo")
    parser.add_argument("-w", "--overwrite", "--force", action="store_true", help="Sobrescribir si ya existe (por defecto omite duplicados)")
    parser.add_argument("--lyrics", dest="lyrics", action="store_true", default=None, help="Descargar con letras sincronizadas (.lrc)")
    parser.add_argument("--no-lyrics", dest="lyrics", action="store_false", help="Descargar sin letras sincronizadas")
    
    # Persistent defaults commands
    parser.add_argument("--set-default-format", help="Establecer formato predeterminado permanente (flac, mp3_320, m4a, opus)")
    parser.add_argument("--set-default-lyrics", choices=["true", "false"], help="Establecer si siempre descargar letras por defecto (true/false)")
    parser.add_argument("--set-default-output", help="Establecer carpeta de descargas predeterminada permanente")
    parser.add_argument("--jwt", "--auth", dest="set_jwt", type=str, help="Configurar opcionalmente Token Turnstile para Amazon Music Ultra HD")
    parser.add_argument("--config", action="store_true", help="Abrir menú de configuración interactivo")

    args = parser.parse_args()

    # Handle persistent settings changes via CLI flags
    if args.set_jwt is not None:
        config.turnstile_jwt = args.set_jwt.strip() or None
        if config.turnstile_jwt:
            console.print("[bold green]✔ Token de Amazon Music Ultra HD guardado con éxito.[/bold green]")
        else:
            console.print("[yellow]Token de Amazon Music eliminado.[/yellow]")
        return
    if args.set_default_format:
        config.default_format = AudioFormat.from_string(args.set_default_format)
        console.print(f"[bold green]✔ Formato predeterminado guardado:[/bold green] {config.default_format.display_name}")
        return

    if args.set_default_lyrics:
        val = args.set_default_lyrics.lower() == "true"
        config.set("embed_lyrics", val)
        config.set("save_lrc_file", val)
        console.print(f"[bold green]✔ Descarga de letras predeterminada guardada:[/bold green] {'Activada' if val else 'Desactivada'}")
        return

    if args.set_default_output:
        config.download_directory = args.set_default_output
        console.print(f"[bold green]✔ Directorio de descargas predeterminado guardado:[/bold green] {config.download_directory}")
        return

    if args.config:
        configure_settings_interactive()
        return

    # Temporary run overrides
    run_fmt = AudioFormat.from_string(args.format) if args.format else None
    run_out = Path(args.output).expanduser() if args.output else None
    run_lyrics = args.lyrics

    if args.query:
        query = args.query.strip()
        console.print(f"[bold cyan]Buscando '{query}'...[/bold cyan]")
        res = SearchEngine.search(query)

        if not res.tracks and not res.albums:
            console.print("[bold red]No se encontraron resultados.[/bold red]")
            sys.exit(1)

        if args.album and res.albums:
            album = res.albums[0]
            console.print(f"[bold green]Descargando álbum: {album.title} - {album.artist}[/bold green]")
            tracks = SearchEngine.get_album_tracks(album.source_id)
            if tracks:
                download_batch_tracks(tracks, audio_format=run_fmt, output_dir=run_out, overwrite=args.overwrite, include_lyrics=run_lyrics)
            return

        if args.download and res.tracks:
            download_single_track(res.tracks[0], audio_format=run_fmt, output_dir=run_out, overwrite=args.overwrite, include_lyrics=run_lyrics)
            return

        # Interactive display for CLI query
        display_tracks_table(res.tracks, title=f"Resultados para '{query}'")
        if res.albums:
            display_albums_table(res.albums, title=f"Álbumes para '{query}'")

        choice = Prompt.ask("[bold yellow]Selecciona # para descargar (o 'all')[/bold yellow]", default="1")
        if choice.lower() == "all":
            fmt, lyr = ask_download_customization()
            download_batch_tracks(tracks=res.tracks, audio_format=fmt, output_dir=run_out, overwrite=args.overwrite, include_lyrics=lyr)
        elif choice.isdigit() and 1 <= int(choice) <= len(res.tracks):
            fmt, lyr = ask_download_customization()
            download_single_track(res.tracks[int(choice) - 1], audio_format=fmt, output_dir=run_out, overwrite=args.overwrite, include_lyrics=lyr)
        return

    # Default: Start full interactive TUI
    interactive_search_loop()


if __name__ == "__main__":
    cli_entrypoint()
