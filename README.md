# Llama Server Launcher

一个用于便携启动和管理 `llama-server` 的 Windows 桌面启动器。界面基于 CustomTkinter，支持模型扫描、常用参数配置、高级参数管理、命令预览、运行状态和日志查看。

## 运行要求

- Windows
- Python 3.11 或更高版本
- 可用的 `llama-server.exe`
- GGUF 模型文件

## 首次启动

双击运行：

```bat
llama.bat
```

启动脚本会自动完成以下操作：

1. 在项目目录创建 `.venv` 虚拟环境。
2. 使用 `.venv\Scripts\python.exe` 安装 `requirements.txt` 里的依赖。
3. 使用 `.venv\Scripts\pythonw.exe` 启动 `llama_launcher_backup.py`。

如果依赖下载失败，通常是网络或 pip 源不可用。可以手动运行：

```bat
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## 基本使用

1. 设置 `llama-server` 路径。
2. 设置模型根目录，点击刷新后选择 `.gguf` 模型。
3. 按需调整上下文、GPU 层数、线程、采样等参数。
4. 点击保存配置。
5. 点击启动。

程序会在启动前自动保存当前配置，并在右侧显示完整命令预览和运行日志。

## 配置保存

配置保存在：

```text
config.toml
```

已保存内容包括：

- `llama-server` 路径
- 模型根目录和模型路径
- 端口、上下文、线程、GPU、采样参数
- 投机解码、MoE、缓存类型等高级参数
- 自定义参数
- 窗口尺寸

## 参数说明

大部分参数都支持鼠标悬停说明。将鼠标移动到参数名称或输入框上，即可查看该参数用途。

## 模型目录

默认模型根目录是项目下的：

```text
model
```

也可以在界面中选择其他目录。模型下拉框会显示相对路径，避免不同子目录下同名模型互相混淆。

## 依赖

当前 Python 依赖：

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

检查：

- `llama-server.exe` 路径是否正确。
- 模型路径是否正确。
- 端口是否被占用。
- 参数是否被当前版本的 `llama-server` 支持。

### 配置保存后下次没有恢复

确认程序对项目目录有写入权限，并检查 `config.toml` 是否被其他程序占用。
