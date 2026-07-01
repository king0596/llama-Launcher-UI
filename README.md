# Llama Server Launcher

![Python](https://img.shields.io/badge/Python-3.11%2B-blue)
![License](https://img.shields.io/badge/License-MIT-green)
![Platform](https://img.shields.io/badge/Platform-Windows%2010%2F11-00a8e8)
![CustomTkinter](https://img.shields.io/badge/CustomTkinter-6.0.0-orange)
![llama.cpp](https://img.shields.io/badge/llama.cpp-latest-red)

Windows 桌面版 `llama-server` 启动器，用于集中配置、启动、停止和监控 llama.cpp 的 server 进程。

基于 CustomTkinter 构建 GUI，主窗口使用原生 `tk.Tk()` 以降低 Windows 拖拽窗口时的卡顿。

## 目录

- [Llama Server Launcher](#llama-server-launcher)
  - [目录](#目录)
  - [功能特性](#功能特性)
  - [环境要求](#环境要求)
  - [安装](#安装)
    - [方式一：一键启动（推荐）](#方式一一键启动推荐)
    - [方式二：手动安装](#方式二手动安装)
  - [使用方法](#使用方法)
  - [命令行参数](#命令行参数)
  - [配置文件](#配置文件)
  - [项目结构](#项目结构)
    - [架构](#架构)
  - [开发指南](#开发指南)
    - [模块修改指南](#模块修改指南)
    - [性能注意事项](#性能注意事项)
    - [性能优化](#性能优化)
  - [常见问题](#常见问题)
    - [双击 bat 后没有启动](#双击-bat-后没有启动)
    - [启动失败](#启动失败)
    - [拖拽窗口仍然卡顿](#拖拽窗口仍然卡顿)
  - [许可](#许可)
  - [致谢](#致谢)

---

## 功能特性

- **模型管理** - 自动扫描模型目录下的 `.gguf` 文件，可视化选择模型
- **参数配置** - 可视化配置模型、`llama-server.exe`、端口、上下文长度、GPU 层数、线程、采样等参数
- **高级参数** - 按 Tab 分类管理采样、GPU/MoE、投机解码、服务工具和自定义参数
- **命令预览** - 实时生成启动命令预览，启动后可查看参数快照
- **运行监控** - 启动后切换到运行控制台，显示日志、PID、硬件监控、Token 统计和异常捕获
- **配置持久化** - 配置保存到 `config.toml`，下次启动自动恢复
- **工作目录隔离** - llama-server 的工作目录设为 `workspace/`，避免工具输出污染项目根目录

---

## 环境要求

| 项目 | 要求 |
| --- | --- |
| 操作系统 | Windows 10 / 11 |
| Python | 3.11+ |
| GUI 框架 | tkinter + CustomTkinter 6.0.0 |
| Python 依赖 | `psutil`, `nvidia-ml-py` |
| 外部程序 | `llama-server.exe` |
| 模型格式 | GGUF |

---

## 安装

### 方式一：一键启动（推荐）

双击运行 `llama一键启动器.bat`。

脚本会自动创建 `.venv` 虚拟环境。依赖已存在时不会重复执行 `pip install`，仅在缺失依赖时安装 `requirements.txt`。

### 方式二：手动安装

```bat
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe llama_launcher_backup.py
```

---

## 使用方法

1. 设置 `llama-server.exe` 路径
2. 设置模型根目录并点击刷新，或直接选择模型文件
3. 调整基础参数和右侧高级参数
4. 点击保存写入 `config.toml`
5. 点击启动，程序会保存当前配置、启动子进程并切换到运行控制台
6. 点击停止可终止当前 server 进程

---

## 命令行参数

启动器支持用命令行参数覆盖部分配置：

```bat
.venv\Scripts\python.exe llama_launcher_backup.py --model "D:\models\Qwen.gguf" --server "D:\llama.cpp\llama-server.exe" --port 8080 -c 32768 -ngl 99
```

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

---

## 配置文件

`config.toml` 保存用户配置，包括：

- `llama-server` 路径
- 模型根目录和模型路径
- host、port、上下文长度、线程、GPU 层数
- 采样参数
- GPU/MoE、投机解码、缓存类型等高级参数
- 自定义命令行参数
- 窗口位置和大小

---

## 项目结构

```text
llama service lunch/
├─ llama_launcher_backup.py      # 主入口，组装 LlamaLauncher 和运行时补丁
├─ llama一键启动器.bat           # Windows 一键启动脚本
├─ requirements.txt              # Python 依赖
├─ config.toml                   # 用户配置，运行时读写
├─ README.md                     # 项目说明
├─ 千问系列参数.txt              # 模型参数参考
├─ workspace/                    # llama-server 工作目录和工具输出目录（已忽略）
│
├─ config/
│  ├─ colors.py                  # UI 配色
│  ├─ defaults.py                # 默认配置
│  └─ params.py                  # 参数标签和 tooltip 元数据
│
├─ utils/
│  ├─ cli.py                     # 命令行参数解析
│  └─ toml_io.py                 # TOML 写入工具
│
├─ ui/
│  ├─ widgets.py                 # 通用控件构建 helper
│  └─ views.py                   # 主界面、配置页、运行页和高级参数 Tab
│
└─ core/
   ├─ command.py                 # 命令构建、命令预览、启动快照
   ├─ config_manager.py          # 配置读写、校验、模型扫描
   ├─ monitor.py                 # 硬件监控、Token 统计、异常捕获
   └─ server.py                  # server 进程、日志、状态、WebUI
```

### 架构

项目使用 mixin 组合模式。`LlamaLauncher` 只负责初始化共享状态、创建 Tk 变量、加载配置并调用各 mixin 的构建流程。

```text
LlamaLauncher
├─ UIWidgetMixin      ui/widgets.py
├─ ViewMixin          ui/views.py
├─ ServerMixin        core/server.py
├─ CommandMixin       core/command.py
├─ ConfigMixin        core/config_manager.py
└─ MonitorMixin       core/monitor.py
```

各 mixin 通过 `self` 共享 Tk 变量、配置、进程对象和 UI 控件引用。

---

## 开发指南

### 模块修改指南

| 需求 | 主要文件 |
| --- | --- |
| 新增 llama-server 参数 | `config/params.py`, `llama_launcher_backup.py`, `core/command.py`, `core/config_manager.py`, `ui/views.py` |
| 修改 UI 布局 | `ui/views.py` |
| 修改通用控件样式 | `ui/widgets.py`, `config/colors.py` |
| 修改启动/停止逻辑 | `core/server.py` |
| 修改监控或统计 | `core/monitor.py` |
| 修改配置格式 | `config/defaults.py`, `core/config_manager.py` |
| 修改启动脚本 | `llama一键启动器.bat` |

### 性能注意事项

- 不要在主界面一次性创建大量 `CTkTextbox` 或 `CTkScrollableFrame`
- 不要在未必要时增加 `after()` 高频轮询
- 新增周期任务时需要保存 `after_id`，停止服务或关闭窗口时取消
- 如果新增运行页控件，优先放在运行页懒加载流程中，而不是 `build_ui()` 首屏创建

### 性能优化

为降低窗口拖拽卡顿，当前实现做了几项处理：

- 主窗口使用原生 `tk.Tk()`，避免 CustomTkinter 在 Windows 上的标题栏和 DPI 几何处理影响拖拽
- 启动前修补 CustomTkinter 6.0.0 的外观/DPI 轮询和 `block_update_dimensions_event()` 行为
- 高级参数保持默认可见；运行控制台延迟到启动服务或切换运行视图时再创建
- 日志、命令预览和异常捕获使用轻量 `tk.Text`，减少 CTk Canvas 数量
- 日志刷新分批处理，单次最多处理有限行数，避免大量输出阻塞 Tk 主循环

---

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

- `llama-server.exe` 路径是否正确
- 模型路径是否正确
- 端口是否被占用
- 当前 llama-server 版本是否支持所选参数

启动失败时，启动器会清理已创建的子进程状态并恢复启动按钮；详细 traceback 会写入运行日志，修正配置后可以直接再次点击启动。

### 拖拽窗口仍然卡顿

先关闭所有旧启动器窗口，并在任务管理器中确认没有残留的 `pythonw.exe` 启动器进程，再重新双击 bat。旧窗口不会加载新的性能优化代码。

---

## 许可

[MIT License](LICENSE)

Copyright (c) 2026 king0596

---

## 致谢

- [ggml-org/llama.cpp](https://github.com/ggml-org/llama.cpp) - llama-server 实现
- [customtkinter](https://github.com/Tk-node/customtkinter) - GUI 框架
