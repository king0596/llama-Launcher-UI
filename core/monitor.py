import tkinter as tk
import threading
import time
import re
import json
import urllib.request
import urllib.error

try:
    import customtkinter as ctk
except ImportError:
    ctk = None

try:
    import psutil
except ImportError:
    psutil = None

try:
    import pynvml
except ImportError:
    pynvml = None

from config import COLORS


# 异常关键词（中英双语），分一般与严重两级
_ERROR_RE = re.compile(
    r"(error|exception|traceback|failed|fatal|aborted|"
    r"segmentation\s+fault|cuda\s+error|out\s+of\s+memory|"
    r"cannot |could not|unable to|crash|killed|"
    r"错误|失败|异常|致命|崩溃|无法|超时|中断)",
    re.IGNORECASE,
)
_CRITICAL_RE = re.compile(
    r"(fatal|exception|traceback|cuda\s+error|out\s+of\s+memory|"
    r"segmentation\s+fault|crash|killed|"
    r"致命|异常|崩溃|错误|中断)",
    re.IGNORECASE,
)

# /metrics 端点的累计计数器（Prometheus 格式），不会因请求结束而清零
_METRIC_PROMPT_RE = re.compile(
    r"^(?!#).*(?:llamacpp:)?prompt_tokens_total\s+(\d+)", re.MULTILINE
)
_METRIC_PREDICT_RE = re.compile(
    r"^(?!#).*(?:llamacpp:)?tokens_predicted_total\s+(\d+)", re.MULTILINE
)


