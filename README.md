# 小红书视频转文字：插件式下载 + Qwen ASR

这是一个最小可跑的 Python CLI：输入一个视频链接或本地视频文件，通过插件拿到视频，抽取音频，再调用 Qwen/Qwen3 ASR 把语音转成文字。

> 请只处理你自己拥有、已获授权，或平台明确允许下载/处理的内容。这个项目不会绕过登录、付费、DRM 或访问控制；小红书插件只是调用本机 `yt-dlp` 处理可合法访问的链接。

## 能力

- 内置插件：`local-file`、`direct-url`、`xiaohongshu-ytdlp`
- 支持自定义插件：把 `*.py` 放进 `plugins/`，实现 `register(registry)`
- 使用 Qwen 官方 OpenAI-compatible ASR：`qwen3-asr-flash`
- 默认抽取 16kHz 单声道 MP3，并限制同步 ASR 音频在 `9.5MB` 内
- 小红书下载走“两段式”：`yt-dlp` 负责解析分享页，`curl`/内置下载器负责直链落盘，规避末尾断流

## 依赖

需要系统里有：

```bash
python3 --version
ffmpeg -version
yt-dlp --version   # 只在处理小红书链接时需要
```

如果没有：

```bash
brew install ffmpeg yt-dlp
```

## 使用

```bash
export DASHSCOPE_API_KEY="你的百炼或 Qwen API Key"
python3 -m xhs_qwen_transcriber.cli "https://www.xiaohongshu.com/..."
```

本地视频：

```bash
python3 -m xhs_qwen_transcriber.cli ./demo.mp4
```

如果链接需要你自己的浏览器登录态，可导出 cookies 后传给 `yt-dlp`：

```bash
python3 -m xhs_qwen_transcriber.cli "https://www.xiaohongshu.com/..." --cookies ./cookies.txt
```

如果你手头只有浏览器里复制出来的一整段 Cookie 字符串，也可以直接传：

```bash
python3 -m xhs_qwen_transcriber.cli "https://www.xiaohongshu.com/..." --cookie-header 'a=1; b=2; c=3'
```

如果你想把配置放到本地文件里，复制 `local.secrets.example.json` 为 `local.secrets.json`，再填入你自己的 API Key 和 Cookie。

输出默认在：

- `runs/downloads/`：下载后的视频
- `runs/audio/`：抽取后的音频
- `runs/transcript.txt`：转写文本


## Qwen 区域

默认使用国际站新加坡端点：

```bash
python3 -m xhs_qwen_transcriber.cli ./demo.mp4 --region intl
```

中国内地北京端点：

```bash
python3 -m xhs_qwen_transcriber.cli ./demo.mp4 --region cn
```

根据阿里云 Model Studio 文档，OpenAI-compatible `qwen3-asr-flash` 适合 10MB 以内短音频；长音频应改接 DashScope async `qwen3-asr-flash-filetrans`。

## 自定义插件

参考 `examples/custom_plugin.py`。插件只需要提供：

```python
def register(registry):
    registry.register(YourPlugin())
```

其中 `YourPlugin` 实现：

- `name`
- `can_handle(url)`
- `download(request) -> DownloadResult`

## 常见问题

- `Missing required command: ffmpeg`：安装 `ffmpeg`
- `Missing required command: yt-dlp`：安装 `yt-dlp`
- `Audio file is ... above the limit`：缩短视频、降低码率，或扩展异步 Qwen 文件转写
- `FILE_403_FORBIDDEN`：音频 URL 不可公开访问；当前实现用 Base64 Data URL，通常不会遇到，除非你改成 URL 模式
