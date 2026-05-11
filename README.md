# 小红书视频转文字工具

这是一个基于 Python 的命令行工具，用于：

- 通过插件下载视频
- 解析小红书 / Rednote 视频链接
- 调用 DashScope ASR 做语音转文字
- 将转写结果保存到本地文本文件

当前项目主要围绕小红书链接场景构建，但下载层是插件式设计，后续可以继续扩展到其他平台。

> 请仅处理你拥有、已获授权，或平台允许访问与转写的内容。本项目不会绕过 DRM、付费限制或平台访问控制。

## 项目介绍

这个项目的目标很直接：给一个视频链接，程序自动完成下载、提取可转写内容，并输出文字结果。

当前已支持的核心能力：

- 处理小红书 / Rednote 视频链接
- 支持直链视频和本地视频文件
- 自动选择合适的 ASR 后端
- 支持本地配置 API Key 和 Cookie
- 支持后续通过插件机制扩展更多来源

## 快速开始

### 1. 安装系统依赖

先确认本机有这些工具：

```bash
python3 --version
ffmpeg -version
yt-dlp --version
curl --version
```

如果你在 macOS 上使用 Homebrew，可以执行：

```bash
brew install ffmpeg yt-dlp
```

### 2. 克隆仓库

```bash
git clone https://github.com/Haoxuan006631/Xiaohonshu_Video_to_TextViaQwen.git
cd Xiaohonshu_Video_to_TextViaQwen
```

### 3. 创建本地配置文件

复制示例配置：

```bash
cp local.secrets.example.json local.secrets.json
```

然后填写你自己的信息：

- `api_key`：DashScope API Key
- `cookie_header`：浏览器中复制出来的小红书 Cookie 字符串

### 4. 运行命令

```bash
PYTHONPATH=src python3 -m xhs_qwen_transcriber.cli \
  --plugin xiaohongshu-ytdlp \
  --region intl \
  "https://www.xiaohongshu.com/discovery/item/..."
```

## 配置方式

程序支持两种常见配置方式。

### 方式一：使用 `local.secrets.json`

示例：

```json
{
  "api_key": "REPLACE_WITH_YOUR_DASHSCOPE_API_KEY",
  "cookie_header": "REPLACE_WITH_YOUR_XIAOHONGSHU_COOKIE_HEADER"
}
```

### 方式二：在命令行直接传入

```bash
PYTHONPATH=src python3 -m xhs_qwen_transcriber.cli \
  --api-key "your-api-key" \
  --cookie-header "a=1; b=2; c=3" \
  "https://www.xiaohongshu.com/discovery/item/..."
```

如果你已经有 Netscape 格式的 `cookies.txt` 文件，也可以这样传：

```bash
PYTHONPATH=src python3 -m xhs_qwen_transcriber.cli \
  --cookies ./cookies.txt \
  "https://www.xiaohongshu.com/discovery/item/..."
```

## 示例命令

### 处理小红书 / Rednote 完整视频链接

```bash
PYTHONPATH=src python3 -m xhs_qwen_transcriber.cli \
  --plugin xiaohongshu-ytdlp \
  --region intl \
  "https://www.xiaohongshu.com/discovery/item/68a32405000000001d004cdb?..."
```

### 处理本地视频文件

```bash
PYTHONPATH=src python3 -m xhs_qwen_transcriber.cli \
  --asr-backend qwen \
  ./demo.mp4
```

### 强制指定 ASR 后端

```bash
PYTHONPATH=src python3 -m xhs_qwen_transcriber.cli \
  --asr-backend fun-asr \
  --region intl \
  "https://www.xiaohongshu.com/discovery/item/..."
```

## 工作原理

### 下载层

下载层使用插件机制，当前内置插件包括：

- `xiaohongshu-ytdlp`
- `direct-url`
- `local-file`

其中小红书插件采用两段式流程：

1. 用 `yt-dlp` 解析分享页，提取真实媒体 URL
2. 用 `curl` 直接下载视频

这样做比完全依赖 `yt-dlp` 承担最终下载更稳定，尤其是在部分小红书链接场景下。

### 转写层

当前支持三种后端模式：

- `fun-asr`
- `qwen`
- `auto`

默认策略如下：

- 如果下载结果里有公网可访问的媒体 URL，`auto` 优先使用 `fun-asr`
- 如果只有本地文件可用，`auto` 回退到 `qwen`

## 输出结果

默认输出目录在 `runs/` 下：

- `runs/downloads/`：下载后的视频文件
- `runs/audio/`：使用本地音频转写时生成的中间音频
- `runs/transcript.txt`：最终转写文本

## 项目结构

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

## 注意事项

- 小红书短链通常不如完整 `item` 链接稳定
- 某些链接必须依赖有效的浏览器登录态 Cookie
- DashScope 区域要和你的密钥匹配：
  - `--region intl`：国际区 / 新加坡
  - `--region cn`：中国内地区域
- 有些媒体 URL 你的机器可以访问，但云端 ASR 服务端不一定能成功拉取
- 使用 `qwen` 做本地音频同步转写时，过大的音频文件可能超出当前实现的同步上传限制

## 开发说明

查看 CLI 帮助：

```bash
PYTHONPATH=src python3 -m xhs_qwen_transcriber.cli --help
```

做语法检查：

```bash
python3 -m compileall src
```

## 自定义插件

可以参考 [examples/custom_plugin.py](examples/custom_plugin.py) 编写自定义插件。

每个插件至少需要提供：

- `name`
- `can_handle(url)`
- `download(request)`

同时导出：

```python
def register(registry):
    registry.register(YourPlugin())
```