class MonitorMixin:
    """监控 mixin：硬件性能、token 统计、异常捕获。"""

    # ---- 初始化 ----
    def init_monitor(self):
        self._psutil = psutil
        self._pynvml = pynvml
        self._nvml_ready = False
        self._gpu_handles = []
        self._monitor_active = False
        self._monitor_after_id = None
        # token 统计（/metrics 累计计数器为主，/slots 为回退）
        self._token_total_prompt = 0
        self._token_total_predicted = 0
        self._slot_prev = {}
        self._last_token_time = 0.0
        self._last_token_prompt = 0
        self._last_token_predicted = 0
        self._token_rate_in = 0.0
        self._token_rate_out = 0.0
        # /metrics 累计计数器相关
        self._metric_raw_prompt = -1   # 最近一次从 /metrics 读到的原始累计值
        self._metric_raw_predicted = -1
        self._metric_offset_prompt = 0  # “重置统计”时记录的基线偏移
        self._metric_offset_predicted = 0
        # 异常捕获
        self._exceptions = []
        self._last_scanned = 0
        self._ex_max = 500

    # ---- NVML 初始化 / 释放 ----
    def _init_nvml(self):
        if self._pynvml is None or self._nvml_ready:
            return
        try:
            self._pynvml.nvmlInit()
            count = self._pynvml.nvmlDeviceGetCount()
            self._gpu_handles = [
                self._pynvml.nvmlDeviceGetHandleByIndex(i) for i in range(count)
            ]
            self._nvml_ready = True
        except Exception:
            self._nvml_ready = False
            self._gpu_handles = []

    def _shutdown_nvml(self):
        if self._nvml_ready:
            try:
                self._pynvml.nvmlShutdown()
            except Exception:
                pass
            self._nvml_ready = False
            self._gpu_handles = []

    # ---- 监控生命周期 ----
    def start_monitoring(self):
        if self._monitor_active:
            return
        self._init_nvml()
        self._monitor_active = True
        self._last_scanned = len(getattr(self, "log_lines", []))
        self._monitor_tick()

    def stop_monitoring(self):
        self._monitor_active = False
        if self._monitor_after_id is not None:
            try:
                self.root.after_cancel(self._monitor_after_id)
            except Exception:
                pass
            self._monitor_after_id = None
        self._shutdown_nvml()

    def _monitor_tick(self):
        if not self._monitor_active:
            return
        try:
            self._update_hardware()
            self._poll_tokens_async()
            self._scan_exceptions()
        except Exception:
            pass
        self._monitor_after_id = self.root.after(2000, self._monitor_tick)

    # ---- 硬件指标 ----
    def _update_hardware(self):
        if not hasattr(self, "hw_cpu_bar"):
            return
        C = self.COLORS
        # CPU / 内存
        if self._psutil is not None:
            try:
                cpu = self._psutil.cpu_percent(interval=None)
                self.hw_cpu_bar.set(max(0.0, min(1.0, cpu / 100.0)))
                self.hw_cpu_val.set(f"{cpu:.0f}%")
                vm = self._psutil.virtual_memory()
                self.hw_ram_bar.set(vm.percent / 100.0)
                self.hw_ram_val.set(
                    f"{vm.percent:.0f}%  ({self._fmt_bytes(vm.used)}/{self._fmt_bytes(vm.total)})"
                )
            except Exception:
                self.hw_cpu_val.set("读取失败")
                self.hw_ram_val.set("读取失败")
        else:
            self.hw_cpu_val.set("未安装 psutil")
            self.hw_ram_val.set("未安装 psutil")
        # GPU
        if self._nvml_ready and self._gpu_handles:
            try:
                h = self._gpu_handles[0]
                util = self._pynvml.nvmlDeviceGetUtilizationRates(h)
                gpu_pct = float(util.gpu)
                self.hw_gpu_bar.set(max(0.0, min(1.0, gpu_pct / 100.0)))
                self.hw_gpu_val.set(f"{util.gpu}%")
                mem = self._pynvml.nvmlDeviceGetMemoryInfo(h)
                vram_pct = (mem.used / mem.total) if mem.total else 0.0
                self.hw_vram_bar.set(vram_pct)
                self.hw_vram_val.set(
                    f"{self._fmt_bytes(mem.used)}/{self._fmt_bytes(mem.total)}"
                )
                temp = self._pynvml.nvmlDeviceGetTemperature(
                    h, self._pynvml.NVML_TEMPERATURE_GPU
                )
                self.hw_gpu_temp_var.set(f"{temp} °C")
                color = (
                    C["success_text"] if temp < 70
                    else (C["warning_text"] if temp < 85 else C["danger_text"])
                )
                self.hw_gpu_temp_lbl.configure(text_color=color)
            except Exception:
                self.hw_gpu_val.set("读取失败")
                self.hw_vram_val.set("—")
                self.hw_gpu_temp_var.set("—")
        else:
            self.hw_gpu_val.set("未检测到 NVIDIA GPU")
            self.hw_vram_val.set("—")
            self.hw_gpu_temp_var.set("—")

    @staticmethod
    def _fmt_bytes(n):
        gb = n / (1024 ** 3)
        if gb >= 1:
            return f"{gb:.1f}GB"
        mb = n / (1024 ** 2)
        return f"{mb:.0f}MB"

    # ---- token 统计 ----
    def _poll_tokens_async(self):
        if not (self.process and self.process.poll() is None):
            return
        host = self.host_var.get().strip() or "127.0.0.1"
        if host == "0.0.0.0":
            host = "127.0.0.1"
        port = self.port_var.get().strip() or "8080"
        base = f"http://{host}:{port}"

        def worker():
            # 优先 /metrics：累计计数器，不会因请求结束而清零
            try:
                req = urllib.request.Request(
                    base + "/metrics", headers={"Connection": "close"}
                )
                with urllib.request.urlopen(req, timeout=2) as resp:
                    text = resp.read().decode("utf-8", errors="replace")
                p = self._parse_metric(text, _METRIC_PROMPT_RE)
                o = self._parse_metric(text, _METRIC_PREDICT_RE)
                if p is not None and o is not None:
                    self.root.after(0, lambda: self._apply_metrics(p, o))
                    return
            except Exception:
                pass
            # 回退 /slots（旧版本或未启用 --metrics 时）
            try:
                req = urllib.request.Request(
                    base + "/slots", headers={"Connection": "close"}
                )
                with urllib.request.urlopen(req, timeout=2) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                self.root.after(0, lambda: self._apply_tokens(data))
            except Exception:
                pass

        threading.Thread(target=worker, daemon=True).start()

    @staticmethod
    def _parse_metric(text, pattern):
        m = pattern.search(text)
        return int(m.group(1)) if m else None

    def _apply_metrics(self, prompt_total, predicted_total):
        # 服务重启时计数器会归零：检测到回退则重置偏移基线
        if self._metric_raw_prompt >= 0 and prompt_total < self._metric_raw_prompt:
            self._metric_offset_prompt = 0
        if self._metric_raw_predicted >= 0 and predicted_total < self._metric_raw_predicted:
            self._metric_offset_predicted = 0
        self._metric_raw_prompt = prompt_total
        self._metric_raw_predicted = predicted_total
        # 显示值 = 累计值 - 重置偏移
        disp_in = max(0, prompt_total - self._metric_offset_prompt)
        disp_out = max(0, predicted_total - self._metric_offset_predicted)
        # 速率
        now = time.time()
        if self._last_token_time:
            dt = now - self._last_token_time
            if dt > 0:
                dp = disp_in - self._last_token_prompt
                do = disp_out - self._last_token_predicted
                if dp >= 0:
                    self._token_rate_in = dp / dt
                if do >= 0:
                    self._token_rate_out = do / dt
        self._last_token_time = now
        self._last_token_prompt = disp_in
        self._last_token_predicted = disp_out
        self.token_in_var.set(f"{disp_in:,}")
        self.token_out_var.set(f"{disp_out:,}")
        self.token_total_var.set(f"{disp_in + disp_out:,}")
        self.token_rate_var.set(
            f"↑{self._token_rate_in:.1f} / ↓{self._token_rate_out:.1f} t/s"
        )

    def _apply_tokens(self, data):
        """/slots 回退路径：累积各槽位统计，处理槽位复用重置。"""
        if not isinstance(data, list):
            return
        cur_prompt = 0
        cur_predicted = 0
        for slot in data:
            sid = slot.get("id", 0)
            p = int(slot.get("n_prompt_tokens", 0))
            o = int(slot.get("n_tokens_predicted", 0))
            prev = self._slot_prev.get(sid, (0, 0))
            # 检测槽位复用：当前值小于历史值，说明已重置 → 把历史值累加到总量
            if p < prev[0]:
                self._token_total_prompt += prev[0]
            if o < prev[1]:
                self._token_total_predicted += prev[1]
            self._slot_prev[sid] = (p, o)
            cur_prompt = max(cur_prompt, p)
            cur_predicted = max(cur_predicted, o)
        # 速率
        now = time.time()
        if self._last_token_time:
            dt = now - self._last_token_time
            if dt > 0:
                dp = cur_prompt - self._last_token_prompt
                do = cur_predicted - self._last_token_predicted
                if dp >= 0:
                    self._token_rate_in = dp / dt
                if do >= 0:
                    self._token_rate_out = do / dt
        self._last_token_time = now
        self._last_token_prompt = cur_prompt
        self._last_token_predicted = cur_predicted
        total_in = self._token_total_prompt + cur_prompt
        total_out = self._token_total_predicted + cur_predicted
        self.token_in_var.set(f"{total_in:,}")
        self.token_out_var.set(f"{total_out:,}")
        self.token_total_var.set(f"{total_in + total_out:,}")
        self.token_rate_var.set(f"↑{self._token_rate_in:.1f} / ↓{self._token_rate_out:.1f} t/s")

    def reset_token_stats(self):
        # /metrics 模式：以当前累计值为新基线，显示归零
        if self._metric_raw_prompt >= 0:
            self._metric_offset_prompt = self._metric_raw_prompt
        if self._metric_raw_predicted >= 0:
            self._metric_offset_predicted = self._metric_raw_predicted
        # /slots 回退模式状态清零
        self._token_total_prompt = 0
        self._token_total_predicted = 0
        self._slot_prev = {}
        self._last_token_time = 0.0
        self._last_token_prompt = 0
        self._last_token_predicted = 0
        self._token_rate_in = 0.0
        self._token_rate_out = 0.0
        self.token_in_var.set("0")
        self.token_out_var.set("0")
        self.token_total_var.set("0")
        self.token_rate_var.set("0 / 0")

    # ---- 异常捕获 ----
    def _scan_exceptions(self):
        lines = getattr(self, "log_lines", [])
        if len(lines) <= self._last_scanned:
            return
        new = lines[self._last_scanned:]
        self._last_scanned = len(lines)
        ts = time.strftime("%H:%M:%S")
        for line in new:
            if _ERROR_RE.search(line):
                level = "错误" if _CRITICAL_RE.search(line) else "警告"
                self._exceptions.append((ts, level, line.strip()))
        if len(self._exceptions) > self._ex_max:
            self._exceptions = self._exceptions[-self._ex_max:]
        self._render_exceptions()

    def _render_exceptions(self):
        if not hasattr(self, "ex_text"):
            return
        C = self.COLORS
        count = len(self._exceptions)
        self.ex_count_var.set(f"{count} 条" if count else "无异常")
        self.ex_count_lbl.configure(
            text_color=C["danger_text"] if count else C["success_text"]
        )
        self.ex_text.configure(state=tk.NORMAL)
        self.ex_text.delete(1.0, tk.END)
        tag_err = "err"
        tag_warn = "warn"
        self.ex_text.tag_configure(tag_err, foreground=C["danger_text"])
        self.ex_text.tag_configure(tag_warn, foreground=C["warning_text"])
        for ts, level, text in self._exceptions[-200:]:
            tag = tag_err if level == "错误" else tag_warn
            self.ex_text.insert(tk.END, f"[{ts}] [{level}] ", tag)
            self.ex_text.insert(tk.END, text + "\n")
        self.ex_text.see(tk.END)
        self.ex_text.configure(state=tk.DISABLED)

    def clear_exceptions(self):
        self._exceptions = []
        self._render_exceptions()

    def copy_exceptions(self):
        if not self._exceptions:
            return
        text = "\n".join(
            f"[{ts}] [{lvl}] {t}" for ts, lvl, t in self._exceptions
        )
        self.root.clipboard_clear()
        self.root.clipboard_append(text)

    # ============== 侧边栏 UI 构建 ==============
    def build_monitor_sidebar(self, parent):
        C = self.COLORS
        parent.grid_rowconfigure(2, weight=1)

        # ---- 硬件监控卡片 ----
        hw = self.card(parent, "🖥 硬件监控")
        hw.grid(row=0, column=0, sticky="ew", pady=(8, 6))
        hw_body = ctk.CTkFrame(hw, fg_color="transparent")
        hw_body.grid(row=2, column=0, sticky="ew", padx=10, pady=(0, 10))
        hw_body.grid_columnconfigure(0, weight=1)
        hw_body.grid_columnconfigure(1, weight=0)

        self.hw_cpu_bar, self.hw_cpu_val = self._monitor_bar(hw_body, 0, "CPU 使用率")
        self.hw_ram_bar, self.hw_ram_val = self._monitor_bar(hw_body, 2, "内存使用")
        self.hw_gpu_bar, self.hw_gpu_val = self._monitor_bar(hw_body, 4, "GPU 使用率")
        self.hw_vram_bar, self.hw_vram_val = self._monitor_bar(hw_body, 6, "GPU 显存")

        ctk.CTkLabel(
            hw_body, text="GPU 温度",
            text_color=C["text_secondary"],
            font=("Microsoft YaHei UI", 11), anchor="w",
        ).grid(row=8, column=0, sticky="w", padx=2, pady=(4, 0))
        self.hw_gpu_temp_var = tk.StringVar(value="—")
        self.hw_gpu_temp_lbl = ctk.CTkLabel(
            hw_body, textvariable=self.hw_gpu_temp_var,
            font=("Consolas", 12, "bold"), text_color=C["text_primary"],
        )
        self.hw_gpu_temp_lbl.grid(row=8, column=1, sticky="e", padx=2, pady=(4, 0))

        # ---- token 统计卡片 ----
        tk_card = self.card(parent, "📊 Token 统计")
        tk_card.grid(row=1, column=0, sticky="ew", pady=6)
        tk_body = ctk.CTkFrame(tk_card, fg_color="transparent")
        tk_body.grid(row=2, column=0, sticky="ew", padx=10, pady=(0, 10))
        tk_body.grid_columnconfigure(1, weight=1)

        self.token_in_var = tk.StringVar(value="0")
        self.token_out_var = tk.StringVar(value="0")
        self.token_total_var = tk.StringVar(value="0")
        self.token_rate_var = tk.StringVar(value="0 / 0")
        self._stat_row(tk_body, 0, "📥 输入 tokens", self.token_in_var)
        self._stat_row(tk_body, 1, "📤 输出 tokens", self.token_out_var)
        self._stat_row(tk_body, 2, "∑ 总计", self.token_total_var)
        self._stat_row(tk_body, 3, "⚡ 实时速率", self.token_rate_var)

        ctk.CTkButton(
            tk_body, text="重置统计", width=80, height=26, corner_radius=6,
            command=self.reset_token_stats, fg_color=C["tab_bg"],
            hover_color=C["card_border"], text_color=C["text_primary"],
            font=("Microsoft YaHei UI", 10),
        ).grid(row=4, column=0, columnspan=2, sticky="w", pady=(6, 0))

        # ---- 异常捕获卡片 ----
        ex = self.card(parent, "⚠ 异常捕获")
        ex.grid(row=2, column=0, sticky="nsew", pady=6)
        ex.grid_rowconfigure(3, weight=1)
        ex_body = ctk.CTkFrame(ex, fg_color="transparent")
        ex_body.grid(row=2, column=0, sticky="ew", padx=10, pady=(0, 4))
        ex_body.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            ex_body, text="捕获数量:",
            text_color=C["text_secondary"],
            font=("Microsoft YaHei UI", 11),
        ).grid(row=0, column=0, sticky="w", padx=2)
        self.ex_count_var = tk.StringVar(value="无异常")
        self.ex_count_lbl = ctk.CTkLabel(
            ex_body, textvariable=self.ex_count_var,
            font=("Microsoft YaHei UI", 11, "bold"),
            text_color=C["success_text"],
        )
        self.ex_count_lbl.grid(row=0, column=1, sticky="w", padx=(4, 2))

        self.ex_text = tk.Text(
            ex, height=8, wrap=tk.WORD,
            font=("Consolas", 10),
            bg=C["dark_bg"], fg=C["dark_text"],
            relief=tk.FLAT, borderwidth=0, padx=8, pady=8,
            insertbackground=C["dark_text"],
        )
        self.ex_text.grid(row=3, column=0, sticky="nsew", padx=10, pady=(0, 6))
        self.ex_text.configure(state=tk.DISABLED)

        btns = ctk.CTkFrame(ex, fg_color="transparent")
        btns.grid(row=4, column=0, sticky="ew", padx=10, pady=(0, 10))
        ctk.CTkButton(
            btns, text="🗑 清空", width=80, height=26, corner_radius=6,
            command=self.clear_exceptions, fg_color=C["tab_bg"],
            hover_color=C["card_border"], text_color=C["text_primary"],
            font=("Microsoft YaHei UI", 10),
        ).pack(side=tk.LEFT)
        ctk.CTkButton(
            btns, text="📋 复制", width=80, height=26, corner_radius=6,
            command=self.copy_exceptions, fg_color=C["tab_bg"],
            hover_color=C["card_border"], text_color=C["text_primary"],
            font=("Microsoft YaHei UI", 10),
        ).pack(side=tk.LEFT, padx=(4, 0))

    def _monitor_bar(self, parent, row, label):
        C = self.COLORS
        ctk.CTkLabel(
            parent, text=label, text_color=C["text_secondary"],
            font=("Microsoft YaHei UI", 11), anchor="w",
        ).grid(row=row, column=0, sticky="w", padx=2, pady=(4, 0))
        val = tk.StringVar(value="—")
        ctk.CTkLabel(
            parent, textvariable=val, font=("Consolas", 10),
            text_color=C["text_primary"],
        ).grid(row=row, column=1, sticky="e", padx=2, pady=(4, 0))
        bar = ctk.CTkProgressBar(
            parent, height=14, corner_radius=6,
            progress_color=C["primary"], fg_color=C["tab_bg"],
        )
        bar.grid(row=row + 1, column=0, columnspan=2, sticky="ew", padx=2, pady=(0, 6))
        bar.set(0)
        return bar, val

    def _stat_row(self, parent, row, label, var):
        C = self.COLORS
        ctk.CTkLabel(
            parent, text=label, text_color=C["text_secondary"],
            font=("Microsoft YaHei UI", 11), anchor="w",
        ).grid(row=row, column=0, sticky="w", padx=2, pady=3)
        ctk.CTkLabel(
            parent, textvariable=var, font=("Consolas", 12, "bold"),
            text_color=C["text_primary"], anchor="e",
        ).grid(row=row, column=1, sticky="e", padx=2, pady=3)
