# Project Structure

## 目录

```text
llama service lunch/
├─ llama_launcher_backup.py      # 主入口，组装 LlamaLauncher 和运行时补丁
├─ llama一键启动器.bat           # Windows 一键启动脚本
├─ requirements.txt              # Python 依赖
├─ config.toml                   # 用户配置，运行时读写
├─ README.md                     # 项目说明
├─ 千问系列参数.txt              # 模型参数参考
├─ workspace/                    # llama-server 工作目录和工具输出目录，已忽略
│
├─ config/
│  ├─ __init__.py
│  ├─ colors.py                  # UI 配色
│  ├─ defaults.py                # 默认配置
│  └─ params.py                  # 参数标签和 tooltip 元数据
│
├─ utils/
│  ├─ __init__.py
│  ├─ cli.py                     # 命令行参数解析
│  └─ toml_io.py                 # TOML 写入工具
│
├─ ui/
│  ├─ __init__.py
│  ├─ widgets.py                 # 通用控件构建 helper
│  └─ views.py                   # 主界面、配置页、运行页和高级参数 Tab
│
└─ core/
   ├─ __init__.py
   ├─ command.py                 # 命令构建、命令预览、启动快照
   ├─ config_manager.py          # 配置读写、校验、模型扫描
   ├─ monitor.py                 # 硬件监控、Token 统计、异常捕获
   └─ server.py                  # server 进程、日志、状态、WebUI
```

## 架构

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

## 启动流程

```text
llama一键启动器.bat
└─ .venv\Scripts\pythonw.exe llama_launcher_backup.py
   └─ main()
      ├─ patch_customtkinter_runtime()
      ├─ root = tk.Tk()
      └─ LlamaLauncher(root)
         ├─ load_config()
         ├─ scan_models()
         ├─ create_variables()
         ├─ init_monitor()
         ├─ build_ui()
         ├─ load_config_to_ui()
         ├─ apply_cli_args()
         ├─ setup_variable_traces()
         └─ update_command_preview()
```

## UI 说明

- 主窗口使用原生 `tk.Tk()`。
- 页面控件主要使用 CustomTkinter。
- 高级参数面板默认可见。
- 运行控制台延迟创建：只有启动服务或切换到运行视图时才构建日志、监控和异常捕获控件。
- 命令预览、运行日志、异常捕获使用原生 `tk.Text`，减少 CTk Canvas 数量。
- 高级参数 Tabview 使用固定高度并关闭几何传播，避免切换 Tab 时因内容高度不同产生抖动。

## 模块职责

### `llama_launcher_backup.py`

- 导入依赖和 mixin。
- `patch_customtkinter_runtime()`：禁用 CTk 外观/DPI 高频轮询，修正 CTk 6.0.0 的窗口尺寸阻塞标记，关闭 CTk Windows 标题栏处理。
- `LlamaLauncher.__init__()`：创建共享状态、日志队列、配置路径、模型路径和 UI。
- `create_variables()`：创建所有 Tk 变量。
- `on_closing()`：保存窗口状态、停止监控和 server 进程。

### `ui/widgets.py`

- `card()`：统一卡片容器。
- `add_input_row()` / `add_dropdown_row()` / `add_switch_row()` / `add_path_row()`：表单行构建。
- `add_metric()`：基础参数卡片。
- `make_scroll_frame()`：高级参数 Tab 内部容器。当前使用普通 `CTkFrame`，避免 `CTkScrollableFrame` 的全局滚轮绑定和额外 Configure 事件。
- `create_tooltip()`：延迟 tooltip。

### `ui/views.py`

- `build_ui()`：顶层布局。
- `build_toolbar()`：顶部模型选择、端口、启动、停止、保存和 WebUI。
- `build_config_view()`：左侧基础配置和右侧高级参数。
- `build_advanced_panel()`：高级参数 Tab。
- `show_runtime_view()`：首次进入运行页时懒加载运行控制台。
- `build_runtime_view()` / `build_status_panel()`：运行状态、日志和控制台。

### `core/server.py`

- `start_server()` / `stop_server()`：管理 llama-server 子进程。
- `read_output()` / `update_log_display()`：读取并分批刷新日志。
- `set_server_status()` / `update_gpu_info()`：状态显示和 PID 轮询。轮询使用 `gpu_update_after_id` 去重，停止时取消残留回调。
- `check_server_ready()`：端口就绪检测。
- `open_webui()`：打开 server WebUI。

### `core/command.py`

- `build_command()`：从 UI 变量构建命令列表。
- `format_command()`：格式化命令字符串。
- `setup_variable_traces()`：监听参数变化。
- `update_command_preview()`：刷新命令预览。
- `build_launch_snapshot()` / `show_launch_snapshot()`：启动参数快照。

### `core/config_manager.py`

- `load_config()` / `save_config()` / `write_config_file()`：配置读写。
- `load_config_to_ui()` / `collect_config_from_ui()`：配置和 UI 双向同步。
- `scan_models()` / `refresh_models()`：模型扫描。
- `browse_*()`：文件选择。
- `apply_cli_args()`：命令行参数覆盖。

### `core/monitor.py`

- NVML / psutil 初始化和释放。
- 硬件监控。
- `/metrics` 和 `/slots` Token 统计。
- 日志异常关键字扫描和异常面板渲染。

## 修改指南

| 需求 | 主要文件 |
| --- | --- |
| 新增 llama-server 参数 | `config/params.py`, `llama_launcher_backup.py`, `core/command.py`, `core/config_manager.py`, `ui/views.py` |
| 修改 UI 布局 | `ui/views.py` |
| 修改通用控件样式 | `ui/widgets.py`, `config/colors.py` |
| 修改启动/停止逻辑 | `core/server.py` |
| 修改监控或统计 | `core/monitor.py` |
| 修改配置格式 | `config/defaults.py`, `core/config_manager.py` |
| 修改启动脚本 | `llama一键启动器.bat` |

## 性能注意事项

- 不要在主界面一次性创建大量 `CTkTextbox` 或 `CTkScrollableFrame`。
- 不要在未必要时增加 `after()` 高频轮询。
- 新增周期任务时需要保存 `after_id`，停止服务或关闭窗口时取消。
- 如果新增运行页控件，优先放在运行页懒加载流程中，而不是 `build_ui()` 首屏创建。
