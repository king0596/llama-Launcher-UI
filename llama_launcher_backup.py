import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import subprocess
import os
import sys
import time
import socket
import threading
import tomllib
import json
import argparse
import queue


def parse_args():
    parser = argparse.ArgumentParser(description="Llama Server Launcher")
    parser.add_argument("--no-mmap", action="store_true", help="Disable memory mapping")
    parser.add_argument(
        "--flash-attention",
        choices=["auto", "on", "off"],
        default=None,
        help="Flash attention mode",
    )
    parser.add_argument("-m", "--model", help="Model file path")
    parser.add_argument("--host", default="0.0.0.0", help="Server host")
    parser.add_argument("--port", type=int, default=8080, help="Server port")
    parser.add_argument("-c", "--ctx-size", type=int, help="Context size")
    parser.add_argument("-n", "--n-predict", type=int, help="Max tokens to predict")
    parser.add_argument("-ngl", "--n-gpu-layers", type=int, help="GPU layers")
    parser.add_argument("-t", "--threads", type=int, help="Number of threads")
    parser.add_argument(
        "--threads-batch", type=int, help="Number of threads for batch processing"
    )
    parser.add_argument("-b", "--batch-size", type=int, help="Batch size")
    parser.add_argument("--ubatch-size", type=int, help="Physical batch size")
    parser.add_argument("--temp", type=float, help="Temperature")

    parser.add_argument("--server", help="llama-server executable path")
    parser.add_argument("--mmproj", help="Vision projector file")
    parser.add_argument("--timeout", type=int, help="Timeout in seconds")
    parser.add_argument("--sleep-idle-seconds", type=int, help="Sleep idle seconds")
    parser.add_argument("--tools", help="Enable built-in tools for AI agents (e.g. 'all' or 'read_file,grep_search')")
    parser.add_argument(
        "--chat-template-kwargs",
        help="Chat template kwargs JSON",
    )
    return parser.parse_args()


def toml_dump(data, f):
    for key, value in data.items():
        if isinstance(value, dict):
            f.write(f"[{key}]\n")
            for k, v in value.items():
                if isinstance(v, bool):
                    f.write(f"{k} = {'true' if v else 'false'}\n")
                else:
                    f.write(f"{k} = {repr(v)}\n")
            f.write("\n")
        else:
            if isinstance(value, bool):
                f.write(f"{key} = {'true' if value else 'false'}\n")
            else:
                f.write(f"{key} = {repr(value)}\n")


args = parse_args()


PARAM_CONFIG = {
    "host": {
        "label": "监听地址 (--host)",
        "tooltip": "服务器绑定的IP地址，0.0.0.0允许所有连接",
    },
    "port": {
        "label": "监听端口 (--port)",
        "tooltip": "服务器监听的端口号，默认8080",
    },
    "ctx_size": {
        "label": "上下文长度 (-c, --ctx-size)",
        "tooltip": "模型处理的上下文最大token数，影响内存占用",
    },
    "threads": {
        "label": "CPU线程数 (-t, --threads)",
        "tooltip": "用于推理的CPU线程数，-1表示自动检测CPU核心数",
    },
    "threads_batch": {
        "label": "批处理线程 (--threads-batch)",
        "tooltip": "用于批处理预计算的CPU线程数，默认与threads相同",
    },
    "n_predict": {
        "label": "最大生成数 (-n, --n-predict)",
        "tooltip": "单次生成的最大token数，-1表示无限制",
    },
 
    "n_gpu_layers": {
        "label": "GPU加速层数 (-ngl, --n-gpu-layers)",
        "tooltip": "加载到GPU的模型层数，-1表示全部GPU层，999也代表全部",
    },
    "batch_size": {
        "label": "批处理大小 (-b, --batch-size)",
        "tooltip": "预计算批处理的token数，影响内存和速度",
    },
    "ubatch_size": {
        "label": "物理批处理大小 (-ub, --ubatch-size)",
        "tooltip": "物理最大批处理大小，默认512",
    },
    "temp": {
        "label": "温度 (--temp)",
        "tooltip": "采样温度，较低值使输出更确定性，较高值增加创造性",
    },
    "top_k": {
        "label": "Top-K采样 (--top-k)",
        "tooltip": "限制采样候选词数量，数值越小越保守，0表示不限制",
    },
    "top_p": {
        "label": "Top-P采样 (--top-p)",
        "tooltip": "核采样阈值，只选择累积概率超过此值的词",
    },
    "min_p": {
        "label": "最小概率 (--min-p)",
        "tooltip": "最小token概率阈值，过滤掉概率过低的词",
    },
    "presence_penalty": {
        "label": "存在惩罚 (--presence-penalty)",
        "tooltip": "对已出现过的token增加惩罚，避免重复",
    },
    "repeat_penalty": {
        "label": "重复惩罚 (--repeat-penalty)",
        "tooltip": "对重复token的惩罚力度，默认1.0",
    },
    "repeat_last_n": {
        "label": "重复惩罚范围 (--repeat-last-n)",
        "tooltip": "考虑重复的最近token数量",
    },
    "main_gpu": {
        "label": "主GPU编号 (--main-gpu)",
        "tooltip": "当使用多GPU时指定主设备编号",
    },
    "split_mode": {
        "label": "分割模式 (--split-mode)",
        "tooltip": "模型层分割方式：none不分、layer按层、row按行",
    },
    "tensor_split": {
        "label": "张量分割 (--tensor-split)",
        "tooltip": "多GPU间张量分割比例，如0.3,0.7",
    },
    "cpu_moe": {
        "label": "MoE保留CPU (--cpu-moe)",
        "tooltip": "将MoE专家权重全部保留在CPU以节省显存",
    },
    "n_cpu_moe": {
        "label": "MoE保留层数 (--n-cpu-moe)",
        "tooltip": "将MoE专家权重的前N层保留在CPU",
    },
    "spec_type": {
        "label": "投机类型 (--spec-type)",
        "tooltip": "投机解码实现方式：none禁用、draft-simple/eagle3/mtp使用draft模型、ngram-simple/map-k/map-k4v/mod/cache无需draft模型",
    },
    "spec_draft_n_max": {
        "label": "投机token数 (--spec-draft-n-max)",
        "tooltip": "最大draft token数量，0为禁用，默认16",
    },
    "spec_draft_p_min": {
        "label": "投机最小阈值 (--spec-draft-p-min)",
        "tooltip": "draft token被接受的最小概率阈值，范围0~1，默认0.75",
    },
    "n_gpu_layers_draft": {
        "label": "Draft-GPU层数 (--n-gpu-layers-draft)",
        "tooltip": "draft模型加载到GPU的层数，auto自动，0为全部CPU",
    },
    "model_draft": {
        "label": "Draft模型路径 (--model-draft)",
        "tooltip": "投机解码用的draft模型路径（可选）",
    },

    "flash_attn": {
        "label": "Flash注意力 (--flash-attn)",
        "tooltip": "启用Flash Attention加速，可选auto/on/off",
    },
    "mlock": {
        "label": "锁定内存 (--mlock)",
        "tooltip": "将模型锁定在内存中，防止交换到磁盘",
    },
    "cache_type_k": {
        "label": "K缓存类型 (-ctk, --cache-type-k)",
        "tooltip": "Key缓存数据类型",
    },
    "cache_type_v": {
        "label": "V缓存类型 (-ctv, --cache-type-v)",
        "tooltip": "Value缓存数据类型",
    },
    "timeout": {
        "label": "超时 (--timeout)",
        "tooltip": "请求超时时间(秒)",
    },
    "sleep_idle_seconds": {
        "label": "空闲休眠 (--sleep-idle-seconds)",
        "tooltip": "空闲多少秒后进入休眠状态",
    },
    "tools": {
        "label": "工具调用 (--tools)",
        "tooltip": "启用AI智能体的内置工具，如'all'启用所有工具（用于模型调用工具）",
    },
    "seed": {
        "label": "随机种子 (-s, --seed)",
        "tooltip": "随机数种子，-1表示随机",
    },
}


