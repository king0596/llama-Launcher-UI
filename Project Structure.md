# Project Structure

## 目录结构

```
llama service lunch/
├── llama_launcher_backup.py   主入口 + LlamaLauncher 类（mixin 组合）
├── llama.bat                  Windows 启动脚本（自动创建 .venv 并启动）
├── config.toml                用户配置文件（运行时生成）
├── requirements.txt           Python 依赖清单
├── README.md                  项目说明
├── 千问系列参数.txt             千问模型参数参考
│
├── config/                    配置数据包（纯数据，无逻辑）
│   ├── __init__.py            统一导出 PARAM_CONFIG / COLORS / DEFAULT_CONFIG
│   ├── params.py              llama-server 参数元数据（标签、tooltip 文案）
│   ├── colors.py              界面配色方案
│   └── defaults.py            默认配置字典（首次运行时使用）
│
├── utils/                     通用工具函数（纯函数，无 UI 依赖）
│   ├── __init__.py            统一导出 toml_dump / parse_args
│   ├── toml_io.py             TOML 序列化（轻量实现，无需第三方库）
│   └── cli.py                 命令行参数解析（argparse）
│
├── ui/                        UI 模块
│   ├── __init__.py            统一导出 UIWidgetMixin / ViewMixin
│   ├── widgets.py             UIWidgetMixin — 通用控件构建器
│   └── views.py               ViewMixin — 视图布局与 Tab 填充
│
└── core/                      核心逻辑模块
    ├── __init__.py            统一导出 ServerMixin / CommandMixin / ConfigMixin
    ├── server.py              ServerMixin — 进程生命周期、日志、状态监控
    ├── command.py             CommandMixin — 命令构建、预览、启动快照
    └── config_manager.py      ConfigMixin — 配置加载/保存/校验、模型扫描
```

## 架构说明

项目采用 **mixin 组合模式** 将原本 1600+ 行的单文件拆分为多个职责明确的模块。`LlamaLauncher` 类通过多继承组合所有 mixin，各模块通过 `self` 共享状态，无需额外的通信机制。

```
LlamaLauncher
  ├── UIWidgetMixin      (ui/widgets.py)      — card / add_*_row / tooltip 等控件
  ├── ViewMixin          (ui/views.py)        — 工具栏 / 配置视图 / 运行视图 / Tab
  ├── ServerMixin        (core/server.py)     — start/stop / 日志 / 状态轮询
  ├── CommandMixin       (core/command.py)    — build_command / 预览 / 快照
  └── ConfigMixin        (core/config_manager.py) — load/save / 校验 / 模型扫描
```

主类 `LlamaLauncher`（`llama_launcher_backup.py`）仅保留 `__init__`、`create_variables`、`on_closing` 三个方法，负责初始化和组装。

## 文件详细说明

### `llama_launcher_backup.py`（136 行）

程序主入口。定义 `LlamaLauncher` 类，通过 mixin 组合所有功能。包含：
- `__init__` — 初始化状态、加载配置、扫描模型、创建变量、构建 UI
- `create_variables` — 创建所有 `tk.StringVar` / `tk.BooleanVar` 控件变量
- `on_closing` — 窗口关闭时保存配置并停止服务
- `main()` — 入口函数，创建 CTk 根窗口并启动主循环

### `config/` — 配置数据包

| 文件 | 行数 | 内容 |
|------|------|------|
| `params.py` | 142 | `PARAM_CONFIG` 字典：34 个参数的标签和 tooltip 文案 |
| `colors.py` | 29 | `COLORS` 字典：25 个配色常量 |
| `defaults.py` | 58 | `DEFAULT_CONFIG` 字典：49 个默认配置项 |

这些文件是纯数据，修改参数文案或配色时只需编辑对应文件，不影响任何逻辑代码。

### `utils/` — 通用工具

| 文件 | 行数 | 内容 |
|------|------|------|
| `toml_io.py` | 19 | `toml_dump()` — 将字典写入 TOML 格式文件 |
| `cli.py` | 38 | `parse_args()` — argparse 命令行参数定义 |

### `ui/` — UI 模块

#### `ui/widgets.py`（275 行）— `UIWidgetMixin`

