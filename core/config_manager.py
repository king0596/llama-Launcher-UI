import tkinter as tk
import os
import tomllib
import json
import shlex
from tkinter import filedialog, messagebox

try:
    import customtkinter as ctk
except ImportError:
    ctk = None

from config import DEFAULT_CONFIG
from utils import toml_dump


class ConfigMixin:
    """配置管理 mixin：加载/保存/校验配置、模型扫描、文件浏览。"""

    def apply_cli_args(self):
        args = self._cli_args
        if args.model:
            self.model_path_var.set(args.model)
            self.model_combo_var.set(os.path.basename(args.model))
        if args.server:
            self.server_path_var.set(args.server)
        if args.host:
            self.host_var.set(args.host)
        if args.port:
            self.port_var.set(str(args.port))
        if args.ctx_size:
            self.ctx_size_var.set(str(args.ctx_size))
        if args.n_predict:
            self.n_predict_var.set(str(args.n_predict))
        if args.n_gpu_layers:
            self.n_gpu_layers_var.set(str(args.n_gpu_layers))
        if args.threads:
            self.threads_var.set(str(args.threads))
        if args.batch_size:
            self.batch_size_var.set(str(args.batch_size))
        if args.ubatch_size:
            self.ubatch_size_var.set(str(args.ubatch_size))
        if args.temp:
            self.temp_var.set(str(args.temp))

        if args.chat_template_kwargs:
            self.chat_template_var.set(args.chat_template_kwargs)
        if args.flash_attention is not None:
            self.flash_attn_var.set(args.flash_attention)
        if args.mmproj:
            self.mmproj_path_var.set(args.mmproj)
        if args.timeout:
            self.timeout_var.set(str(args.timeout))
        if args.sleep_idle_seconds:
            self.sleep_idle_seconds_var.set(str(args.sleep_idle_seconds))

    def load_config(self):
        if os.path.exists(self.config_file):
            with open(self.config_file, "rb") as f:
                self.config = tomllib.load(f)
        else:
            self.config = DEFAULT_CONFIG.copy()
            self.config["model_root"] = self.model_root

    def scan_models_later(self):
        self.scan_models()

    def scan_models(self):
        self.models = []
        self._model_rel_paths = {}
        if os.path.isdir(self.model_root):
            for dirpath, _, filenames in os.walk(self.model_root):
                for f in filenames:
                    if f.lower().endswith(".gguf"):
                        rel_path = os.path.relpath(
                            os.path.join(dirpath, f), self.model_root
                        )
                        rel_path = rel_path.replace("\\", "/")
                        self.models.append(rel_path)
                        self._model_rel_paths[rel_path] = rel_path
        self.models.sort()

    def model_display_for_path(self, path):
        if not path:
            return ""
        try:
            rel_path = os.path.relpath(path, self.model_root)
            if not rel_path.startswith(".."):
                return rel_path.replace("\\", "/")
        except ValueError:
            pass
        return os.path.basename(path)

    def load_config_to_ui(self):
        self.server_path_var.set(self.config.get("llama_server_path", ""))
        self.model_root_var.set(self.config.get("model_root", self.model_root))
        model = self.config.get("model", "")
        self.model_path_var.set(model)

        if model:
            display_name = self.model_display_for_path(model)
            if display_name in self.models:
                self.model_combo_var.set(display_name)

        self.host_var.set(self.config.get("host", "0.0.0.0"))
        self.port_var.set(str(self.config.get("port", 8080)))
        self.ctx_size_var.set(str(self.config.get("ctx_size", 96000)))
        self.threads_var.set(str(self.config.get("threads", 0)))
        self.threads_batch_var.set(str(self.config.get("threads_batch", 0)))
        self.n_predict_var.set(str(self.config.get("n_predict", -1)))
        self.n_gpu_layers_var.set(str(self.config.get("n_gpu_layers", 99)))
        self.batch_size_var.set(str(self.config.get("batch_size", 1024)))
        self.ubatch_size_var.set(str(self.config.get("ubatch_size", 512)))
        self.temp_var.set(str(self.config.get("temp", 0.6)))
        self.top_k_var.set(str(self.config.get("top_k", 20)))
        self.top_p_var.set(str(self.config.get("top_p", 0.95)))
        self.min_p_var.set(str(self.config.get("min_p", 0.0)))
        self.presence_penalty_var.set(str(self.config.get("presence_penalty", 0.0)))
        self.repeat_penalty_var.set(str(self.config.get("repeat_penalty", 1.0)))
        self.repeat_last_n_var.set(str(self.config.get("repeat_last_n", 64)))
        self.seed_var.set(str(self.config.get("seed", "-1")))
        self.timeout_var.set(str(self.config.get("timeout", "")))
        self.sleep_idle_seconds_var.set(str(self.config.get("sleep_idle_seconds", "")))
        self.n_parallel_var.set(str(self.config.get("n_parallel", "")))
        self.tools_var.set(self.config.get("tools", ""))
        self.chat_template_var.set(
            self.config.get("chat_template_kwargs", '{}')
        )
        self.main_gpu_var.set(str(self.config.get("main_gpu", 0)))
        self.split_mode_var.set(self.config.get("split_mode", ""))
        self.tensor_split_var.set(self.config.get("tensor_split", ""))
        self.cpu_moe_var.set(self.config.get("cpu_moe", False))
        self.n_cpu_moe_var.set(str(self.config.get("n_cpu_moe", 0)))
        self.moe_expert_count_var.set(str(self.config.get("moe_expert_count", -1)))
        self.spec_draft_n_max_var.set(str(self.config.get("spec_draft_n_max", self.config.get("draft", "0"))))
        self.spec_draft_p_min_var.set(str(self.config.get("spec_draft_p_min", "")))
        self.spec_type_var.set(self.config.get("spec_type", ""))
        self.n_gpu_layers_draft_var.set(str(self.config.get("n_gpu_layers_draft", "")))
        self.model_draft_var.set(self.config.get("model_draft", ""))
        self.flash_attn_var.set(self.config.get("flash_attn", "auto"))
        self.mlock_var.set(self.config.get("mlock", False))
        self.cache_type_k_var.set(self.config.get("cache_type_k", ""))
        self.cache_type_v_var.set(self.config.get("cache_type_v", ""))

        self.verbose_var.set(self.config.get("verbose", True))
        self.webui_var.set(self.config.get("webui", True))
        self.embeddings_var.set(self.config.get("embeddings", False))
        self.log_verbosity_var.set(str(self.config.get("log_verbosity", 3)))
        self.mmproj_path_var.set(self.config.get("mmproj", ""))
        self.mmproj_enabled_var.set(self.config.get("mmproj_enabled", False))
        self.custom_args_var.set(self.config.get("custom_args", ""))

    def refresh_models(self):
        self.model_root = self.model_root_var.get().strip()
        self.scan_models()
        self.model_combo.configure(values=self.models or ["未扫描到模型"])
        current = self.model_path_var.get()
        if current:
            display_name = self.model_display_for_path(current)
            if display_name in self.models:
                self.model_combo_var.set(display_name)

    def on_model_select(self, event):
        selected = self.model_combo_var.get()
        if selected:
            search_root = self.model_root_var.get()
            rel_path = self._model_rel_paths.get(selected, selected)
            found = os.path.join(search_root, rel_path)
            self.model_path_var.set(found)

    def browse_model_root(self):
        path = filedialog.askdirectory()
        if path:
            self.model_root_var.set(path)
            self.model_root = path
            self.refresh_models()

    def browse_server(self):
        path = filedialog.askopenfilename(
            filetypes=[("Executable", "*.exe"), ("All files", "*.*")]
        )
        if path:
            self.server_path_var.set(path)

    def browse_model(self):
        path = filedialog.askopenfilename(
            filetypes=[("GGUF files", "*.gguf"), ("All files", "*.*")]
        )
        if path:
            self.model_path_var.set(path)
            display_name = self.model_display_for_path(path)
            self.model_combo_var.set(display_name if display_name in self.models else "")

    def browse_mmproj(self):
        path = filedialog.askopenfilename(
            filetypes=[("GGUF files", "*.gguf"), ("All files", "*.*")]
        )
        if path:
            self.mmproj_path_var.set(path)

    def browse_model_draft(self):
        path = filedialog.askopenfilename(
            filetypes=[("GGUF files", "*.gguf"), ("All files", "*.*")]
        )
        if path:
            self.model_draft_var.set(path)

    def parse_int_field(self, label, var, errors, default=None, required=True):
        raw = var.get().strip()
        if not raw:
            if required:
                errors.append(f"{label} 不能为空")
                return 0
            return default
        try:
            return int(raw)
        except ValueError:
            errors.append(f"{label} 必须是整数")
            return default if default is not None else 0

    def parse_float_field(self, label, var, errors, default=None, required=True):
        raw = var.get().strip()
        if not raw:
            if required:
                errors.append(f"{label} 不能为空")
                return 0.0
            return default
        try:
            return float(raw)
        except ValueError:
            errors.append(f"{label} 必须是数字")
            return default if default is not None else 0.0

    def collect_config_from_ui(self):
        errors = []
        port = self.parse_int_field("监听端口", self.port_var, errors)
        if not (1 <= port <= 65535):
            errors.append("监听端口必须在 1 到 65535 之间")

        chat_template = self.chat_template_var.get().strip()
        if chat_template:
            try:
                json.loads(chat_template)
            except json.JSONDecodeError as exc:
                errors.append(f"对话模板必须是有效 JSON: {exc.msg}")

        custom_args = self.custom_args_var.get().strip()
        if custom_args:
            try:
                shlex.split(custom_args)
            except ValueError as exc:
                errors.append(f"自定义参数格式无效: {exc}")

        data = {
            "llama_server_path": self.server_path_var.get().strip(),
            "model_root": self.model_root_var.get().strip(),
            "model": self.model_path_var.get().strip(),
            "host": self.host_var.get().strip(),
            "port": port,
            "ctx_size": self.parse_int_field("上下文长度", self.ctx_size_var, errors),
            "threads": self.parse_int_field("CPU线程数", self.threads_var, errors),
            "threads_batch": self.parse_int_field("批处理线程", self.threads_batch_var, errors, 0, False),
            "n_predict": self.parse_int_field("最大生成数", self.n_predict_var, errors),
            "n_gpu_layers": self.parse_int_field("GPU加速层数", self.n_gpu_layers_var, errors),
            "batch_size": self.parse_int_field("批处理大小", self.batch_size_var, errors),
            "ubatch_size": self.parse_int_field("物理批处理大小", self.ubatch_size_var, errors, 0, False),
            "temp": self.parse_float_field("温度", self.temp_var, errors),
            "top_k": self.parse_int_field("Top-K采样", self.top_k_var, errors),
            "top_p": self.parse_float_field("Top-P采样", self.top_p_var, errors),
            "min_p": self.parse_float_field("最小概率", self.min_p_var, errors),
            "presence_penalty": self.parse_float_field("存在惩罚", self.presence_penalty_var, errors),
            "repeat_penalty": self.parse_float_field("重复惩罚", self.repeat_penalty_var, errors, 1.0, False),
            "repeat_last_n": self.parse_int_field("重复惩罚范围", self.repeat_last_n_var, errors, 64, False),
            "seed": self.parse_int_field("随机种子", self.seed_var, errors, -1, False),
            "timeout": self.parse_int_field("超时", self.timeout_var, errors, 0, False),
            "sleep_idle_seconds": self.parse_int_field("空闲休眠", self.sleep_idle_seconds_var, errors, 0, False),
            "n_parallel": self.parse_int_field("并发槽位数", self.n_parallel_var, errors, -1, False),
            "tools": self.tools_var.get().strip(),
            "chat_template_kwargs": chat_template,
            "main_gpu": self.parse_int_field("主GPU编号", self.main_gpu_var, errors, 0, False),
            "split_mode": self.split_mode_var.get().strip(),
            "tensor_split": self.tensor_split_var.get().strip(),
            "cpu_moe": self.cpu_moe_var.get(),
            "n_cpu_moe": self.parse_int_field("MoE保留层数", self.n_cpu_moe_var, errors, -1, False),
            "moe_expert_count": self.parse_int_field("MoE专家数量", self.moe_expert_count_var, errors, -1, False),
            "spec_draft_n_max": self.spec_draft_n_max_var.get().strip(),
            "spec_draft_p_min": self.spec_draft_p_min_var.get().strip(),
            "spec_type": self.spec_type_var.get().strip(),
            "n_gpu_layers_draft": self.n_gpu_layers_draft_var.get().strip(),
            "model_draft": self.model_draft_var.get().strip(),
            "flash_attn": self.flash_attn_var.get().strip(),
            "mlock": self.mlock_var.get(),
            "cache_type_k": self.cache_type_k_var.get().strip(),
            "cache_type_v": self.cache_type_v_var.get().strip(),
            "verbose": self.verbose_var.get(),
            "webui": self.webui_var.get(),
            "embeddings": self.embeddings_var.get(),
            "log_verbosity": self.parse_int_field("日志级别", self.log_verbosity_var, errors),
            "mmproj": self.mmproj_path_var.get().strip(),
            "mmproj_enabled": self.mmproj_enabled_var.get(),
            "custom_args": custom_args,
            "window_geometry": self.root.geometry(),
        }

        if errors:
            messagebox.showerror("配置无效", "\n".join(errors[:10]))
            return None
        return data

    def write_config_file(self):
        with open(self.config_file, "w", encoding="utf-8") as f:
            toml_dump(self.config, f)

    def save_config(self, show_message=True):
        data = self.collect_config_from_ui()
        if data is None:
            return False

        self.config.update(data)
        self.model_root = data["model_root"]
        self.write_config_file()
        self.update_command_preview()

        self.log("配置已保存到 config.toml")
        if show_message:
            messagebox.showinfo("成功", "配置已保存!")
        return True