class LlamaLauncher:
    def __init__(self, root):
        self.root = root
        self.root.title("Llama Server Launcher")
        self.root.geometry("1000x750")
        self.root.resizable(True, True)
        self.process = None
        self.openclaw_process = None
        self.config_file = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "config.toml"
        )
        self.config = {}
        self.model_root = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "model"
        )
        self.models = []
        self.load_config()
        self.scan_models()
        self.build_ui()
        self.load_config_to_ui()
        self.apply_cli_args()

    def apply_cli_args(self):
        global args
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
            self.config = {
                "llama_server_path": "",
                "model": "",
                "host": "0.0.0.0",
                "port": 8080,
                "ctx_size": 96000,
                "n_predict": -1,
              "chat_template_kwargs": '{}',
                "temp": 0.6,
                "top_k": 20,
                "top_p": 0.95,
                "min_p": 0.0,
                "presence_penalty": 0.0,
                "batch_size": 2048,
                "threads": 0,
                "threads_batch": 0,
                "cpu_moe": False,
                "n_cpu_moe": 0,
                "moe_expert_count": -1,
                "split_mode": "layer",
                "tensor_split": "",
                "main_gpu": 0,
                "flash_attn": "auto",
                "fit": "on",
                "mlock": False,
                "verbose": True,
                "log_verbosity": 3,
                "webui": True,
                "embeddings": False,
                "continuous_batching": True,
                "mmproj": "",
                "mmproj_enabled": False,
                "n_parallel": -1,
            }

    def scan_models_later(self):
        self.scan_models()

    def scan_models(self):
        self.models = []
        self._model_rel_paths = {}
        if os.path.isdir(self.model_root):
            for dirpath, _, filenames in os.walk(self.model_root):
                for f in filenames:
                    if f.endswith(".gguf"):
                        rel_path = os.path.relpath(
                            os.path.join(dirpath, f), self.model_root
                        )
                        self.models.append(f)
                        self._model_rel_paths[f] = rel_path
        self.models.sort()

    def build_ui(self):
        self.root.geometry("980x800")

        paned = tk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        left_frame = ttk.Frame(paned)
        right_frame = ttk.Frame(paned)

        paned.add(left_frame, width=620)
        paned.add(right_frame)

        self.build_left_panel(left_frame)
        self.build_right_panel(right_frame)

    def build_left_panel(self, parent):
        canvas = tk.Canvas(parent, highlightthickness=0)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        self.scrollable = ttk.Frame(canvas)
        self.scrollable.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")),
        )
        canvas.create_window((0, 0), window=self.scrollable, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        canvas.bind(
            "<MouseWheel>",
            lambda e: canvas.yview_scroll(int(-1 * (e.delta / 120)), "units"),
        )

        row = 0
        pad = {"padx": 3, "pady": 2}

        ttk.Label(self.scrollable, text="模型根目录 (--model-root):").grid(
            row=row, column=0, sticky=tk.W, **pad
        )
        self.model_root_var = tk.StringVar(value=self.model_root)
        ttk.Entry(self.scrollable, textvariable=self.model_root_var, width=38).grid(
            row=row, column=1, **pad
        )
        ttk.Button(self.scrollable, text="浏览", command=self.browse_model_root).grid(
            row=row, column=2, **pad
        )
        row += 1

        ttk.Label(self.scrollable, text="选择模型:").grid(
            row=row, column=0, sticky=tk.W, **pad
        )
        self.model_combo_var = tk.StringVar()
        self.model_combo = ttk.Combobox(
            self.scrollable,
            textvariable=self.model_combo_var,
            width=38,
            state="readonly",
        )
        self.model_combo["values"] = self.models
        self.model_combo.grid(row=row, column=1, **pad)
        self.model_combo.bind("<MouseWheel>", lambda e: "break")
        self.model_combo.bind("<<ComboboxSelected>>", self.on_model_select)
        ttk.Button(self.scrollable, text="刷新", command=self.refresh_models).grid(
            row=row, column=2, **pad
        )
        row += 1

        ttk.Label(self.scrollable, text="模型路径 (-m):").grid(
            row=row, column=0, sticky=tk.W, **pad
        )
        self.model_path_var = tk.StringVar()
        ttk.Entry(
            self.scrollable,
            textvariable=self.model_path_var,
            width=38,
            state="readonly",
        ).grid(row=row, column=1, **pad)
        ttk.Button(self.scrollable, text="手动浏览", command=self.browse_model).grid(
            row=row, column=2, **pad
        )
        row += 1

        ttk.Label(self.scrollable, text="视觉投影 (--mmproj):").grid(
            row=row, column=0, sticky=tk.W, **pad
        )
        self.mmproj_path_var = tk.StringVar()
        ttk.Entry(
            self.scrollable,
            textvariable=self.mmproj_path_var,
            width=38,
            state="readonly",
        ).grid(row=row, column=1, **pad)
        ttk.Button(self.scrollable, text="浏览", command=self.browse_mmproj).grid(
            row=row, column=2, **pad
        )
        row += 1

        self.mmproj_enabled_var = tk.BooleanVar()
        ttk.Checkbutton(
            self.scrollable,
            text="启用视觉模型",
            variable=self.mmproj_enabled_var,
        ).grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=1)
        row += 1

        ttk.Label(self.scrollable, text="llama-server 路径:").grid(
            row=row, column=0, sticky=tk.W, **pad
        )
        self.server_path_var = tk.StringVar()
        ttk.Entry(self.scrollable, textvariable=self.server_path_var, width=38).grid(
            row=row, column=1, **pad
        )
        ttk.Button(self.scrollable, text="浏览", command=self.browse_server).grid(
            row=row, column=2, **pad
        )
        row += 1

        self.add_sep(row)
        row += 1

        self.host_var = tk.StringVar()
        self.port_var = tk.StringVar()
        self.ctx_size_var = tk.StringVar()
        self.threads_var = tk.StringVar()
        self.threads_batch_var = tk.StringVar()
        self.n_predict_var = tk.StringVar()
        self.n_gpu_layers_var = tk.StringVar()
        self.batch_size_var = tk.StringVar()
        self.ubatch_size_var = tk.StringVar()
        self.temp_var = tk.StringVar()
        self.top_k_var = tk.StringVar()
        self.top_p_var = tk.StringVar()
        self.min_p_var = tk.StringVar()
        self.presence_penalty_var = tk.StringVar()
        self.timeout_var = tk.StringVar()
        self.sleep_idle_seconds_var = tk.StringVar()
        self.n_parallel_var = tk.StringVar()
        self.tools_var = tk.StringVar()

        ttk.Label(self.scrollable, text="服务器设置", font=("Arial", 9, "bold")).grid(
            row=row, column=0, columnspan=3, sticky=tk.W
        )
        row += 1
        cfg = PARAM_CONFIG
        self.add_param_row(
            row, cfg["host"]["label"] + ":", self.host_var, 18, cfg["host"]["tooltip"]
        )
        row += 1
        self.add_param_row(
            row, cfg["port"]["label"] + ":", self.port_var, 18, cfg["port"]["tooltip"]
        )
        row += 1

        self.add_sep(row)
        row += 1

        ttk.Label(self.scrollable, text="模型参数", font=("Arial", 9, "bold")).grid(
            row=row, column=0, columnspan=3, sticky=tk.W
        )
        row += 1
        self.add_param_row(
            row,
            cfg["ctx_size"]["label"] + ":",
            self.ctx_size_var,
            18,
            cfg["ctx_size"]["tooltip"],
        )
        row += 1
        self.add_param_row(
            row,
            cfg["n_gpu_layers"]["label"] + ":",
            self.n_gpu_layers_var,
            18,
            cfg["n_gpu_layers"]["tooltip"],
        )
        row += 1
        self.add_param_row(
            row,
            cfg["batch_size"]["label"] + ":",
            self.batch_size_var,
            18,
            cfg["batch_size"]["tooltip"],
        )
        row += 1
        self.add_param_row(
            row,
            cfg["ubatch_size"]["label"] + ":",
            self.ubatch_size_var,
            18,
            cfg["ubatch_size"]["tooltip"],
        )
        row += 1

        self.add_sep(row)
        row += 1

        ttk.Label(self.scrollable, text="CPU 线程", font=("Arial", 9, "bold")).grid(
            row=row, column=0, columnspan=3, sticky=tk.W
        )
        row += 1
        self.add_param_row(
            row,
            cfg["threads"]["label"] + ":",
            self.threads_var,
            18,
            cfg["threads"]["tooltip"],
        )
        row += 1
        self.add_param_row(
            row,
            cfg["threads_batch"]["label"] + ":",
            self.threads_batch_var,
            18,
            cfg["threads_batch"]["tooltip"],
        )
        row += 1

        self.add_sep(row)
        row += 1

        ttk.Label(self.scrollable, text="采样设置", font=("Arial", 9, "bold")).grid(
            row=row, column=0, columnspan=3, sticky=tk.W
        )
        row += 1
        self.add_param_row(
            row, cfg["temp"]["label"] + ":", self.temp_var, 18, cfg["temp"]["tooltip"]
        )
        row += 1
        self.add_param_row(
            row,
            cfg["top_k"]["label"] + ":",
            self.top_k_var,
            18,
            cfg["top_k"]["tooltip"],
        )
        row += 1
        self.add_param_row(
            row,
            cfg["top_p"]["label"] + ":",
            self.top_p_var,
            18,
            cfg["top_p"]["tooltip"],
        )
        row += 1
        self.add_param_row(
            row,
            cfg["min_p"]["label"] + ":",
            self.min_p_var,
            18,
            cfg["min_p"]["tooltip"],
        )
        row += 1
        self.add_param_row(
            row,
            cfg["presence_penalty"]["label"] + ":",
            self.presence_penalty_var,
            18,
            cfg["presence_penalty"]["tooltip"],
        )
        row += 1
        self.add_param_row(
            row,
            cfg["n_predict"]["label"] + ":",
            self.n_predict_var,
            18,
            cfg["n_predict"]["tooltip"],
        )
        row += 1


        self.add_sep(row)
        row += 1

        ttk.Label(self.scrollable, text="请求控制", font=("Arial", 9, "bold")).grid(
            row=row, column=0, columnspan=3, sticky=tk.W
        )
        row += 1
        self.add_param_row(
            row,
            cfg["timeout"]["label"] + ":",
            self.timeout_var,
            18,
            cfg["timeout"]["tooltip"],
        )
        row += 1
        self.add_param_row(
            row,
            cfg["sleep_idle_seconds"]["label"] + ":",
            self.sleep_idle_seconds_var,
            18,
            cfg["sleep_idle_seconds"]["tooltip"],
        )
        row += 1
        self.add_param_row(
            row,
            cfg["tools"]["label"] + ":",
            self.tools_var,
            18,
            cfg["tools"]["tooltip"],
        )
        row += 1

        ttk.Label(self.scrollable, text="并发槽位数 (-np, --n-parallel):").grid(
            row=row, column=0, sticky=tk.W, **pad
        )
        ttk.Entry(self.scrollable, textvariable=self.n_parallel_var, width=18).grid(
            row=row, column=1, **pad
        )
        row += 1

        self.add_sep(row)
        row += 1

        ttk.Label(self.scrollable, text="对话模板 (--chat-template-kwargs):").grid(
            row=row, column=0, sticky=tk.W, **pad
        )
        self.chat_template_var = tk.StringVar()
        ttk.Entry(self.scrollable, textvariable=self.chat_template_var, width=38).grid(
            row=row, column=1, **pad
        )
        row += 1

        self.add_sep(row)
        row += 1

        self.repeat_penalty_var = tk.StringVar()
        self.repeat_last_n_var = tk.StringVar()
        self.seed_var = tk.StringVar()

        ttk.Label(self.scrollable, text="高级采样", font=("Arial", 9, "bold")).grid(
            row=row, column=0, columnspan=3, sticky=tk.W
        )
        row += 1
        self.add_param_row(
            row,
            cfg["repeat_penalty"]["label"] + ":",
            self.repeat_penalty_var,
            18,
            cfg["repeat_penalty"]["tooltip"],
        )
        row += 1
        self.add_param_row(
            row,
            cfg["repeat_last_n"]["label"] + ":",
            self.repeat_last_n_var,
            18,
            cfg["repeat_last_n"]["tooltip"],
        )
        row += 1
        self.add_param_row(
            row,
            cfg["seed"]["label"] + ":",
            self.seed_var,
            18,
            cfg["seed"]["tooltip"],
        )
        row += 1

        self.add_sep(row)
        row += 1

        self.main_gpu_var = tk.StringVar()
        self.split_mode_var = tk.StringVar()
        self.tensor_split_var = tk.StringVar()
        self.cpu_moe_var = tk.BooleanVar()
        self.n_cpu_moe_var = tk.StringVar()
        self.moe_expert_count_var = tk.StringVar()
        self.spec_draft_n_max_var = tk.StringVar()
        self.spec_draft_p_min_var = tk.StringVar()
        self.spec_type_var = tk.StringVar()
        self.n_gpu_layers_draft_var = tk.StringVar()
        self.model_draft_var = tk.StringVar()
        self.flash_attn_var = tk.StringVar()
        self.mlock_var = tk.BooleanVar()
        self.cache_type_k_var = tk.StringVar()
        self.cache_type_v_var = tk.StringVar()

        ttk.Label(self.scrollable, text="GPU 设置", font=("Arial", 9, "bold")).grid(
            row=row, column=0, columnspan=3, sticky=tk.W
        )
        row += 1

        self.add_param_row(
            row,
            cfg["main_gpu"]["label"] + ":",
            self.main_gpu_var,
            18,
            cfg["main_gpu"]["tooltip"],
        )
        row += 1

        ttk.Label(self.scrollable, text=cfg["split_mode"]["label"] + ":").grid(
            row=row, column=0, sticky=tk.W, **pad
        )
        cb = ttk.Combobox(
            self.scrollable,
            textvariable=self.split_mode_var,
            values=["", "none", "layer", "row", "tensor"],
            width=16,
            state="readonly",
        )
        cb.grid(row=row, column=1, sticky=tk.W, **pad)
        cb.bind("<MouseWheel>", lambda e: "break")
        row += 1

        self.add_param_row(
            row,
            cfg["tensor_split"]["label"] + ":",
            self.tensor_split_var,
            18,
            cfg["tensor_split"]["tooltip"],
        )
        row += 1

        ttk.Label(self.scrollable, text=cfg["flash_attn"]["label"] + ":").grid(
            row=row, column=0, sticky=tk.W, **pad
        )
        cb = ttk.Combobox(
            self.scrollable,
            textvariable=self.flash_attn_var,
            values=["auto", "on", "off"],
            width=16,
            state="readonly",
        )
        cb.grid(row=row, column=1, sticky=tk.W, **pad)
        cb.bind("<MouseWheel>", lambda e: "break")
        row += 1

        ttk.Label(self.scrollable, text=cfg["cache_type_k"]["label"] + ":").grid(
            row=row, column=0, sticky=tk.W, **pad
        )
        cb = ttk.Combobox(
            self.scrollable,
            textvariable=self.cache_type_k_var,
            values=[
                "f16",
                "f32",
                "bf16",
                "q8_0",
                "q4_0",
                "q4_1",
                "iq4_nl",
                "q5_0",
                "q5_1",
                "turbo4",
                "turbo3_tcq",
                "turbo3",
                "turbo2_tcq",
                "turbo2",
            ],
            width=16,
            state="readonly",
        )
        cb.grid(row=row, column=1, sticky=tk.W, **pad)
        cb.bind("<MouseWheel>", lambda e: "break")
        row += 1

        ttk.Label(self.scrollable, text=cfg["cache_type_v"]["label"] + ":").grid(
            row=row, column=0, sticky=tk.W, **pad
        )
        cb = ttk.Combobox(
            self.scrollable,
            textvariable=self.cache_type_v_var,
            values=[
                "f16",
                "f32",
                "bf16",
                "q8_0",
                "q4_0",
                "q4_1",
                "iq4_nl",
                "q5_0",
                "q5_1",
                "turbo4",
                "turbo3_tcq",
                "turbo3",
                "turbo2_tcq",
                "turbo2",
            ],
            width=16,
            state="readonly",
        )
        cb.grid(row=row, column=1, sticky=tk.W, **pad)
        cb.bind("<MouseWheel>", lambda e: "break")
        row += 1

        self.mlock_var = tk.BooleanVar()
        ttk.Checkbutton(
            self.scrollable, text=cfg["mlock"]["label"], variable=self.mlock_var
        ).grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=1)
        row += 1

        self.add_sep(row)
        row += 1

        ttk.Label(self.scrollable, text="MoE 设置", font=("Arial", 9, "bold")).grid(
            row=row, column=0, columnspan=3, sticky=tk.W
        )
        row += 1

        self.cpu_moe_var = tk.BooleanVar()
        ttk.Checkbutton(
            self.scrollable,
            text=cfg["cpu_moe"]["label"],
            variable=self.cpu_moe_var,
        ).grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=1)
        row += 1

        self.add_param_row(
            row,
            cfg["n_cpu_moe"]["label"] + ":",
            self.n_cpu_moe_var,
            18,
            cfg["n_cpu_moe"]["tooltip"],
        )
        row += 1


        self.add_sep(row)
        row += 1

        ttk.Label(self.scrollable, text="MTP 投机解码", font=("Arial", 9, "bold")).grid(
            row=row, column=0, columnspan=3, sticky=tk.W
        )
        row += 1

        ttk.Label(self.scrollable, text=cfg["spec_type"]["label"] + ":").grid(
            row=row, column=0, sticky=tk.W, **pad
        )
        cb = ttk.Combobox(
            self.scrollable,
            textvariable=self.spec_type_var,
            values=["", "none", "draft-simple", "draft-eagle3", "draft-mtp", "ngram-simple", "ngram-map-k", "ngram-map-k4v", "ngram-mod", "ngram-cache"],
            width=16,
            state="readonly",
        )
        cb.grid(row=row, column=1, sticky=tk.W, **pad)
        cb.bind("<MouseWheel>", lambda e: "break")
        row += 1

        self.add_param_row(
            row,
            cfg["spec_draft_n_max"]["label"] + ":",
            self.spec_draft_n_max_var,
            18,
            cfg["spec_draft_n_max"]["tooltip"],
        )
        row += 1
        self.add_param_row(
            row,
            cfg["spec_draft_p_min"]["label"] + ":",
            self.spec_draft_p_min_var,
            18,
            cfg["spec_draft_p_min"]["tooltip"],
        )
        row += 1
        self.add_param_row(
            row,
            cfg["n_gpu_layers_draft"]["label"] + ":",
            self.n_gpu_layers_draft_var,
            18,
            cfg["n_gpu_layers_draft"]["tooltip"],
        )
        row += 1

        ttk.Label(self.scrollable, text=cfg["model_draft"]["label"] + ":").grid(
            row=row, column=0, sticky=tk.W, **pad
        )
        self.model_draft_entry = ttk.Entry(
            self.scrollable, textvariable=self.model_draft_var, width=38
        )
        self.model_draft_entry.grid(row=row, column=1, sticky=tk.EW, **pad)
        ttk.Button(self.scrollable, text="浏览", command=self.browse_model_draft).grid(
            row=row, column=2, **pad
        )
        row += 1

        self.add_sep(row)
        row += 1

        ttk.Label(self.scrollable, text="功能选项", font=("Arial", 9, "bold")).grid(
            row=row, column=0, columnspan=3, sticky=tk.W
        )
        row += 1

        self.verbose_var = tk.BooleanVar()
        ttk.Checkbutton(
            self.scrollable, text="详细日志", variable=self.verbose_var
        ).grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=1)
        row += 1
        self.webui_var = tk.BooleanVar()
        ttk.Checkbutton(
            self.scrollable, text="启用 WebUI", variable=self.webui_var
        ).grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=1)
        row += 1
        self.embeddings_var = tk.BooleanVar()
        ttk.Checkbutton(
            self.scrollable, text="启用 Embeddings", variable=self.embeddings_var
        ).grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=1)
        row += 1

        ttk.Label(self.scrollable, text="日志级别 (--log-verbosity):").grid(
            row=row, column=0, sticky=tk.W, **pad
        )
        self.log_verbosity_var = tk.StringVar()
        cb = ttk.Combobox(
            self.scrollable,
            textvariable=self.log_verbosity_var,
            values=["0", "1", "2", "3", "4", "5"],
            width=16,
            state="readonly",
        )
        cb.grid(row=row, column=1, sticky=tk.W, **pad)
        cb.bind("<MouseWheel>", lambda e: "break")
        row += 1

        self.add_sep(row)
        row += 1
        ttk.Label(self.scrollable, text="额外参数", font=("Arial", 9, "bold")).grid(
            row=row, column=0, columnspan=3, sticky=tk.W
        )
        row += 1
        self.custom_args_var = tk.StringVar()
        ttk.Label(self.scrollable, text="自定义参数:").grid(
            row=row, column=0, sticky=tk.W, **pad
        )
        ttk.Entry(self.scrollable, textvariable=self.custom_args_var, width=38).grid(
            row=row, column=1, columnspan=2, sticky=tk.EW, **pad
        )
        row += 1
        ttk.Label(
            self.scrollable,
            text="示例: --no-kv-offload -ngl 20 --cont-batching",
            font=("Arial", 7),
            foreground="gray",
        ).grid(row=row, column=0, columnspan=3, sticky=tk.W, **pad)
        row += 1

    def add_param_row(self, row, label, var, width, tooltip=""):
        lbl = ttk.Label(self.scrollable, text=label)
        lbl.grid(row=row, column=0, sticky=tk.W, padx=3, pady=2)
        if tooltip:
            self.create_tooltip(lbl, tooltip)
        entry = ttk.Entry(self.scrollable, textvariable=var, width=width)
        entry.grid(row=row, column=1, sticky=tk.W, padx=3, pady=2)
        if tooltip:
            self.create_tooltip(entry, tooltip)

    def create_tooltip(self, widget, text):
        tooltip = tk.Toplevel(widget)
        tooltip.wm_overrideredirect(True)
        tooltip.withdraw()
        label = ttk.Label(
            tooltip,
            text=text,
            background="#ffffe0",
            relief=tk.SOLID,
            borderwidth=1,
            padding=5,
        )
        label.pack()

        def on_enter(event):
            x = widget.winfo_rootx()
            y = widget.winfo_rooty() + widget.winfo_height() + 5
            tooltip.wm_geometry(f"+{x}+{y}")
            tooltip.deiconify()

        def on_leave(event):
            tooltip.withdraw()

        widget.bind("<Enter>", on_enter)
        widget.bind("<Leave>", on_leave)

    def add_sep(self, row):
        ttk.Separator(self.scrollable, orient=tk.HORIZONTAL).grid(
            row=row, column=0, columnspan=3, sticky=tk.EW, pady=4
        )

    def build_right_panel(self, parent):
        btn_frame = ttk.Frame(parent)
        btn_frame.pack(fill=tk.X, pady=(0, 5))

        self.start_btn = ttk.Button(
            btn_frame, text="启动服务器", command=self.start_server
        )
        self.start_btn.pack(side=tk.LEFT, padx=2)
        self.stop_btn = ttk.Button(
            btn_frame, text="停止服务器", command=self.stop_server, state=tk.DISABLED
        )
        self.stop_btn.pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="保存配置", command=self.save_config).pack(
            side=tk.LEFT, padx=2
        )
        ttk.Button(btn_frame, text="打开 WebUI", command=self.open_webui).pack(
            side=tk.LEFT, padx=2
        )

        openclaw_frame = ttk.Frame(parent)
        openclaw_frame.pack(fill=tk.X, pady=(5, 0))
        ttk.Button(
            openclaw_frame, text="开启 OpenClaw", command=self.start_openclaw
        ).pack(side=tk.LEFT, padx=2)
        ttk.Button(
            openclaw_frame, text="关闭 OpenClaw", command=self.stop_openclaw
        ).pack(side=tk.LEFT, padx=2)

        status_frame = ttk.LabelFrame(parent, text="服务器状态", padding=5)
        status_frame.pack(fill=tk.X, pady=(0, 5))

        self.server_status_label = ttk.Label(
            status_frame, text="未运行", font=("Arial", 10, "bold")
        )
        self.server_status_label.pack(anchor=tk.W)

        gpu_frame = ttk.LabelFrame(parent, text="进程信息", padding=5)
        gpu_frame.pack(fill=tk.X, pady=(0, 5))

        ttk.Label(gpu_frame, text="运行状态:").grid(
            row=0, column=0, sticky=tk.W, pady=2
        )
        self.gpu_status_var = tk.StringVar(value="-")
        ttk.Label(
            gpu_frame, textvariable=self.gpu_status_var, font=("Arial", 9, "bold")
        ).grid(row=0, column=1, sticky=tk.W, pady=2)

        ttk.Label(gpu_frame, text="PID:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.pid_var = tk.StringVar(value="-")
        ttk.Label(gpu_frame, textvariable=self.pid_var).grid(
            row=1, column=1, sticky=tk.W, pady=2
        )

        log_frame = ttk.LabelFrame(parent, text="日志输出", padding=5)
        log_frame.pack(fill=tk.BOTH, expand=True, pady=(5, 0))

        self.log_text = tk.Text(
            log_frame,
            height=10,
            width=40,
            wrap=tk.WORD,
            font=("Consolas", 8),
            bg="black",
            fg="#00ff00",
        )
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        log_scroll = ttk.Scrollbar(log_frame, command=self.log_text.yview)
        log_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.config(yscrollcommand=log_scroll.set, state=tk.DISABLED)

        btn_bar = ttk.Frame(parent)
        btn_bar.pack(fill=tk.X, pady=(5, 0))
        ttk.Button(btn_bar, text="清空日志", command=self.clear_log).pack(side=tk.LEFT)

        self.log_queue = queue.Queue()
        self.log_thread = None
        self.running = False
        self.max_log_lines = 999999
        self.log_lines = []

        self.update_gpu_info()

    def update_gpu_info(self):
        if self.process and self.process.poll() is None:
            self.server_status_label.config(text="运行中", foreground="green")
            self.gpu_status_var.set("是")
            self.pid_var.set(str(self.process.pid))
        else:
            self.server_status_label.config(text="未运行", foreground="red")
            self.gpu_status_var.set("否")
            self.pid_var.set("-")

        if hasattr(self, "root"):
            self.root.after(2000, self.update_gpu_info)

    def load_config_to_ui(self):
        self.server_path_var.set(self.config.get("llama_server_path", ""))
        model = self.config.get("model", "")
        self.model_path_var.set(model)

        if model:
            basename = os.path.basename(model)
            if basename in self.models:
                self.model_combo_var.set(basename)

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
        self.model_combo["values"] = self.models
        current = self.model_path_var.get()
        if current:
            basename = os.path.basename(current)
            if basename in self.models:
                self.model_combo_var.set(basename)

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

    def log(self, message):
        print(f"[LlamaLauncher] {message}")
        self.log_queue.put(message)

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

        return cmd

    def start_server(self):
        if self.process is not None:
            return

        cmd = self.build_command()

        try:
            self.log("=" * 60)
            self.log("=== 启动参数配置 ===")
            self.log("=" * 60)
            for i in range(1, len(cmd)):
                if cmd[i].startswith("-"):
                    if i + 1 < len(cmd) and not cmd[i + 1].startswith("-"):
                        self.log(f"  {cmd[i]}: {cmd[i+1]}")
                    else:
                        self.log(f"  {cmd[i]}")
            self.log("=" * 60)
            cmd_str = " ".join(f'"{c}"' for c in cmd)
            self.log(f"完整命令: {cmd_str}")
            startupinfo = None
            if sys.platform == "win32":
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = subprocess.SW_HIDE
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                startupinfo=startupinfo,
            )
            self.running = True
            self.log_thread = threading.Thread(target=self.read_output, daemon=True)
            self.log_thread.start()
            self.start_btn.configure(state=tk.DISABLED)
            self.stop_btn.configure(state=tk.NORMAL)
            self.root.after(3000, self.check_server_ready)
            self.root.after(300, self.update_log_display)
        except Exception as e:
            messagebox.showerror("错误", f"启动失败: {str(e)}")
            self.start_btn.configure(state=tk.NORMAL)
            self.stop_btn.configure(state=tk.DISABLED)

    def read_output(self):
        try:
            for line in iter(self.process.stdout.readline, b""):
                if not self.running:
                    break
                if line:
                    self.log_queue.put(line.decode("utf-8", errors="replace"))
        except Exception:
            pass

    def update_log_display(self):
        new_lines = []
        try:
            while not self.log_queue.empty():
                line = self.log_queue.get_nowait()
                stripped = line.rstrip("\n")
                self.log_lines.append(stripped)
                new_lines.append(stripped)
        except queue.Empty:
            pass

        if new_lines:
            self.log_text.config(state=tk.NORMAL)
            self.log_text.insert(tk.END, "\n".join(new_lines) + "\n")
            self.log_text.see(tk.END)
            self.log_text.config(state=tk.DISABLED)

        if hasattr(self, "root") and self.running:
            self.root.after(300, self.update_log_display)

    def clear_log(self):
        self.log_lines = []
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state=tk.DISABLED)

    def check_server_ready(self):
        import threading
        import socket

        def check():
            host = self.host_var.get().strip()
            port = int(self.port_var.get().strip())
            for _ in range(30):
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(1)
                    result = sock.connect_ex(
                        (host if host != "0.0.0.0" else "127.0.0.1", port)
                    )
                    sock.close()
                    if result == 0:
                        self.root.after(
                            0,
                            lambda: self.server_status_label.config(
                                text="已就绪", foreground="blue"
                            ),
                        )
                        return
                except:
                    pass
                time.sleep(1)
            self.root.after(
                0,
                lambda: self.server_status_label.config(
                    text="启动超时", foreground="orange"
                ),
            )

        threading.Thread(target=check, daemon=True).start()

    def stop_server(self):
        if self.process is None:
            return
        self.running = False
        try:
            self.process.terminate()
            self.process.wait(timeout=5)
        except Exception:
            self.process.kill()
        self.process = None
        self.start_btn.configure(state=tk.NORMAL)
        self.stop_btn.configure(state=tk.DISABLED)
        self.log("服务器已停止")

    def start_openclaw(self):
        if self.openclaw_process is not None:
            self.log("OpenClaw已在运行!")
            return
        try:
            self.openclaw_process = subprocess.Popen(
                ["cmd", "/c", "openclaw gateway run"],
                creationflags=(
                    subprocess.CREATE_NEW_CONSOLE if sys.platform == "win32" else 0
                ),
            )
            self.log("OpenClaw已启动，PID: " + str(self.openclaw_process.pid))
        except Exception as e:
            self.log("启动OpenClaw失败: " + str(e))

    def stop_openclaw(self):
        if self.openclaw_process is None:
            return

        def kill_process():
            try:
                subprocess.Popen(
                    ["taskkill", "/F", "/T", "/PID", str(self.openclaw_process.pid)],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
            except Exception:
                pass
            self.openclaw_process = None
            self.log("OpenClaw已停止")

        threading.Thread(target=kill_process, daemon=True).start()

    def on_closing(self):
        self.stop_server()
        self.root.destroy()

    def open_webui(self):
        import webbrowser

        host = self.host_var.get().strip()
        if host == "0.0.0.0":
            host = "127.0.0.1"
        webbrowser.open(f"http://{host}:{self.port_var.get().strip()}")

    def save_config(self):
        chat_template = self.chat_template_var.get().strip()

        self.config.update(
            {
                "llama_server_path": self.server_path_var.get().strip(),
                "model": self.model_path_var.get().strip(),
                "host": self.host_var.get().strip(),
                "port": int(self.port_var.get().strip()),
                "ctx_size": int(self.ctx_size_var.get().strip()),
                "threads": int(self.threads_var.get().strip()),
                "threads_batch": int(self.threads_batch_var.get().strip() or 0),
                 "n_predict": int(self.n_predict_var.get().strip()),
                "n_gpu_layers": int(self.n_gpu_layers_var.get().strip()),
                "batch_size": int(self.batch_size_var.get().strip()),
                "ubatch_size": int(self.ubatch_size_var.get().strip() or 0),
                "temp": float(self.temp_var.get().strip()),
                "top_k": int(self.top_k_var.get().strip()),
                "top_p": float(self.top_p_var.get().strip()),
                "min_p": float(self.min_p_var.get().strip()),
                "presence_penalty": float(self.presence_penalty_var.get().strip()),
                "repeat_penalty": float(self.repeat_penalty_var.get().strip() or 1.0),
                "repeat_last_n": int(self.repeat_last_n_var.get().strip() or 64),
                "seed": int(self.seed_var.get().strip() or -1),
                "timeout": int(self.timeout_var.get().strip() or 0),
               "sleep_idle_seconds": int(
                    self.sleep_idle_seconds_var.get().strip() or 0
                ),
                "n_parallel": int(self.n_parallel_var.get().strip() or -1),
                "tools": self.tools_var.get().strip(),
                "chat_template_kwargs": chat_template,
                "main_gpu": int(self.main_gpu_var.get().strip() or 0),
                "split_mode": self.split_mode_var.get().strip(),
                "tensor_split": self.tensor_split_var.get().strip(),
                "cpu_moe": self.cpu_moe_var.get(),
              "n_cpu_moe": int(self.n_cpu_moe_var.get().strip() or -1),
                "moe_expert_count": int(self.moe_expert_count_var.get().strip() or -1),
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
                "log_verbosity": int(self.log_verbosity_var.get().strip()),
                "mmproj": self.mmproj_path_var.get().strip(),
                "mmproj_enabled": self.mmproj_enabled_var.get(),
                "custom_args": self.custom_args_var.get().strip(),
            }
        )

        with open(self.config_file, "w", encoding="utf-8") as f:
            toml_dump(self.config, f)

        self.log("配置已保存到 config.toml")
        messagebox.showinfo("成功", "配置已保存!")


def main():
    root = tk.Tk()
    app = LlamaLauncher(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()


if __name__ == "__main__":
    main()
