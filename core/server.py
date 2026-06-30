import tkinter as tk
import subprocess
import sys
import time
import socket
import threading
import queue
import os
from tkinter import messagebox

try:
    import customtkinter as ctk
except ImportError:
    ctk = None

from config import COLORS


class ServerMixin:
    """服务进程管理 mixin：启动/停止、日志、状态监控。"""

    def log(self, message):
        print(f"[LlamaLauncher] {message}")
        self.log_queue.put(message)

    def set_server_status(self, text):
        C = self.COLORS
        colors = {
            "未运行": (C["danger_bg"], C["danger_text"]),
            "已停止": (C["danger_bg"], C["danger_text"]),
            "启动失败": (C["danger_bg"], C["danger_text"]),
            "启动中": (C["warning_bg"], C["warning_text"]),
            "启动超时": (C["warning_bg"], C["warning_text"]),
            "运行中": (C["success_bg"], C["success_text"]),
            "已就绪": ("#dbeafe", "#2563eb"),
        }
        bg, fg = colors.get(text, (C["tab_bg"], C["text_secondary"]))
        self.status_pill.configure(text=text, fg_color=bg, text_color=fg)

    def update_gpu_info(self):
        if self.process and self.process.poll() is None:
            current = self.status_pill.cget("text")
            if current not in ("启动中", "已就绪", "启动超时"):
                self.set_server_status("运行中")
            self.gpu_status_var.set("是")
            self.pid_var.set(str(self.process.pid))
        else:
            current = self.status_pill.cget("text")
            if current not in ("未运行", "已停止", "启动失败"):
                self.set_server_status("已停止")
                self.show_config_view()
            elif current == "未运行":
                self.set_server_status("未运行")
            self.gpu_status_var.set("否")
            self.pid_var.set("-")

        if hasattr(self, "root"):
            self.root.after(2000, self.update_gpu_info)

    def update_runtime_summary(self):
        model = self.model_path_var.get().strip()
        self.runtime_model_var.set(os.path.basename(model) if model else "-")
        host = self.host_var.get().strip() or "127.0.0.1"
        if host == "0.0.0.0":
            host = "127.0.0.1"
        port = self.port_var.get().strip() or "-"
        self.runtime_url_var.set(f"http://{host}:{port}" if port != "-" else "-")
        if getattr(self, "server_started_at", None):
            self.runtime_started_var.set(self.server_started_at)
        else:
            self.runtime_started_var.set("-")

    def start_server(self):
        if self.process is not None:
            return

        if not self.save_config(show_message=False):
            return
        cmd = self.build_command()
        self.last_launch_command = self.format_command(cmd)
        self.update_command_preview()

        try:
            self.set_server_status("启动中")
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
            self.server_started_at = time.strftime("%Y-%m-%d %H:%M:%S")
            self.last_launch_config_text = self.build_launch_snapshot(cmd)
            self.update_runtime_summary()
            self.show_runtime_view()
            self.log_thread = threading.Thread(target=self.read_output, daemon=True)
            self.log_thread.start()
            self.start_btn.configure(state=tk.DISABLED)
            self.stop_btn.configure(state=tk.NORMAL)
            self.root.after(3000, self.check_server_ready)
            self.root.after(300, self.update_log_display)
            self.start_monitoring()
        except Exception as e:
            self.set_server_status("启动失败")
            self.show_config_view()
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
            self.log_text.configure(state=tk.NORMAL)
            self.log_text.insert(tk.END, "\n".join(new_lines) + "\n")
            self.log_text.see(tk.END)
            self.log_text.configure(state=tk.DISABLED)

        if hasattr(self, "root") and self.running:
            self.root.after(300, self.update_log_display)

    def clear_log(self):
        self.log_lines = []
        self.log_text.configure(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.configure(state=tk.DISABLED)

    def check_server_ready(self):
        import threading
        import socket

        def check():
            host = self.host_var.get().strip()
            port = int(self.port_var.get().strip())
            for _ in range(30):
                if not (self.process and self.process.poll() is None):
                    return
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
                            lambda: self.set_server_status("已就绪"),
                        )
                        return
                except:
                    pass
                time.sleep(1)
            if not (self.process and self.process.poll() is None):
                return
            self.root.after(
                0,
                lambda: self.set_server_status("启动超时"),
            )

        threading.Thread(target=check, daemon=True).start()

    def stop_server(self):
        if self.process is None:
            return
        self.running = False
        self.stop_monitoring()
        try:
            self.process.terminate()
            self.process.wait(timeout=5)
        except Exception:
            self.process.kill()
        self.process = None
        self.start_btn.configure(state=tk.NORMAL)
        self.stop_btn.configure(state=tk.DISABLED)
        self.set_server_status("已停止")
        self.show_config_view()
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

    def open_webui(self):
        import webbrowser

        host = self.host_var.get().strip()
        if host == "0.0.0.0":
            host = "127.0.0.1"
        webbrowser.open(f"http://{host}:{self.port_var.get().strip()}")
