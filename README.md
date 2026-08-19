# 🎵 Monochrome CLI (Terminal & Termux)

<p align="center">
  <strong>Versión de terminal (CLI / TUI) optimizada para Termux (Android), Linux y macOS.</strong><br>
  Inspirada en el proyecto original <a href="https://github.com/monochrome-music/monochrome">Monochrome</a>.
</p>

---

## 🌟 Características Principales

- 🔍 **Búsqueda Hi-Res:** Catálogo amplio y preciso impulsado por Tidal y Deezer.
- 🎛️ **Formatos y Calidades Seleccionables:**
  - **FLAC:** Lossless / Hi-Res Audio (16/24-bit sin pérdida).
  - **MP3 320k:** Máxima fidelidad en formato MP3 (CBR).
  - **MP3 256k / 128k:** VBR de alta calidad o ahorro de espacio.
  - **M4A / AAC:** Estándar de alta fidelidad Apple / AAC (256 kbps).
  - **OPUS:** Codec de compresión ultra-eficiente de alta definición (160 kbps).
- 🖼️ **Carátulas en HD (1280x1280):** Incrustadas directamente en los metadatos de los archivos (ID3v2.4 / Vorbis Picture block / MP4 covr atom).
- 🎤 **Letras Sincronizadas (.lrc):** Descarga de letras con marcas de tiempo milimétricas e incrustación en etiquetas de audio.
- 🛡️ **Sistema Antiduplicados:** Detección instantánea de canciones ya descargadas para ahorrar ancho de banda y espacio.
- 📦 **Descargas por Lote:** Descarga canciones individuales, selecciones múltiples (`1-5`, `1,3,6`), o álbumes enteros ordenados por pista.
- ⚙️ **Preferencias Fijas:** Menú interactivo y comandos CLI para guardar tus ajustes favoritos por defecto.

---

## 📱 Instalación en Termux (Android)

### 1. Instalador Automático de 1 Comando
Abre **Termux** y ejecuta:
```bash
git clone https://github.com/Em1lio573/monochrome-cli.git
cd monochrome-cli
bash install_termux.sh
```

### 2. Instalación Manual
```bash
pkg update -y && pkg install -y python ffmpeg git
termux-setup-storage
pip install yt-dlp mutagen rich requests
pip install -e .
```

*En Android, las canciones se guardarán automáticamente en tu carpeta de música del sistema (`/sdcard/Music/` o `~/storage/shared/Music/`).*

---

## 💻 Instalación en Linux / macOS

```bash
# 1. Instalar FFmpeg y Python
sudo apt install ffmpeg python3-pip   # Ubuntu / Debian
sudo pacman -S ffmpeg python-pip     # Arch Linux
brew install ffmpeg python           # macOS

# 2. Clonar e instalar
git clone https://github.com/Em1lio573/monochrome-cli.git
cd monochrome-cli
pip install -e .
```

---

## 🎮 Guía de Uso

### 1. Modo Interactivo TUI (Recomendado)
Simplemente ejecuta:
```bash
mono
```
- Escribe el nombre de la canción, álbum o artista.
- Selecciona el número `#` de la pista deseada (o escribe `all` o `1-5`).
- Presiona `Enter` para descargar con tus opciones por defecto, o escribe `c` para cambiar el formato o activar/desactivar letras al momento.
- Escribe `fmt` para cambiar el formato activo.
- Escribe `config` para abrir el panel de configuración.

---

### 2. Modo Comando Directo (CLI)

```bash
# Descargar primer resultado en formato específico
mono "daft punk get lucky" -d -f flac
mono "the weeknd starboy" -d -f mp3_320
mono "dua lipa levitating" -d -f m4a

# Descargar con o sin letras sincronizadas
mono "queen bohemian rhapsody" -d --no-lyrics
mono "queen bohemian rhapsody" -d --lyrics

# Descargar un álbum completo
mono "tainy data" -a -f mp3_320

# Forzar re-descarga si ya existe
mono "daft punk get lucky" -d -w
```

---

### ⚙️ Guardar Preferencias Predeterminadas

```bash
# Establecer formato preferido para siempre (flac, mp3_320, mp3_256, m4a, opus)
mono --set-default-format flac

# Establecer si siempre descargar letras (.lrc) o no
mono --set-default-lyrics true

# Establecer carpeta de descargas permanente
mono --set-default-output /sdcard/Music

# Menú de configuración interactivo
mono --config
```

---

## 🙏 Créditos y Reconocimientos

Este proyecto está inspirado y construido con admiración hacia **[Monochrome Music](https://github.com/monochrome-music/monochrome)**:
- Proyecto original: [monochrome-music/monochrome](https://github.com/monochrome-music/monochrome)
- Sitio web oficial: [monochrome.tf](https://monochrome.tf)

Todos los derechos y créditos de diseño de metadatos pertenecen a los creadores originales de Monochrome.

---

## 📄 Licencia

Este proyecto se distribuye bajo la licencia **GNU General Public License v3.0 (GPL-3.0)**, al igual que el proyecto Monochrome original.
