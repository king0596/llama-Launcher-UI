# Llama Server Launcher

![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?style=flat-square&logo=python&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-blue.svg?style=flat-square)
![Platform](https://img.shields.io/badge/Platform-Windows-blue?style=flat-square&logo=windows)
![CustomTkinter](https://img.shields.io/badge/Framework-CustomTkinter-green?style=flat-square)
![Status](https://img.shields.io/badge/Status-Active-success?style=flat-square)

一个用于便携启动和管理 `llama-server` 的 Windows 桌面图形化工具。基于 CustomTkinter 构建，支持模型自动扫描、参数可视化配置、实时日志监控和运行状态管理。

## 技术栈

| 类别 | 技术 | 版本 |
|------|------|------|
| 语言 | Python | 3.11+ |
| UI 框架 | CustomTkinter | 6.0.0 |
| 底层 UI | tkinter (Tk 8.6+) | 内置 |
| 配置格式 | TOML | - |
| 目标程序 | llama-server (llama.cpp) | - |

## 功能特性

- **模型管理** — 自动扫描指定目录下的 `.gguf` 模型文件，支持下拉选择与相对路径显示
- **参数配置** — 可视化配置上下文长度、GPU 层数、线程、批处理、采样等常用参数
- **高级选项** — 投机解码、MoE、Flash Attention、缓存类型、多 GPU 分割等高级参数管理
- **命令预览** — 实时预览完整启动命令，启动后可查看参数快照
- **运行监控** — 实时日志输出、进程状态轮询、端口就绪检测
- **配置持久化** — 所有参数自动保存到 `config.toml`，下次启动自动恢复
- **命令行覆盖** — 支持通过命令行参数覆盖配置文件中的值
- **OpenClaw 集成** — 支持一键启动/停止 OpenClaw 网关

## 运行环境

| 项目 | 要求 |
|------|------|
| 操作系统 | Windows 10 / 11 |
| Python | 3.11 或更高版本 |
| 依赖 | `customtkinter`（自动安装） |
| 外部程序 | `llama-server.exe`（需自行准备） |
| 模型格式 | GGUF (`.gguf`) |

## 快速开始

### 方式一：一键启动（推荐）

双击运行：

```bat
llama一键启动器.bat
```

启动脚本会自动完成以下操作：

1. 在项目目录创建 `.venv` 虚拟环境
2. 使用虚拟环境的 Python 安装 `requirements.txt` 中的依赖
3. 使用 `pythonw.exe` 后台启动主程序（无控制台窗口）

### 方式二：手动启动

```bat
python -m pip install -r requirements.txt
python llama_launcher_backup.py
```

### 命令行参数

启动时可通过命令行参数覆盖配置：

```bat
python llama_launcher_backup.py --model "D:/models/Qwen3-8B.gguf" --port 8080 -c 32000 -ngl 99
```

可用参数：

| 参数 | 说明 |
|------|------|
| `-m`, `--model` | 模型文件路径 |
| `--server` | llama-server 可执行文件路径 |
| `--host` | 监听地址（默认 `0.0.0.0`） |
| `--port` | 监听端口（默认 `8080`） |
| `-c`, `--ctx-size` | 上下文长度 |
| `-n`, `--n-predict` | 最大生成 token 数 |
| `-ngl`, `--n-gpu-layers` | GPU 加速层数 |
| `-t`, `--threads` | CPU 线程数 |
| `--threads-batch` | 批处理线程数 |
| `-b`, `--batch-size` | 批处理大小 |
| `--ubatch-size` | 物理批处理大小 |
| `--temp` | 采样温度 |
| `--mmproj` | 视觉投影文件路径 |
| `--timeout` | 请求超时（秒） |
| `--sleep-idle-seconds` | 空闲休眠时间（秒） |
| `--tools` | 启用内置工具（如 `all`） |
| `--flash-attention` | Flash Attention 模式（`auto`/`on`/`off`） |
| `--chat-template-kwargs` | 对话模板 JSON 参数 |
| `--no-mmap` | 禁用内存映射 |

## 使用说明

### 首次配置

1. 在左侧 **基础配置** 区域设置 `llama-server` 可执行文件路径
2. 设置模型根目录，点击 **刷新** 扫描 `.gguf` 模型
3. 从下拉列表选择要使用的模型
4. 按需调整上下文长度、GPU 层数、线程数等参数
5. 点击 **保存** 按钮将配置写入 `config.toml`

### 启动服务

1. 确认配置无误后，点击工具栏的 **启动** 按钮
2. 程序会自动保存当前配置并切换到运行控制台视图
3. 右侧实时显示完整命令预览和运行日志
4. 状态指示灯会显示：未运行 → 启动中 → 已就绪 / 启动超时

### 参数说明

界面中大部分参数都支持 **鼠标悬停提示**。将鼠标移动到参数名称或输入框上，即可查看该参数的详细说明。

### 高级参数

右侧 **高级参数** 面板按 Tab 分类：

| Tab | 内容 |
|-----|------|
| **采样** | 温度、Top-K、Top-P、Min-P、重复惩罚、随机种子等 |
| **GPU / MoE** | 主 GPU、分割模式、Flash Attention、缓存类型、MoE 配置 |
| **投机解码** | 投机类型、Draft token 数、Draft 模型路径等 |
| **服务与工具** | 监听地址/端口、超时、空闲休眠、WebUI、Embeddings 开关 |
| **自定义** | 对话模板参数、自定义命令行参数 |

## 项目结构

```
llama service lunch/
├── llama_launcher_backup.py   # 主入口 + LlamaLauncher（mixin 组合）
├── llama一键启动器.bat          # Windows 一键启动脚本
├── config.toml                # 用户配置文件（运行时自动生成）
├── requirements.txt           # Python 依赖清单
├── .gitignore                 # Git 忽略规则
│
├── config/                    # 配置数据包（纯数据，无逻辑）
│   ├── params.py              # 参数元数据（标签、tooltip）
│   ├── colors.py              # 界面配色方案
│   └── defaults.py            # 默认配置字典
│
├── utils/                     # 通用工具（纯函数，无 UI 依赖）
│   ├── toml_io.py             # TOML 序列化
│   └── cli.py                 # 命令行参数解析
│
├── ui/                        # UI 模块
│   ├── widgets.py             # UIWidgetMixin — 通用控件构建器
│   └── views.py               # ViewMixin — 视图布局与 Tab 填充
│
└── core/                      # 核心逻辑模块
    ├── server.py              # ServerMixin — 进程管理、日志、状态监控
    ├── command.py             # CommandMixin — 命令构建、预览、快照
    └── config_manager.py      # ConfigMixin — 配置加载/保存/校验
```

详细架构说明请参阅 [Project Structure.md](file:///d:/llama.cpp/llama%20service%20lunch/Project%20Structure.md)。

## 配置说明

所有用户配置保存在项目根目录的 `config.toml` 中，包括：

- `llama-server` 路径
- 模型根目录和当前选择的模型路径
- 端口、上下文长度、线程数、GPU 层数
- 采样参数（温度、Top-K、Top-P、Min-P 等）
- 投机解码、MoE、缓存类型等高级参数
- 自定义命令行参数
- 窗口尺寸与位置

## 依赖

```text
customtkinter==6.0.0
```

依赖安装在项目本地 `.venv` 中，不会污染系统 Python。

## 常见问题

### 双击后提示缺少 customtkinter

在项目目录运行：

```bat
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

### 启动失败

依次检查：

- `llama-server.exe` 路径是否正确
- 模型文件路径是否正确
- 端口是否被其他程序占用
- 使用的参数是否被当前版本的 `llama-server` 支持

### 配置保存后下次没有恢复

确认程序对项目目录有写入权限，并检查 `config.toml` 是否被其他程序占用或设置为只读。

### 模型下拉框为空

确认模型根目录设置正确，且该目录下包含 `.gguf` 格式的文件。点击 **刷新** 按钮重新扫描。

## 许可证

本项目基于 [MIT License](LICENSE) 开源。

## 贡献

欢迎提交 Issue 和 Pull Request。如有功能建议或问题反馈，请通过 GitHub Issues 联系。

## 致谢

- [ggml-org/llama.cpp](https://github.com/ggml-org/llama.cpp) — 提供 `llama-server` 核心引擎
- [CustomTkinter](https://github.com/Tk-fullstack/CustomTkinter) — 现代化 tkinter UI 框架

## 作者

由 **king0596** 开发并维护。
