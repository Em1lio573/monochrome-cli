# Monochrome CLI

Cliente de terminal y TUI (Text User Interface) para busqueda, descarga y gestion de audio de alta fidelidad, optimizado para entornos Linux, macOS y Termux (Android).

Inspirado en el ecosistema de codigo abierto Monochrome.

---

## Caracteristicas del Sistema

- **Descargas 100% Automaticas e Instantaneas:** Motor HQ integrado que opera de forma totalmente autonoma sin requerir inicios de sesion, resolucion de captchas ni configuraciones manuales complejas.
- **Consultas de Catalogo Oficial:** Integracion con Tidal OpenAPI y Deezer para la obtencion precisa de metadatos de estudio, codigos ISRC, creditos y discografias completas.
- **Motor de Audio y Calidad Seleccionable:**
  - **FLAC (Lossless / Hi-Res):** Audio de estudio sin perdidas (16/24-bit, 44.1 kHz hasta 192 kHz).
  - **MP3 (320 kbps CBR):** Codificacion a bitrate constante de maxima calidad con `libmp3lame`.
  - **M4A / AAC (256 kbps):** Codificacion con perfil avanzado de compresion perceptual de alta definicion.
  - **OPUS (160 kbps):** Compresion de ultima generacion optimizada para preservacion del espectro audible.
- **Incrustacion de Metadatos y Caratulas en Alta Resolucion:**
  - Caratulas oficiales en resolucion nativa (1280x1280 px).
  - Etiquetas incrustadas mediante Mutagen (ID3v2.4 para MP3, Vorbis Comments / Picture Block para FLAC y Ogg, MP4 Atoms para M4A).
- **Letras Sincronizadas (.lrc):**
  - Descarga e integracion de letras sincronizadas milimetricamente mediante LRCLIB.
  - Generacion automatica de archivos `.lrc` compatibles con reproductores de audio locales y moviles.
- **Deteccion Inteligente de Duplicados:**
  - Evita descargas redundantes verificando la existencia e integridad del archivo en disco antes de procesar el stream.
- **Gestion de Descargas Individuales y por Lotes:**
  - Soporte para descargas puntuales, rangos numericos (ej. `1-5`), selecciones separadas por comas (ej. `1,3,7`), o albumes completos respetando el orden original de pistas.
- **Soporte Opcional de Amazon Music Ultra HD:**
  - Compatibilidad opcional con streams CENC descifrados de Amazon Music Ultra HD a 24-bit si se proporciona un token de sesion (`--jwt`).
- **Compatibilidad Optimizada con Termux en Android:**
  - Creacion automatica de lanzadores globales en `$PREFIX/bin`.
  - Deteccion nativa del almacenamiento compartido de Android (`/sdcard/Music` y `~/storage/shared/Music`).

---

## Arquitectura de Descargas

Monochrome CLI opera mediante una arquitectura de obtencion de dos niveles:

1. **Nivel 1 (Motor HQ Automatico - Predeterminado):**
   Disenado para funcionamiento sin intervencion. Resuelve el stream de mayor tasa de bits disponible, procesando y transcodificando el flujo de audio con FFmpeg hacia el formato solicitado (FLAC, MP3 320k, M4A 256k u OPUS) e inyectando de forma automatica las etiquetas oficiales de Tidal, la caratula en 1280x1280 px y las letras sincronizadas.

2. **Nivel 2 (Amazon Music Lossless CENC - Opcional):**
   Para usuarios que deseen especificamente flujos Ultra HD a 24-bit desde los servidores de Amazon Music, el sistema permite configurar opcionalmente un token de sesion web (`mono --jwt <TOKEN>`). Si este token no esta configurado, el CLI no se detiene ni muestra advertencias invasivas: continua operando fluidamente a traves del Motor HQ Automatico.

---

## Requisitos del Sistema

- **Python:** Version 3.8 o superior.
- **FFmpeg:** Con soporte para decodificacion y extraccion de audio.
- **Git:** Para clonar el repositorio.

---

## Instalacion

### 1. Instalacion en Termux (Android)

#### Metodo Automatico (Recomendado)
Ejecute en la terminal de Termux:

```bash
git clone https://github.com/Em1lio573/monochrome-cli.git
cd monochrome-cli
bash install_termux.sh
```

El script actualizara los paquetes necesarios, solicitara acceso al almacenamiento de Android (`termux-setup-storage`), instalara las dependencias de Python y configurara los ejecutables globales `mono` y `monochrome` en `$PREFIX/bin`.

#### Metodo Manual
```bash
pkg update -y
pkg install -y python ffmpeg git libjpeg-turbo
termux-setup-storage
pip install --upgrade pip
pip install yt-dlp mutagen rich requests setuptools
pip install -e .
```

---

### 2. Instalacion en Linux y macOS

#### Dependencias Previas
- **Debian / Ubuntu / Linux Mint:**
  ```bash
  sudo apt update && sudo apt install -y ffmpeg python3 python3-pip git
  ```
- **Arch Linux / Manjaro:**
  ```bash
  sudo pacman -S ffmpeg python python-pip git
  ```
- **Fedora / RHEL:**
  ```bash
  sudo dnf install -y ffmpeg python3 python3-pip git
  ```
- **macOS (via Homebrew):**
  ```bash
  brew install ffmpeg python git
  ```

