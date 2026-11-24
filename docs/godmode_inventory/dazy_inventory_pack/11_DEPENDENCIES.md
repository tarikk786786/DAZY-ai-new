# 11 — Dependencies and package inventory

## Desktop Python `requirements.txt`

The following are declared dependencies, with constraints copied from the inspected file where specified. Some are OS-specific; some are optional/commented and not installed by the default setup.

### Base and runtime dependencies

| Package | Declared form | Role |
|---|---|---|
| PyQt6 | `>=6.6,<7` | Desktop GUI |
| sounddevice | `>=0.4,<1` | Audio device capture/playback |
| numpy | `>=1.24,<3` | Audio arrays and numerical work |
| google-genai | `>=2.8.0,<3` | Gemini SDK |
| httpx | `>=0.27,<1` | HTTP/API clients |
| requests | `>=2.31,<3` | HTTP integrations |
| certifi | `>=2024.2.2` | CA certificates |
| beautifulsoup4 | `>=4.12,<5` | HTML parsing |
| playwright | `>=1.40,<2` | Browser automation |
| yt-dlp | unbounded | YouTube/media stream extraction |
| pyautogui | unpinned | Mouse/keyboard automation |
| pyperclip | unpinned | Clipboard |
| pillow | `>=13.0.0` | Image processing |
| opencv-python | `>=4.8,<5` | Computer vision |
| mss | `>=9,<11` | Screen capture |
| psutil | `>=5.9,<8` | System monitoring |
| send2trash | unpinned | Recoverable file deletion |
| python-pptx | unpinned | PowerPoint file processing |
| fastapi | `>=0.110,<1` | Remote backend/dashboard API |
| uvicorn[standard] | `>=0.27,<1` | ASGI server |
| cryptography | `>=50.0.0` | Cryptographic functions |
| python-multipart | `>=0.0.9,<1` | Multipart uploads |
| qrcode[pil] | `>=7,<9` | QR pairing |
| google-api-python-client | unpinned | Google APIs |
| google-auth-oauthlib | unpinned | Google OAuth |
| tinytuya | unpinned | Tuya/Smart Life device control |
| paho-mqtt | unpinned | MQTT integration |
| openpyxl | unpinned | Excel output |
| youtube-transcript-api | unpinned | YouTube transcript retrieval |
| pygetwindow | unpinned | Window geometry |
| ddgs | `>=9,<10` | DuckDuckGo search client |
| pdfplumber | unpinned | PDF text/table extraction |
| PyPDF2 | unpinned | PDF fallback reading |
| python-docx | unpinned | DOCX processing |
| pynvml | unpinned | NVIDIA GPU monitoring |

### Windows-only dependencies (`sys_platform == win32`)

`comtypes`, `pycaw`, `win10toast`, `pywin32`, `wmi`, `pywinauto`.

### Optional packages described in requirements comments

- `pandas` — spreadsheet/CSV analysis.
- `pydub` — audio metadata/conversion; ffmpeg typically also required.
- `mediapipe` — pose/rep detection.
- `faster-whisper` — local CPU transcription.
- `piper-tts` — local neural TTS.
- `openwakeword` — local wake-word recognition; one-click opt-in in app.

### Backend requirements

`backend/requirements.txt`: `fastapi>=0.110.0`, `uvicorn>=0.28.0`, `pydantic>=2.6.0`, `httpx>=0.27.0`.

## Web npm dependencies

### Direct production dependencies

| Package | Range | Role |
|---|---|---|
| @supabase/supabase-js | `^2.45.0` | Supabase client |
| react | `^18.3.1` | UI runtime |
| react-dom | `^18.3.1` | DOM renderer |

### Direct dev dependencies

| Package | Range | Role |
|---|---|---|
| @types/react | `^18.3.12` | React typings |
| @types/react-dom | `^18.3.1` | React DOM typings |
| @vitejs/plugin-react | `^4.3.4` | Vite React plugin |
| typescript | `^5.6.3` | TypeScript |
| vite | `^5.4.11` | Build/dev tool |

The checked package-lock contained 124 package entries, including transitive packages. The lockfile resolves some newer patch/minor versions than package.json ranges; run `npm ci` to reproduce lockfile resolution.

## Installation/setup notes from repository

Desktop `setup.py` targets Python 3.11 minimum and says 3.12 is the tested upper bound at the time that file was written; it continues with a warning on newer Python versions. It installs platform-specific requirements and attempts Playwright Chromium/Firefox setup. The README/setup scripts contain inherited MARK naming in places.

Web: `npm install` / `npm run dev`; build script is `tsc -b --noCheck && vite build`.

## Important

A declared package is not necessarily imported on every startup. Provider registry and lazy imports are intentionally used so large optional engines do not load unless selected. Check exact runtime installation with `pip show`, `pip freeze`, `npm ls` or an environment audit on the actual PC.