通用控件构建器，提供可复用的 UI 组件工厂方法：
- `card()` — 带标题的卡片容器
- `add_input_row()` / `add_dropdown_row()` / `add_switch_row()` / `add_path_row()` — 表格行构建
- `add_input_cell()` / `add_dropdown_cell()` / `add_switch_cell()` — 网格单元格构建
- `add_metric()` — 快速参数卡片
- `make_scroll_frame()` / `row_col()` / `_section_header()` — 布局辅助
- `create_tooltip()` / `_destroy_active_tooltip()` — Tooltip 系统（带延迟、防残留）

#### `ui/views.py`（394 行）— `ViewMixin`

视图布局，组装整体界面结构：
- `build_ui()` — 顶层框架搭建
- `build_toolbar()` — 顶部工具栏（模型选择、端口、启动/停止按钮）
- `build_config_view()` — 配置视图（左侧边栏 + 右侧高级参数）
- `build_dashboard()` / `build_config_preview()` — 左侧基础配置和命令预览
- `build_advanced_panel()` — 右侧高级参数 Tab 容器
- `fill_sampling_tab()` / `fill_gpu_tab()` / `fill_spec_tab()` / `fill_service_tab()` / `fill_custom_tab()` — 各 Tab 内容填充
- `build_status_panel()` — 运行状态面板
- `show_config_view()` / `show_runtime_view()` — 视图切换

### `core/` — 核心逻辑

#### `core/server.py`（252 行）— `ServerMixin`

服务进程管理：
- `start_server()` / `stop_server()` — 启动/停止 llama-server 子进程
- `read_output()` / `update_log_display()` / `clear_log()` — 日志读取与显示
- `check_server_ready()` — 端口探测，检测服务是否就绪
- `set_server_status()` / `update_gpu_info()` — 状态轮询与 UI 更新
- `update_runtime_summary()` — 运行时摘要刷新
- `start_openclaw()` / `stop_openclaw()` — OpenClaw 网关管理
- `open_webui()` — 打开浏览器访问 WebUI

#### `core/command.py`（338 行）— `CommandMixin`

命令构建与预览：
- `build_command()` — 从 UI 变量构建 llama-server 命令行参数列表
- `format_command()` — 格式化命令为字符串（区分 Windows/Unix）
- `build_launch_snapshot()` — 生成启动参数快照文本
- `show_launch_snapshot()` — 弹窗显示启动参数
- `setup_variable_traces()` / `schedule_command_preview()` / `update_command_preview()` — 变量变更监听与命令预览实时更新

#### `core/config_manager.py`（327 行）— `ConfigMixin`

配置管理：
- `load_config()` / `save_config()` / `write_config_file()` — 配置文件读写
- `load_config_to_ui()` / `collect_config_from_ui()` — 配置 ↔ UI 双向同步
- `parse_int_field()` / `parse_float_field()` — 输入校验
- `scan_models()` / `refresh_models()` / `model_display_for_path()` — 模型文件扫描
- `apply_cli_args()` — 应用命令行参数覆盖配置
- `browse_model_root()` / `browse_server()` / `browse_model()` / `browse_mmproj()` / `browse_model_draft()` — 文件浏览对话框

## 启动流程

```
llama.bat
  └── python llama_launcher_backup.py
        └── main()
              └── LlamaLauncher(root)
                    ├── load_config()          ← ConfigMixin
                    ├── scan_models()          ← ConfigMixin
                    ├── create_variables()     ← 主类
                    ├── build_ui()             ← ViewMixin
                    │     ├── build_toolbar()
                    │     ├── build_config_view()
                    │     │     ├── build_dashboard()       ← ViewMixin (使用 UIWidgetMixin)
                    │     │     ├── build_config_preview()
                    │     │     └── build_advanced_panel()
                    │     │           └── fill_*_tab()
                    │     └── build_status_panel()
                    ├── load_config_to_ui()    ← ConfigMixin
                    ├── apply_cli_args()       ← ConfigMixin
                    └── setup_variable_traces() ← CommandMixin
```

## 修改指南

| 需求 | 编辑文件 |
|------|----------|
| 修改参数标签或 tooltip | `config/params.py` |
| 修改界面配色 | `config/colors.py` |
| 修改默认配置值 | `config/defaults.py` |
| 修改命令行参数 | `utils/cli.py` |
| 修改控件样式或 tooltip 行为 | `ui/widgets.py` |
| 修改界面布局或 Tab 内容 | `ui/views.py` |
| 修改服务启动/停止逻辑 | `core/server.py` |
| 修改命令构建逻辑 | `core/command.py` |
| 修改配置加载/保存/校验 | `core/config_manager.py` |
| 修改初始化流程 | `llama_launcher_backup.py` |