#### Instalacion del Paquete
```bash
git clone https://github.com/Em1lio573/monochrome-cli.git
cd monochrome-cli
pip install -e .
```

---

## Guia de Uso

### 1. Modo Interactivo (TUI)

Para iniciar la interfaz de terminal interactiva, ejecute:

```bash
mono
```

#### Comandos Disponibles dentro del Modo Interactivo:
- **`nombre_de_pista`**: Realiza una busqueda en el catalogo y despliega las coincidencias.
- **`numero_de_pista`**: Descarga la pista correspondiente (ej. `1`, `2`, `3`).
- **`all`**: Descarga todas las pistas encontradas en la busqueda.
- **`1-5` o `1,3,4`**: Descarga una seleccion especifica de resultados.
- **`fmt`**: Abre el menu para cambiar el formato de audio activo.
- **`config`**: Abre el panel de configuracion y preferencias.
- **`q`**: Sale de la aplicacion.

---

### 2. Modo Linea de Comandos (CLI)

#### Descarga Directa
```bash
# Descargar el primer resultado coincidente en formato FLAC
mono "Daft Punk Get Lucky" -d -f flac

# Descargar en formato MP3 a 320 kbps
mono "The Weeknd Blinding Lights" -d -f mp3_320

# Descargar en formato M4A (AAC 256 kbps)
mono "Dua Lipa Levitating" -d -f m4a

# Descargar en formato OPUS
mono "Queen Bohemian Rhapsody" -d -f opus
```

#### Descarga de Albumes Completos
```bash
# Buscar y descargar todas las pistas de un album
mono "Bad Bunny YHLQMDLG" -a -f flac
```

#### Opciones de Letras Sincronizadas
```bash
# Forzar descarga de letras sincronizadas (.lrc)
mono "Ed Sheeran Shape of You" -d --lyrics

# Desactivar descarga de letras sincronizadas
mono "Ed Sheeran Shape of You" -d --no-lyrics
```

#### Sobrescribir Archivos Existentes
```bash
mono "Daft Punk Around the World" -d -w
```

---

## Configuracion Persistente

Monochrome CLI almacena las preferencias de usuario en `~/.config/monochrome-cli/config.json`. Puede modificarlas mediante el menu interactivo (`mono --config`) o mediante flags de linea de comandos:

```bash
# Establecer el formato de descarga predeterminado
mono --set-default-format flac
mono --set-default-format mp3_320
mono --set-default-format m4a
mono --set-default-format opus

# Establecer la carpeta de destino predeterminada
mono --set-default-output "/home/usuario/Musica"

# Activar o desactivar letras sincronizadas por defecto
mono --set-default-lyrics true
mono --set-default-lyrics false

# Configurar opcionalmente el token de sesion para Amazon Music Ultra HD
mono --jwt "<TOKEN_TURNSTILE>"
```

---

## Formatos de Audio y Especificaciones Tecnicas

| Formato | Extension | Bitrate / Profundidad | Codec de Salida | Uso Recomendado |
| :--- | :---: | :---: | :---: | :--- |
| **FLAC** | `.flac` | 16/24-bit (1.400 - 9.200 kbps) | FLAC | Audio de maxima fidelidad sin perdidas (Audiophile). |
| **MP3 320k** | `.mp3` | 320 kbps CBR | libmp3lame | Maxima compatibilidad universal con alta calidad. |
| **M4A** | `.m4a` | 256 kbps VBR/CBR | AAC (libfdk_aac/aac) | Ecosistema Apple y dispositivos moviles. |
| **OPUS** | `.opus` | 160 kbps VBR | libopus | Maxima eficiencia de almacenamiento con fidelidad perceptual. |
| **MP3 256k / 128k** | `.mp3` | 256 / 128 kbps | libmp3lame | Ahorro de espacio en disco. |

---

## Estructura del Proyecto

```text
monochrome-cli/
├── mono.py                     # Lanzador principal del ejecutable
├── setup.py                    # Configuracion de empaquetado pip
├── install_termux.sh           # Instalador automatizado para Termux (Android)
├── monochrome_cli/
│   ├── main.py                 # Punto de entrada CLI y control de flujo TUI
│   ├── config.py               # Gestion de configuracion persistente
│   ├── types.py                # Modelos de datos y definiciones de formato
│   ├── core/
│   │   ├── search.py           # Buscador en catalogo oficial de Tidal y Deezer
│   │   ├── unified.py          # Motor de resolucion y descifrado Lossless
│   │   ├── downloader.py       # Gestor de streams, conversiones y fallbacks
│   │   ├── tagger.py           # Inyeccion de metadatos y caratulas en alta resolucion
│   │   └── lyrics.py           # Descarga y formateo de letras sincronizadas (.lrc)
│   ├── ui/
│   │   ├── banner.py           # Presentacion visual de terminal
│   │   └── tables.py           # Tablas de resultados, configuracion y formatos
│   └── utils/
│       ├── platform.py         # Deteccion de plataforma (Android, Termux, Linux, macOS)
│       └── template.py         # Generador de rutas y nombres segun plantilla
└── tests/                      # Suite de pruebas automatizadas
    ├── test_search.py
    ├── test_lyrics.py
    ├── test_tagger.py
    ├── test_downloader.py
    ├── test_unified_downloader.py
    └── test_famous_tracks.py
```

---

## Licencia

Este proyecto esta desarrollado con fines educativos y de gestion de bibliotecas de audio personales.\n