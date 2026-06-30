import tkinter as tk
import queue

try:
    import customtkinter as ctk
except ImportError:
    ctk = None

from config import COLORS, PARAM_CONFIG


class ViewMixin:
    """视图布局 mixin：工具栏、配置视图、运行视图、Tab 填充。"""

    def build_ui(self):
        if ctk is None:
            raise RuntimeError("缺少 customtkinter，请先运行: python -m pip install -r requirements.txt")

        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")
        self.root.geometry(self.config.get("window_geometry", "1280x820"))
        self.root.minsize(1100, 700)
        C = self.COLORS
        self.root.configure(fg_color=C["bg"])

        shell = ctk.CTkFrame(self.root, fg_color=C["bg"], corner_radius=0)
        shell.pack(fill=tk.BOTH, expand=True)
        shell.grid_columnconfigure(0, weight=1)
        shell.grid_rowconfigure(1, weight=1)

        self.build_toolbar(shell)

        content = ctk.CTkFrame(shell, fg_color="transparent")
        content.grid(row=1, column=0, sticky="nsew", padx=12, pady=8)
        self.content = content
        content.grid_columnconfigure(0, weight=1)
        content.grid_rowconfigure(0, weight=1)

        # ---- 配置视图（左右分栏）----
        self.config_view = ctk.CTkFrame(content, fg_color="transparent")
        self.config_view.grid_columnconfigure(0, weight=3, minsize=420)
        self.config_view.grid_columnconfigure(1, weight=2, minsize=300)
        self.config_view.grid_rowconfigure(0, weight=1)

        # ---- 运行视图（单列）----
        self.runtime_view = ctk.CTkFrame(content, fg_color="transparent")
        self.runtime_view.grid_columnconfigure(0, weight=1)
        self.runtime_view.grid_rowconfigure(1, weight=1)

        self.build_config_view(self.config_view)
        self.build_runtime_view(self.runtime_view)
        self.show_config_view()

    # ---- 工具栏 ----
    def build_toolbar(self, parent):
        C = self.COLORS
        bar = ctk.CTkFrame(parent, height=56, fg_color=C["card"])
        bar.grid(row=0, column=0, sticky="ew", pady=(6, 8))
        bar.grid_columnconfigure(2, weight=1)

        # 左侧标题
        ctk.CTkLabel(
            bar, text="Llama Launcher",
            font=("Microsoft YaHei UI", 16, "bold"),
            text_color=C["text_primary"],
        ).grid(row=0, column=0, sticky="w", padx=(18, 0), pady=8)

        # 中间模型选择 + 端口
        mid = ctk.CTkFrame(bar, fg_color="transparent")
        mid.grid(row=0, column=2, sticky="ew", padx=16)
        mid.grid_columnconfigure(0, weight=1)

        self.model_combo = ctk.CTkComboBox(
            mid, variable=self.model_combo_var,
            values=self.models or ["未扫描到模型"],
            command=self.on_model_select, height=32, corner_radius=8,
            border_color=C["input_border"], button_color=C["tab_bg"],
            button_hover_color=C["card_border"], text_color=C["text_primary"],
            font=("Microsoft YaHei UI", 11),
        )
        self.model_combo.grid(row=0, column=0, sticky="ew", padx=(0, 8))

        port_lbl = ctk.CTkLabel(mid, text="端口:", font=("Microsoft YaHei UI", 11), text_color=C["text_secondary"])
        port_lbl.grid(row=0, column=1, sticky="e", padx=(0, 4))
        self.port_entry = ctk.CTkEntry(
            mid, textvariable=self.port_var, width=72, height=30,
            corner_radius=8, placeholder_text="8080",
            border_color=C["input_border"], font=("Consolas", 11),
        )
        self.port_entry.grid(row=0, column=2)

        # 右侧操作按钮
        acts = ctk.CTkFrame(bar, fg_color="transparent")
        acts.grid(row=0, column=3, sticky="e", padx=(12, 18))

        self.start_btn = ctk.CTkButton(
            acts, text="▶  启动", width=90, height=34, corner_radius=8,
            command=self.start_server, fg_color=C["primary"], hover_color=C["primary_hover"],
            font=("Microsoft YaHei UI", 12, "bold"),
        )
        self.start_btn.grid(row=0, column=0, padx=3)

        self.stop_btn = ctk.CTkButton(
            acts, text="■ 停止", width=90, height=34, corner_radius=8,
            command=self.stop_server, state=tk.DISABLED,
            fg_color=C["danger"], hover_color=C["danger_hover"],
            font=("Microsoft YaHei UI", 12, "bold"),
        )
        self.stop_btn.grid(row=0, column=1, padx=3)

        ctk.CTkButton(
            acts, text="💾 保存", width=80, height=34, corner_radius=8,
            command=self.save_config, fg_color=C["tab_bg"], hover_color=C["card_border"],
            text_color=C["text_primary"], font=("Microsoft YaHei UI", 12),
        ).grid(row=0, column=2, padx=3)

        ctk.CTkButton(
            acts, text="🌐 WebUI", width=80, height=34, corner_radius=8,
            command=self.open_webui, fg_color=C["tab_bg"], hover_color=C["card_border"],
            text_color=C["text_primary"], font=("Microsoft YaHei UI", 12),
        ).grid(row=0, column=3, padx=3)

    def show_config_view(self):
        self.runtime_view.grid_remove()
        self.config_view.grid(row=0, column=0, sticky="nsew")
        if hasattr(self, "mode_hint_label"):
            self.mode_hint_label.configure(text="配置模式：调整参数后启动服务")

    def show_runtime_view(self):
        self.config_view.grid_remove()
        self.runtime_view.grid(row=0, column=0, sticky="nsew")
        if hasattr(self, "mode_hint_label"):
            self.mode_hint_label.configure(text="运行模式：参数已锁定，重点查看日志和状态")
        self.update_runtime_summary()

    def build_config_view(self, parent):
        C = self.COLORS
        # 左侧边栏（滚动）
        sidebar = ctk.CTkScrollableFrame(parent, fg_color="transparent")
        sidebar.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        sidebar.grid_columnconfigure(0, weight=1)

        # 右侧高级参数
        advanced = ctk.CTkFrame(parent, fg_color="transparent")
        advanced.grid(row=0, column=1, sticky="nsew")
        advanced.grid_columnconfigure(0, weight=1)
        advanced.grid_rowconfigure(0, weight=1)

        self.build_dashboard(sidebar)
        self.build_config_preview(sidebar)
        self.build_advanced_panel(advanced)

    def build_runtime_view(self, parent):
        C = self.COLORS
        # 运行视图：左侧监控侧边栏 + 右侧状态/控制台
        parent.grid_columnconfigure(0, weight=0, minsize=300)
        parent.grid_columnconfigure(1, weight=3, minsize=400)
        parent.grid_rowconfigure(0, weight=1)

        sidebar = ctk.CTkScrollableFrame(
            parent, fg_color="transparent",
            scrollbar_fg_color=C["tab_bg"],
            scrollbar_button_color=C["card_border"],
            scrollbar_button_hover_color=C["text_hint"],
        )
        sidebar.grid(row=0, column=0, sticky="nsew", padx=(0, 6))
        sidebar.grid_columnconfigure(0, weight=1)

        main = ctk.CTkFrame(parent, fg_color="transparent")
        main.grid(row=0, column=1, sticky="nsew")
        main.grid_columnconfigure(0, weight=1)
        main.grid_rowconfigure(1, weight=1)

        self.build_monitor_sidebar(sidebar)
        self.build_status_panel(main)

    def build_dashboard(self, parent):
        C = self.COLORS
        dash = self.card(parent, "基础配置")
        dash.grid(row=0, column=0, sticky="nsew", pady=(8, 6))
        dash.grid_columnconfigure(1, weight=1)

        row = 2
        row = self.add_path_row(dash, row, "模型根目录", self.model_root_var, self.browse_model_root, "浏览", self.refresh_models)
        row = self.add_path_row(dash, row, "模型文件", self.model_path_var, self.browse_model, "浏览")
        row = self.add_path_row(dash, row, "llama-server", self.server_path_var, self.browse_server, "浏览")
        row = self.add_path_row(dash, row, "视觉投影", self.mmproj_path_var, self.browse_mmproj, "浏览")
        row = self.add_switch_row(dash, row, "启用视觉模型", self.mmproj_enabled_var)

        # ---- 快速参数卡片组 ----
        metrics = ctk.CTkFrame(dash, fg_color=C["tab_bg"], corner_radius=8)
        metrics.grid(row=row, column=0, columnspan=3, sticky="ew", padx=12, pady=(8, 12))
        for col in range(4):
            metrics.grid_columnconfigure(col, weight=1)
        self.add_metric(metrics, 0, "📄 上下文", self.ctx_size_var)
        self.add_metric(metrics, 1, "🎮 GPU层", self.n_gpu_layers_var)
        self.add_metric(metrics, 2, "📦 批处理", self.batch_size_var)
        self.add_metric(metrics, 3, "⚡ 线程", self.threads_var)

    def build_config_preview(self, parent):
        C = self.COLORS
        preview = self.card(parent, "命令预览")
        preview.grid(row=1, column=0, sticky="nsew", pady=(6, 8))
        preview.grid_columnconfigure(0, weight=1)
        preview.grid_rowconfigure(1, weight=1)

        self.config_command_preview_text = ctk.CTkTextbox(
            preview, height=140, wrap=tk.WORD,
            font=("Consolas", 10),
            fg_color=C["dark_bg"], text_color=C["dark_text"],
            corner_radius=8,
        )
        self.config_command_preview_text.grid(row=1, column=0, sticky="nsew", padx=12, pady=(0, 10))
        self.config_command_preview_text.configure(state=tk.DISABLED)

        ctk.CTkLabel(
            preview,
            text="启动后自动切换到运行控制台视图。",
            text_color=C["text_hint"], font=("Microsoft YaHei UI", 11),
        ).grid(row=2, column=0, sticky="w", padx=14, pady=(0, 10))

    def build_advanced_panel(self, parent):
        C = self.COLORS
        panel = self.card(parent, "高级参数")
        panel.grid(row=0, column=0, sticky="nsew")
        panel.grid_columnconfigure(0, weight=1)
        panel.grid_rowconfigure(1, weight=1)

        tabs = ctk.CTkTabview(
            panel,
            fg_color=C["card"], border_width=1, border_color=C["card_border"],
            segmented_button_fg_color=C["tab_bg"],
            segmented_button_selected_color=C["primary"],
            segmented_button_selected_hover_color=C["primary_hover"],
        )
        for name in ["采样", "GPU / MoE", "投机解码", "服务与工具", "自定义"]:
            tabs.add(name)
            tabs.tab(name).grid_columnconfigure(0, weight=1)

        tabs.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        self.fill_sampling_tab(tabs.tab("采样"))
        self.fill_gpu_tab(tabs.tab("GPU / MoE"))
        self.fill_spec_tab(tabs.tab("投机解码"))
        self.fill_service_tab(tabs.tab("服务与工具"))
        self.fill_custom_tab(tabs.tab("自定义"))

    def build_status_panel(self, parent):
        C = self.COLORS
        parent.grid_rowconfigure(1, weight=1)

        # ---- 状态卡片 ----
        status = self.card(parent, "运行状态")
        status.grid(row=0, column=0, sticky="ew", pady=(8, 6))
        status.grid_columnconfigure(1, weight=1)

        self.status_pill = ctk.CTkLabel(
            status, text="未运行", width=100, height=28, corner_radius=14,
            fg_color=C["danger_bg"], text_color=C["danger_text"],
            font=("Microsoft YaHei UI", 12, "bold"),
        )
        self.status_pill.grid(row=1, column=0, sticky="w", padx=14, pady=(0, 8))

        pid_lbl = ctk.CTkLabel(status, text="PID:", font=("Microsoft YaHei UI", 11), text_color=C["text_secondary"])
        pid_lbl.grid(row=1, column=1, sticky="e", padx=(0, 6), pady=(0, 8))

        pid_val = ctk.CTkLabel(
            status, textvariable=self.pid_var,
            font=("Consolas", 12, "bold"), text_color=C["text_primary"],
        )
        pid_val.grid(row=1, column=2, sticky="e", padx=(0, 14), pady=(0, 8))

        self.mode_hint_label = ctk.CTkLabel(
            status, text="配置模式：调整参数后启动服务",
            text_color=C["text_hint"], font=("Microsoft YaHei UI", 11),
        )
        self.mode_hint_label.grid(row=2, column=0, columnspan=3, sticky="w", padx=14, pady=(0, 6))

        # ---- 运行时摘要 ----
        summary = ctk.CTkFrame(status, fg_color=C["tab_bg"], corner_radius=8)
        summary.grid(row=3, column=0, columnspan=3, sticky="ew", padx=14, pady=(0, 10))
        summary.grid_columnconfigure(1, weight=1)

        self.runtime_model_var = tk.StringVar(value="-")
        self.runtime_url_var = tk.StringVar(value="-")
        self.runtime_started_var = tk.StringVar(value="-")
        self.add_summary_row(summary, 0, "模型", self.runtime_model_var)
        self.add_summary_row(summary, 1, "地址", self.runtime_url_var)
        self.add_summary_row(summary, 2, "启动时间", self.runtime_started_var)

        ctk.CTkButton(
            status, text="📋 查看启动参数", width=120, height=28, corner_radius=8,
            command=self.show_launch_snapshot,
            fg_color=C["tab_bg"], hover_color=C["card_border"],
            text_color=C["text_primary"], font=("Microsoft YaHei UI", 11),
        ).grid(row=4, column=0, columnspan=3, sticky="w", padx=14, pady=(0, 10))

        # ---- 控制台卡片 ----
        logs = self.card(parent, "📟 控制台")
        self.logs_card = logs
        logs.grid(row=1, column=0, sticky="nsew")
        logs.grid_columnconfigure(0, weight=1)
        logs.grid_rowconfigure(2, weight=1)

        self.command_preview_text = ctk.CTkTextbox(
            logs, height=80, wrap=tk.WORD, font=("Consolas", 10),
            fg_color=C["dark_bg"], text_color=C["dark_text"], corner_radius=8,
        )
        self.command_preview_text.grid(row=1, column=0, sticky="ew", padx=12, pady=(0, 6))
        self.command_preview_text.configure(state=tk.DISABLED)

        self.log_text = ctk.CTkTextbox(
            logs, wrap=tk.WORD, font=("Consolas", 11),
            fg_color=C["dark_bg"], text_color=C["success"], corner_radius=8,
        )
        self.log_text.grid(row=2, column=0, sticky="nsew", padx=12, pady=(0, 6))
        self.log_text.configure(state=tk.DISABLED)

        btn_bar = ctk.CTkFrame(logs, fg_color="transparent")
        btn_bar.grid(row=3, column=0, sticky="ew", padx=12, pady=(0, 10))

        ctk.CTkButton(
            btn_bar, text="🗑 清空日志", width=90, height=28, corner_radius=8,
            command=self.clear_log, fg_color=C["tab_bg"], hover_color=C["card_border"],
            text_color=C["text_primary"], font=("Microsoft YaHei UI", 11),
        ).pack(side=tk.LEFT)

        self.log_queue = queue.Queue()
        self.log_thread = None
        self.running = False
        self.max_log_lines = 999999
        self.log_lines = []
        self.set_server_status("未运行")
        self.update_gpu_info()

    def add_summary_row(self, parent, row, label, var):
        C = self.COLORS
        ctk.CTkLabel(
            parent, text=label, text_color=C["text_hint"],
            font=("Microsoft YaHei UI", 11), width=60, anchor="w",
        ).grid(row=row, column=0, sticky="w", padx=(10, 8), pady=2)
        ctk.CTkLabel(
            parent, textvariable=var, text_color=C["text_primary"],
            font=("Microsoft YaHei UI", 11), anchor="w",
        ).grid(row=row, column=1, sticky="ew", padx=(0, 10), pady=2)

    # ---- Tab 填充 ----
    def fill_sampling_tab(self, parent):
        frame = self.make_scroll_frame(parent)
        row = 0
        cfg = PARAM_CONFIG
        self._section_header(frame, row, "🎯 采样参数")
        row += 1
        for key in ["temp", "top_k", "top_p", "min_p", "presence_penalty",
                     "n_predict", "repeat_penalty", "repeat_last_n", "seed"]:
            row = self.add_input_row(frame, row, cfg[key]["label"], getattr(self, f"{key}_var"), cfg[key]["tooltip"])

    def fill_gpu_tab(self, parent):
        frame = self.make_scroll_frame(parent)
        row = 0
        cfg = PARAM_CONFIG
        self._section_header(frame, row, "🖥 GPU 配置")
        row += 1
        row = self.add_input_row(frame, row, cfg["main_gpu"]["label"], self.main_gpu_var, cfg["main_gpu"]["tooltip"])
        row = self.add_dropdown_row(frame, row, cfg["split_mode"]["label"], self.split_mode_var, ["", "none", "layer", "row", "tensor"], cfg["split_mode"]["tooltip"])
        row = self.add_input_row(frame, row, cfg["tensor_split"]["label"], self.tensor_split_var, cfg["tensor_split"]["tooltip"])
        row = self.add_dropdown_row(frame, row, cfg["flash_attn"]["label"], self.flash_attn_var, ["auto", "on", "off"], cfg["flash_attn"]["tooltip"])
        cache_values = ["", "f16", "f32", "bf16", "q8_0", "q4_0", "q4_1", "iq4_nl", "q5_0", "q5_1", "turbo4", "turbo3_tcq", "turbo3", "turbo2_tcq", "turbo2"]
        row = self.add_dropdown_row(frame, row, cfg["cache_type_k"]["label"], self.cache_type_k_var, cache_values, cfg["cache_type_k"]["tooltip"])
        row = self.add_dropdown_row(frame, row, cfg["cache_type_v"]["label"], self.cache_type_v_var, cache_values, cfg["cache_type_v"]["tooltip"])
        self._section_header(frame, row, "🔧 内存 / MoE")
        row += 1
        row = self.add_switch_row(frame, row, cfg["mlock"]["label"], self.mlock_var, cfg["mlock"]["tooltip"])
        row = self.add_switch_row(frame, row, cfg["cpu_moe"]["label"], self.cpu_moe_var, cfg["cpu_moe"]["tooltip"])
        row = self.add_input_row(frame, row, cfg["n_cpu_moe"]["label"], self.n_cpu_moe_var, cfg["n_cpu_moe"]["tooltip"])
        self.add_input_row(frame, row, "MoE专家数量", self.moe_expert_count_var, "MoE专家数量，-1表示使用默认或自动配置")

    def fill_spec_tab(self, parent):
        frame = self.make_scroll_frame(parent)
        row = 0
        cfg = PARAM_CONFIG
        row = self.add_dropdown_row(frame, row, cfg["spec_type"]["label"], self.spec_type_var,
            ["", "none", "draft-simple", "draft-eagle3", "draft-mtp", "ngram-simple", "ngram-map-k", "ngram-map-k4v", "ngram-mod", "ngram-cache"],
            cfg["spec_type"]["tooltip"])
        row = self.add_input_row(frame, row, cfg["spec_draft_n_max"]["label"], self.spec_draft_n_max_var, cfg["spec_draft_n_max"]["tooltip"])
        row = self.add_input_row(frame, row, cfg["spec_draft_p_min"]["label"], self.spec_draft_p_min_var, cfg["spec_draft_p_min"]["tooltip"])
        row = self.add_input_row(frame, row, cfg["n_gpu_layers_draft"]["label"], self.n_gpu_layers_draft_var, cfg["n_gpu_layers_draft"]["tooltip"])
        self.add_path_row(frame, row, cfg["model_draft"]["label"], self.model_draft_var, self.browse_model_draft, "浏览", None, cfg["model_draft"]["tooltip"])

    def fill_service_tab(self, parent):
        frame = self.make_scroll_frame(parent)
        row = 0
        cfg = PARAM_CONFIG
        self._section_header(frame, row, "⚙️ 服务参数")
        row += 1
        for key in ["host", "ctx_size", "n_gpu_layers", "batch_size", "ubatch_size",
                     "threads", "threads_batch", "timeout", "sleep_idle_seconds", "tools"]:
            row = self.add_input_row(frame, row, cfg[key]["label"], getattr(self, f"{key}_var"), cfg[key]["tooltip"])
        row = self.add_input_row(frame, row, "并发槽位数 (-np, --n-parallel)", self.n_parallel_var, "并发处理的请求槽位数量，-1表示使用默认值")
        row = self.add_input_row(frame, row, "日志级别 (--log-verbosity)", self.log_verbosity_var, "llama-server日志详细程度，数值越高输出越详细")
        self._section_header(frame, row, "🔌 功能开关")
        row += 1
        row = self.add_switch_row(frame, row, "详细日志", self.verbose_var, "启动时添加 --verbose，输出更详细的运行信息")
        row = self.add_switch_row(frame, row, "启用 WebUI", self.webui_var, "启动 llama-server 自带 WebUI")
        self.add_switch_row(frame, row, "启用 Embeddings", self.embeddings_var, "启用 embeddings 接口能力")

    def fill_custom_tab(self, parent):
        frame = self.make_scroll_frame(parent)
        row = 0
        row = self.add_input_row(frame, row, "对话模板 (--chat-template-kwargs)", self.chat_template_var, "JSON格式的对话模板参数，例如开启或保留思考内容")
        row = self.add_input_row(frame, row, "自定义参数", self.custom_args_var, "直接附加到 llama-server 命令末尾的高级参数，按命令行格式填写")
        C = self.COLORS
        ctk.CTkLabel(
            frame, text="示例: --no-kv-offload -ngl 20 --cont-batching",
            text_color=C["text_hint"], font=("Microsoft YaHei UI", 11),
        ).grid(row=row, column=0, columnspan=3, sticky="w", padx=14, pady=(2, 10))
