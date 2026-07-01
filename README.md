# Llama Server Launcher

Windows 桌面版 `llama-server` 启动器，用于集中配置、启动、停止和监控 llama.cpp 的 server 进程。界面使用 CustomTkinter 控件构建，但主窗口使用原生 `tk.Tk()`，以降低 Windows 拖拽窗口时的卡顿。

## 功能

- 自动扫描模型目录下的 `.gguf` 文件。
- 可视化配置模型、`llama-server.exe`、端口、上下文长度、GPU 层数、线程、采样等参数。
- 高级参数默认可见，按 Tab 分类管理采样、GPU/MoE、投机解码、服务工具和自定义参数。
- 实时生成启动命令预览，启动后可查看参数快照。
- 启动后切换到运行控制台，显示日志、PID、硬件监控、Token 统计和异常捕获。
- 配置保存到 `config.toml`，下次启动自动恢复。
- llama-server 的工作目录设为 `workspace/`，避免工具输出污染项目根目录。

## 环境

| 项目 | 要求 |
| --- | --- |
| 操作系统 | Windows 10 / 11 |
| Python | 3.11+ |
| GUI | tkinter + CustomTkinter 6.0.0 |
| 依赖 | `psutil`, `nvidia-ml-py` |
| 外部程序 | `llama-server.exe` |
| 模型格式 | GGUF |

## 快速启动

推荐双击运行：

```bat
llama一键启动器.bat
```

脚本会在项目目录创建 `.venv`。依赖已存在时不会重复执行 `pip install`，缺失依赖时才安装 `requirements.txt`。

手动启动：

```bat
.venv\Scripts\python.exe llama_launcher_backup.py
```

首次手动安装依赖：

```bat
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## 命令行覆盖

启动器支持用命令行参数覆盖部分配置：

```bat
.venv\Scripts\python.exe llama_launcher_backup.py --model "D:\models\Qwen.gguf" --server "D:\llama.cpp\llama-server.exe" --port 8080 -c 32768 -ngl 99
```

常用参数：

| 参数 | 说明 |
| --- | --- |
| `-m`, `--model` | 模型文件路径 |
| `--server` | `llama-server.exe` 路径 |
| `--host` | 监听地址 |
| `--port` | 监听端口 |
| `-c`, `--ctx-size` | 上下文长度 |
| `-n`, `--n-predict` | 最大生成 token 数 |
| `-ngl`, `--n-gpu-layers` | GPU 加速层数 |
| `-t`, `--threads` | CPU 线程数 |
| `--threads-batch` | 批处理线程数 |
| `-b`, `--batch-size` | batch size |
| `--ubatch-size` | micro batch size |
| `--temp` | 采样温度 |
| `--mmproj` | 视觉投影模型路径 |
| `--timeout` | 请求超时 |
| `--sleep-idle-seconds` | 空闲休眠时间 |
| `--tools` | llama-server 工具参数 |
| `--flash-attention` | Flash Attention 模式 |
| `--chat-template-kwargs` | chat template JSON 参数 |

## 使用流程

1. 设置 `llama-server.exe` 路径。
2. 设置模型根目录并点击刷新，或直接选择模型文件。
3. 调整基础参数和右侧高级参数。
4. 点击保存写入 `config.toml`。
5. 点击启动，程序会保存当前配置、启动子进程并切换到运行控制台。
6. 点击停止可终止当前 server 进程。

## 性能相关实现

为降低窗口拖拽卡顿，当前实现做了几项处理：

- 主窗口使用原生 `tk.Tk()`，避免 `customtkinter.CTk` 在 Windows 上的标题栏和 DPI 几何处理影响拖拽。
- 启动前修补 CustomTkinter 6.0.0 的外观/DPI 轮询和 `block_update_dimensions_event()` 行为。
- 高级参数保持默认可见；运行控制台延迟到启动服务或切换运行视图时再创建。
- 日志、命令预览和异常捕获使用轻量 `tk.Text`，减少 CTk Canvas 数量。
- 日志刷新分批处理，单次最多处理有限行数，避免大量输出阻塞 Tk 主循环。

## 项目结构

详见 [Project Structure.md](Project%20Structure.md)。

## 配置文件

`config.toml` 保存用户配置，包括：

- `llama-server` 路径
- 模型根目录和模型路径
- host、port、上下文长度、线程、GPU 层数
- 采样参数
- GPU/MoE、投机解码、缓存类型等高级参数
- 自定义命令行参数
- 窗口位置和大小

## 常见问题

### 双击 bat 后没有启动

在项目目录手动运行：

```bat
.venv\Scripts\python.exe llama_launcher_backup.py
```

如果提示缺依赖：

```bat
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

### 启动失败

检查以下项目：

- `llama-server.exe` 路径是否正确。
- 模型路径是否正确。
- 端口是否被占用。
- 当前 llama-server 版本是否支持所选参数。

启动失败时，启动器会清理已创建的子进程状态并恢复启动按钮；详细 traceback 会写入运行日志，修正配置后可以直接再次点击启动。

### 拖拽窗口仍然卡顿

先关闭所有旧启动器窗口，并在任务管理器中确认没有残留的 `pythonw.exe` 启动器进程，再重新双击 bat。旧窗口不会加载新的性能优化代码。

## 许可

MIT License。
