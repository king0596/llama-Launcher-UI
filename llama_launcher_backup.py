import tkinter as tk
from tkinter import messagebox
import os
import queue

try:
    import customtkinter as ctk
except ImportError:
    ctk = None

from config import COLORS
from utils import parse_args
from ui.widgets import UIWidgetMixin
from ui.views import ViewMixin
from core.server import ServerMixin
from core.command import CommandMixin
from core.config_manager import ConfigMixin
from core.monitor import MonitorMixin


args = parse_args()


def patch_customtkinter_runtime():
    """Disable CTk polling paths that make Tk window dragging stutter on Windows."""
    if ctk is None:
        return

    # Use a fixed theme mode so AppearanceModeTracker does not need system polling.
    ctk.set_appearance_mode("light")
    ctk.AppearanceModeTracker.update_loop_running = True

    # Keep CTk's initial scaling values, but prevent the 100ms DPI watcher from
    # competing with the Windows move/resize message loop.
    ctk.ScalingTracker.update_loop_running = True
    ctk.CTk._deactivate_windows_window_header_manipulation = True
    ctk.CTkToplevel._deactivate_windows_window_header_manipulation = True

    # customtkinter 6.0.0 accidentally leaves this flag False in both methods.
    # When DPI callbacks run, geometry updates are not actually blocked.
    def block_update_dimensions_event(self):
        self._block_update_dimensions_event = True

    def unblock_update_dimensions_event(self):
        self._block_update_dimensions_event = False

    ctk.CTk.block_update_dimensions_event = block_update_dimensions_event
    ctk.CTk.unblock_update_dimensions_event = unblock_update_dimensions_event
    ctk.CTkToplevel.block_update_dimensions_event = block_update_dimensions_event
    ctk.CTkToplevel.unblock_update_dimensions_event = unblock_update_dimensions_event

    # Several CTkTextbox widgets otherwise poll scrollbar state every 200ms.
    # A slower check keeps auto-scrollbars while reducing idle UI wakeups.
    ctk.CTkTextbox._scrollbar_update_time = 1000


class LlamaLauncher(UIWidgetMixin, ViewMixin, ServerMixin, CommandMixin, ConfigMixin, MonitorMixin):
    """Llama Server 启动器主类，通过 mixin 组合各功能模块。"""

    COLORS = COLORS

    def __init__(self, root):
        self.root = root
        self.root.title("Llama Server Launcher")
        self.root.geometry("1080x780")
        self.root.resizable(True, True)
        self.process = None
        self.openclaw_process = None
        self.command_update_after_id = None
        self.gpu_update_after_id = None
        self.log_queue = queue.Queue()
        self.log_thread = None
        self.running = False
        self.max_log_lines = 5000
        self.log_lines = []
        self._last_output_was_idle = False
        self._server_status_text = "未运行"
        self._cli_args = args
        self.config_file = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "config.toml"
        )
        self.config = {}
        self.last_launch_config_text = ""
        self.last_launch_command = ""
        self.model_root = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "model"
        )
        self.models = []
        self.load_config()
        self.model_root = self.config.get("model_root", self.model_root)
        self.scan_models()
        self.create_variables()
        self.init_monitor()
        self.build_ui()
        self.load_config_to_ui()
        self.apply_cli_args()
        self.setup_variable_traces()
        self.update_command_preview()

    def create_variables(self):
        self.model_root_var = tk.StringVar(value=self.model_root)
        self.model_combo_var = tk.StringVar()
        self.model_path_var = tk.StringVar()
        self.mmproj_path_var = tk.StringVar()
        self.mmproj_enabled_var = tk.BooleanVar()
        self.server_path_var = tk.StringVar()
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
        self.chat_template_var = tk.StringVar()
        self.repeat_penalty_var = tk.StringVar()
        self.repeat_last_n_var = tk.StringVar()
        self.seed_var = tk.StringVar()
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
        self.verbose_var = tk.BooleanVar()
        self.webui_var = tk.BooleanVar()
        self.embeddings_var = tk.BooleanVar()
        self.log_verbosity_var = tk.StringVar()
        self.custom_args_var = tk.StringVar()
        self.gpu_status_var = tk.StringVar(value="-")
        self.pid_var = tk.StringVar(value="-")

    def on_closing(self):
        try:
            self.config["window_geometry"] = self.root.geometry()
            self.write_config_file()
        except Exception:
            pass
        self.stop_monitoring()
        self.stop_server()
        self.root.destroy()


def main():
    if ctk is None:
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror(
            "缺少依赖",
            "缺少 customtkinter。\n\n请在当前目录运行:\npython -m pip install -r requirements.txt",
        )
        root.destroy()
        return

    patch_customtkinter_runtime()

    root = tk.Tk()
    app = LlamaLauncher(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()


if __name__ == "__main__":
    main()
