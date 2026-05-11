# Xiaohongshu Video to Text via Qwen

A small Python CLI for downloading videos through plugins and turning speech into text with DashScope ASR.

This project currently focuses on Xiaohongshu / Rednote links, but the downloader layer is plugin-based so it can be extended to other sources later.

> Use this project only for content you own, are authorized to process, or are otherwise allowed to access and transcribe. It does not attempt to bypass DRM, payment gates, or platform access controls.

## Project Overview

- Download a video from a supported link
- Resolve Xiaohongshu pages through a dedicated plugin
- Transcribe speech with DashScope ASR
- Save the transcript to a local text file
- Keep the architecture open for additional video source plugins

## Quick Start

### 1. Install system dependencies

```bash
python3 --version
ffmpeg -version
yt-dlp --version
curl --version
```

On macOS with Homebrew:

```bash
brew install ffmpeg yt-dlp
```

### 2. Clone the repo and enter it

```bash
git clone https://github.com/Haoxuan006631/Xiaohonshu_Video_to_TextViaQwen.git
cd Xiaohonshu_Video_to_TextViaQwen
```

### 3. Create your local secrets file

Copy the example file:

```bash
cp local.secrets.example.json local.secrets.json
```

Then fill in:

- `api_key`: your DashScope API key
- `cookie_header`: your Xiaohongshu / Rednote browser cookie string

### 4. Run the CLI

```bash
PYTHONPATH=src python3 -m xhs_qwen_transcriber.cli \
  --plugin xiaohongshu-ytdlp \
  --region intl \
  "https://www.xiaohongshu.com/discovery/item/..."
```

## Configuration

The CLI supports two ways to provide secrets.

### Option A: `local.secrets.json`

Example:

```json
{
  "api_key": "REPLACE_WITH_YOUR_DASHSCOPE_API_KEY",
  "cookie_header": "REPLACE_WITH_YOUR_XIAOHONGSHU_COOKIE_HEADER"
}
```

### Option B: pass values directly

```bash
PYTHONPATH=src python3 -m xhs_qwen_transcriber.cli \
  --api-key "your-api-key" \
  --cookie-header "a=1; b=2; c=3" \
  "https://www.xiaohongshu.com/discovery/item/..."
```

You can also use a Netscape-style cookie file:

```bash
PYTHONPATH=src python3 -m xhs_qwen_transcriber.cli \
  --cookies ./cookies.txt \
  "https://www.xiaohongshu.com/discovery/item/..."
```

## Example Commands

### Xiaohongshu / Rednote item link

```bash
PYTHONPATH=src python3 -m xhs_qwen_transcriber.cli \
  --plugin xiaohongshu-ytdlp \
  --region intl \
  "https://www.xiaohongshu.com/discovery/item/68a32405000000001d004cdb?..."
```

### Local video file

```bash
PYTHONPATH=src python3 -m xhs_qwen_transcriber.cli \
  --asr-backend qwen \
  ./demo.mp4
```

### Force the ASR backend

```bash
PYTHONPATH=src python3 -m xhs_qwen_transcriber.cli \
  --asr-backend fun-asr \
  --region intl \
  "https://www.xiaohongshu.com/discovery/item/..."
```

## How It Works

### Download layer

The downloader is plugin-based. Built-in plugins include:

- `xiaohongshu-ytdlp`
- `direct-url`
- `local-file`

For Xiaohongshu, the plugin uses a two-stage flow:

1. `yt-dlp` parses the shared page and extracts the real media URL
2. `curl` downloads the media directly

This is more reliable than letting `yt-dlp` handle the final video transfer by itself for some Rednote links.

### ASR layer

The CLI supports:

- `fun-asr`
- `qwen`
- `auto`

Current behavior:

- If the downloader returns a public media URL, `auto` prefers `fun-asr`
- If only a local file is available, `auto` falls back to `qwen`

## Output

By default, output is written under `runs/`:

- `runs/downloads/` for downloaded videos
- `runs/audio/` for extracted audio when using local-audio transcription
- `runs/transcript.txt` for the final transcript

## Project Structure

```text
src/xhs_qwen_transcriber/
  cli.py
  fun_asr.py
  qwen_asr.py
  downloaders.py
  plugin_base.py
  plugin_loader.py
  plugins/
```

## Notes and Limitations

- Xiaohongshu short links may be less stable than full item URLs
- Some links require a valid browser session cookie
- DashScope region matters:
  - `--region intl` for international / Singapore credentials
  - `--region cn` for mainland China credentials
- Some source media URLs may be downloadable from your machine but not retrievable by the ASR provider from their servers
- For local-file transcription with `qwen`, very large audio inputs may exceed the sync upload path used in this project

## Development Notes

Run help:

```bash
PYTHONPATH=src python3 -m xhs_qwen_transcriber.cli --help
```

Sanity check syntax:

```bash
python3 -m compileall src
```

## Custom Plugins

See [examples/custom_plugin.py](examples/custom_plugin.py) for the minimal shape of a custom plugin.

Each plugin should expose a `register(registry)` function and a plugin object with:

- `name`
- `can_handle(url)`
- `download(request)`
