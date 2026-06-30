import tkinter as tk
import sys
import subprocess
import shlex

try:
    import customtkinter as ctk
except ImportError:
    ctk = None

from config import COLORS


class CommandMixin:
    """命令构建 mixin：命令预览、启动快照、变量追踪。"""

    def setup_variable_traces(self):
        names = [
            "model_root_var", "model_combo_var", "model_path_var", "mmproj_path_var",
            "mmproj_enabled_var", "server_path_var", "host_var", "port_var",
            "ctx_size_var", "threads_var", "threads_batch_var", "n_predict_var",
            "n_gpu_layers_var", "batch_size_var", "ubatch_size_var", "temp_var",
            "top_k_var", "top_p_var", "min_p_var", "presence_penalty_var",
            "timeout_var", "sleep_idle_seconds_var", "n_parallel_var", "tools_var",
            "chat_template_var", "repeat_penalty_var", "repeat_last_n_var", "seed_var",
            "main_gpu_var", "split_mode_var", "tensor_split_var", "cpu_moe_var",
            "n_cpu_moe_var", "moe_expert_count_var", "spec_draft_n_max_var",
            "spec_draft_p_min_var", "spec_type_var", "n_gpu_layers_draft_var",
            "model_draft_var", "flash_attn_var", "mlock_var", "cache_type_k_var",
            "cache_type_v_var", "verbose_var", "webui_var", "embeddings_var",
            "log_verbosity_var", "custom_args_var",
        ]
        for name in names:
            var = getattr(self, name, None)
            if var is not None:
                var.trace_add("write", self.schedule_command_preview)

    def schedule_command_preview(self, *args):
        if self.command_update_after_id:
            self.root.after_cancel(self.command_update_after_id)
        self.command_update_after_id = self.root.after(250, self.update_command_preview)

    def format_command(self, cmd):
        if sys.platform == "win32":
            return subprocess.list2cmdline(cmd)
        return shlex.join(cmd)

    def build_command(self):
        cmd = []
        server_path = self.server_path_var.get().strip()
        cmd.append(server_path if server_path else "llama-server")

        model = self.model_path_var.get().strip()
        if model:
            cmd.extend(["-m", model])

        mmproj = self.mmproj_path_var.get().strip()
        if mmproj and self.mmproj_enabled_var.get():
            cmd.extend(["--mmproj", mmproj])

        cmd.extend(["--host", self.host_var.get().strip()])
        cmd.extend(["--port", self.port_var.get().strip()])

        for ui_val, flag in [
            (self.ctx_size_var.get().strip(), "-c"),
            (self.threads_var.get().strip(), "-t"),
            (self.threads_batch_var.get().strip(), "--threads-batch"),
            (self.n_predict_var.get().strip(), "-n"),
            (self.n_gpu_layers_var.get().strip(), "-ngl"),
            (self.batch_size_var.get().strip(), "-b"),
            (self.ubatch_size_var.get().strip(), "--ubatch-size"),
        ]:
            if ui_val:
                cmd.extend([flag, ui_val])

        for ui_val, flag in [
            (self.temp_var.get().strip(), "--temp"),
            (self.top_k_var.get().strip(), "--top-k"),
            (self.top_p_var.get().strip(), "--top-p"),
            (self.min_p_var.get().strip(), "--min-p"),
            (self.presence_penalty_var.get().strip(), "--presence-penalty"),
            (self.repeat_penalty_var.get().strip(), "--repeat-penalty"),
            (self.repeat_last_n_var.get().strip(), "--repeat-last-n"),
            (self.seed_var.get().strip(), "-s"),
           (self.timeout_var.get().strip(), "--timeout"),
            (self.sleep_idle_seconds_var.get().strip(), "--sleep-idle-seconds"),
            (self.n_parallel_var.get().strip(), "-np"),
            (self.tools_var.get().strip(), "--tools"),
        ]:
            if ui_val:
                cmd.extend([flag, ui_val])

        main_gpu = self.main_gpu_var.get().strip()
        if main_gpu and main_gpu != "0":
            cmd.extend(["--main-gpu", main_gpu])

        split_mode = self.split_mode_var.get().strip()
        if split_mode:
            cmd.extend(["--split-mode", split_mode])

        tensor_split = self.tensor_split_var.get().strip()
        if tensor_split:
            cmd.extend(["--tensor-split", tensor_split])

        if self.cpu_moe_var.get():
            cmd.append("--cpu-moe")

        n_cpu_moe = self.n_cpu_moe_var.get().strip()
        if n_cpu_moe and n_cpu_moe != "0":
            cmd.extend(["--n-cpu-moe", n_cpu_moe])


        spec_type = self.spec_type_var.get().strip()
        if spec_type and spec_type != "none":
            cmd.extend(["--spec-type", spec_type])

        spec_draft_n_max = self.spec_draft_n_max_var.get().strip()
        if spec_draft_n_max and spec_draft_n_max != "0":
            cmd.extend(["--spec-draft-n-max", spec_draft_n_max])

        spec_draft_p_min = self.spec_draft_p_min_var.get().strip()
        if spec_draft_p_min:
            cmd.extend(["--spec-draft-p-min", spec_draft_p_min])

        model_draft = self.model_draft_var.get().strip()
        if model_draft:
            cmd.extend(["--model-draft", model_draft])

        n_gpu_layers_draft = self.n_gpu_layers_draft_var.get().strip()
        if n_gpu_layers_draft:
            cmd.extend(["--n-gpu-layers-draft", n_gpu_layers_draft])

        flash_attn = self.flash_attn_var.get().strip()
        if flash_attn and flash_attn != "auto":
            cmd.extend(["--flash-attn", flash_attn])

        kwargs_str = self.chat_template_var.get().strip()
        if kwargs_str:
            cmd.extend(["--chat-template-kwargs", kwargs_str])

        cache_type_k = self.cache_type_k_var.get().strip()
        if cache_type_k:
            cmd.extend(["-ctk", cache_type_k])

        cache_type_v = self.cache_type_v_var.get().strip()
        if cache_type_v:
            cmd.extend(["-ctv", cache_type_v])

        if self.mlock_var.get():
            cmd.append("--mlock")

        if self.verbose_var.get():
            cmd.append("--verbose")
        if self.webui_var.get():
            cmd.append("--webui")
        if self.embeddings_var.get():
            cmd.append("--embeddings")

        lv = self.log_verbosity_var.get().strip()
        if lv:
            cmd.extend(["--log-verbosity", lv])

        custom = self.custom_args_var.get().strip()
        if custom:
            import shlex
            cmd.extend(shlex.split(custom))

        # 确保开启 /metrics 端点，用于 token 统计看板（用户未显式指定时自动追加）
        if "--metrics" not in cmd:
            cmd.append("--metrics")

        return cmd

    def build_launch_snapshot(self, cmd):
        def value(var, fallback="-"):
            text = str(var.get()).strip()
            return text if text else fallback

        def enabled(var):
            return "开启" if var.get() else "关闭"

        sections = [
            (
                "启动概览",
                [
                    ("启动时间", getattr(self, "server_started_at", "") or "-"),
                    ("进程 PID", str(self.process.pid) if self.process else "-"),
                    ("模型", value(self.model_path_var)),
                    ("模型根目录", value(self.model_root_var)),
                    ("llama-server", value(self.server_path_var)),
                    ("服务地址", f"{value(self.host_var, '0.0.0.0')}:{value(self.port_var)}"),
                ],
            ),
            (
                "基础/性能",
                [
                    ("上下文", value(self.ctx_size_var)),
                    ("GPU 层数", value(self.n_gpu_layers_var)),
                    ("批处理", value(self.batch_size_var)),
                    ("微批处理", value(self.ubatch_size_var)),
                    ("线程", value(self.threads_var)),
                    ("批处理线程", value(self.threads_batch_var)),
                    ("最大生成", value(self.n_predict_var)),
                    ("并发槽位", value(self.n_parallel_var)),
                ],
            ),
            (
                "采样",
                [
                    ("温度", value(self.temp_var)),
                    ("Top-K", value(self.top_k_var)),
                    ("Top-P", value(self.top_p_var)),
                    ("Min-P", value(self.min_p_var)),
                    ("存在惩罚", value(self.presence_penalty_var)),
                    ("重复惩罚", value(self.repeat_penalty_var)),
                    ("重复范围", value(self.repeat_last_n_var)),
                    ("随机种子", value(self.seed_var)),
                ],
            ),
            (
                "GPU/MoE",
                [
                    ("主 GPU", value(self.main_gpu_var)),
                    ("分割模式", value(self.split_mode_var)),
                    ("张量分割", value(self.tensor_split_var)),
                    ("Flash Attention", value(self.flash_attn_var)),
                    ("K 缓存", value(self.cache_type_k_var)),
                    ("V 缓存", value(self.cache_type_v_var)),
                    ("锁定内存", enabled(self.mlock_var)),
                    ("MoE 保留 CPU", enabled(self.cpu_moe_var)),
                    ("MoE CPU 层数", value(self.n_cpu_moe_var)),
                    ("MoE 专家数量", value(self.moe_expert_count_var)),
                ],
            ),
            (
                "投机解码/多模态",
                [
                    ("投机类型", value(self.spec_type_var)),
                    ("Draft token 数", value(self.spec_draft_n_max_var)),
                    ("Draft 最小阈值", value(self.spec_draft_p_min_var)),
                    ("Draft GPU 层数", value(self.n_gpu_layers_draft_var)),
                    ("Draft 模型", value(self.model_draft_var)),
                    ("视觉模型", enabled(self.mmproj_enabled_var)),
                    ("mmproj", value(self.mmproj_path_var)),
                ],
            ),
            (
                "服务/自定义",
                [
                    ("WebUI", enabled(self.webui_var)),
                    ("Embeddings", enabled(self.embeddings_var)),
                    ("详细日志", enabled(self.verbose_var)),
                    ("日志级别", value(self.log_verbosity_var)),
                    ("超时", value(self.timeout_var)),
                    ("空闲休眠", value(self.sleep_idle_seconds_var)),
                    ("工具调用", value(self.tools_var)),
                    ("对话模板参数", value(self.chat_template_var)),
                    ("自定义参数", value(self.custom_args_var)),
                ],
            ),
        ]

        lines = []
        for title, rows in sections:
            lines.append(f"[{title}]")
            for label, text in rows:
                lines.append(f"{label}: {text}")
            lines.append("")

        lines.append("[完整命令]")
        lines.append(self.format_command(cmd))
        return "\n".join(lines).strip()

    def show_launch_snapshot(self):
        if self.last_launch_config_text:
            snapshot = self.last_launch_config_text
        else:
            try:
                snapshot = self.build_launch_snapshot(self.build_command())
            except Exception as exc:
                snapshot = f"启动参数暂不可用: {exc}"

        dialog = ctk.CTkToplevel(self.root)
        dialog.title("启动参数快照")
        dialog.geometry("820x620")
        dialog.minsize(620, 420)
        dialog.transient(self.root)
        dialog.grid_columnconfigure(0, weight=1)
        dialog.grid_rowconfigure(1, weight=1)

        C = self.COLORS
        ctk.CTkLabel(
            dialog, text="启动参数快照",
            font=("Microsoft YaHei UI", 18, "bold"),
            text_color=C["text_primary"],
        ).grid(row=0, column=0, sticky="w", padx=16, pady=(14, 8))

        text = ctk.CTkTextbox(
            dialog, wrap=tk.WORD, font=("Consolas", 11),
            fg_color=C["dark_bg"], text_color=C["dark_text"],
            corner_radius=10,
        )
        text.grid(row=1, column=0, sticky="nsew", padx=16, pady=(0, 10))
        text.insert(tk.END, snapshot)
        text.configure(state=tk.DISABLED)

        actions = ctk.CTkFrame(dialog, fg_color="transparent")
        actions.grid(row=2, column=0, sticky="e", padx=16, pady=(0, 14))
        ctk.CTkButton(
            actions, text="复制", width=74, height=32, corner_radius=9,
            command=lambda: self.copy_text(snapshot),
            fg_color=C["tab_bg"], hover_color=C["card_border"],
            text_color=C["text_primary"], font=("Microsoft YaHei UI", 11),
        ).pack(side=tk.LEFT, padx=(0, 8))
        ctk.CTkButton(
            actions, text="关闭", width=74, height=32, corner_radius=9,
            command=dialog.destroy,
            fg_color=C["primary"], hover_color=C["primary_hover"],
            font=("Microsoft YaHei UI", 11),
        ).pack(side=tk.LEFT)
        dialog.focus()

    def copy_text(self, text):
        self.root.clipboard_clear()
        self.root.clipboard_append(text)

    def update_command_preview(self):
        self.command_update_after_id = None
        if not hasattr(self, "command_preview_text") and not hasattr(self, "config_command_preview_text"):
            return
        try:
            preview = self.format_command(self.build_command())
        except Exception as exc:
            preview = f"命令预览不可用: {exc}"
        for widget_name in ("command_preview_text", "config_command_preview_text"):
            widget = getattr(self, widget_name, None)
            if widget is None:
                continue
            widget.configure(state=tk.NORMAL)
            widget.delete(1.0, tk.END)
            widget.insert(tk.END, preview)
            widget.configure(state=tk.DISABLED)
