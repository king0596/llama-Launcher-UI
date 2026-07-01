import tkinter as tk

try:
    import customtkinter as ctk
except ImportError:
    ctk = None

from config import COLORS


class UIWidgetMixin:
    """通用 UI 控件构建器 mixin。"""
    COLORS = COLORS

    # ---- 通用卡片 ----
    def card(self, parent, title=None, right_label=None):
        C = self.COLORS
        frame = ctk.CTkFrame(
            parent, fg_color=C["card"], corner_radius=8,
            border_width=1, border_color=C["card_border"],
        )
        frame.grid_columnconfigure(0, weight=1)
        if title:
            if right_label is not None:
                # 标题行用 frame 包裹，左侧标题 + 右侧标签
                title_row = ctk.CTkFrame(frame, fg_color="transparent")
                title_row.grid(row=0, column=0, sticky="ew", padx=14, pady=(9, 0))
                title_row.grid_columnconfigure(0, weight=1)
                ctk.CTkLabel(
                    title_row, text=title,
                    font=("Microsoft YaHei UI", 12, "bold"),
                    text_color=C["text_primary"], anchor="w",
                ).grid(row=0, column=0, sticky="w")
                ctk.CTkLabel(
                    title_row, textvariable=right_label if hasattr(right_label, "set") else None,
                    text=right_label if not hasattr(right_label, "set") else "",
                    font=("Consolas", 11, "bold"),
                    text_color=C["primary"], anchor="e",
                ).grid(row=0, column=1, sticky="e")
            else:
                hl = ctk.CTkLabel(
                    frame, text=title,
                    font=("Microsoft YaHei UI", 12, "bold"),
                    text_color=C["text_primary"],
                )
                hl.grid(row=0, column=0, sticky="w", padx=14, pady=(9, 0))
            ctk.CTkFrame(frame, height=1, fg_color=C["divider"]).grid(
                row=1, column=0, sticky="ew", padx=14, pady=(6, 5)
            )
        return frame

    # ---- 基础组件构建器 ----
    def _input_style(self):
        C = self.COLORS
        return {"height": 29, "corner_radius": 6, "border_width": 1,
                "border_color": C["input_border"], "fg_color": C["input_bg"],
                "text_color": C["text_primary"], "font": ("Consolas", 11)}

    def _combo_style(self):
        C = self.COLORS
        return {"height": 29, "corner_radius": 6, "border_width": 1,
                "border_color": C["input_border"], "fg_color": C["input_bg"],
                "button_color": C["input_bg"], "button_hover_color": C["tab_bg"],
                "text_color": C["text_primary"],
                "font": ("Microsoft YaHei UI", 11)}

    def add_label(self, parent, row, text, tooltip=""):
        C = self.COLORS
        label = ctk.CTkLabel(
            parent, text=text, text_color=C["text_secondary"],
            font=("Microsoft YaHei UI", 11), anchor="w", width=124,
        )
        label.grid(row=row, column=0, sticky="w", padx=(14, 8), pady=5)
        if tooltip:
            self.create_tooltip(label, tooltip)
        return label

    def add_input_row(self, parent, row, label, var, tooltip=""):
        C = self.COLORS
        self.add_label(parent, row, label, tooltip)
        sty = self._input_style()
        entry = ctk.CTkEntry(parent, textvariable=var, **sty)
        entry.grid(row=row, column=1, sticky="ew", padx=(0, 12), pady=3)
        if tooltip:
            self.create_tooltip(entry, tooltip)
        return row + 1

    def add_input_cell(self, parent, index, label, var, tooltip=""):
        C = self.COLORS
        row, col = self.row_col(index)
        ctk.CTkLabel(parent, text=label, text_color=C["text_secondary"], font=("Microsoft YaHei UI", 11)).grid(
            row=row, column=col, sticky="w", padx=(10, 6), pady=4
        )
        sty = self._input_style()
        entry = ctk.CTkEntry(parent, textvariable=var, **sty)
        entry.grid(row=row, column=col + 1, sticky="ew", padx=(0, 12), pady=4)
        if tooltip:
            self.create_tooltip(entry, tooltip)

    def add_dropdown_cell(self, parent, index, label, var, values, tooltip=""):
        C = self.COLORS
        row, col = self.row_col(index)
        ctk.CTkLabel(parent, text=label, text_color=C["text_secondary"], font=("Microsoft YaHei UI", 11)).grid(
            row=row, column=col, sticky="w", padx=(10, 6), pady=4
        )
        sty = self._combo_style()
        combo = ctk.CTkComboBox(parent, variable=var, values=values, **sty, state="readonly")
        combo.grid(row=row, column=col + 1, sticky="ew", padx=(0, 12), pady=4)
        if tooltip:
            self.create_tooltip(combo, tooltip)

    def add_switch_cell(self, parent, index, label, var, tooltip=""):
        C = self.COLORS
        row, col = self.row_col(index)
        switch = ctk.CTkSwitch(
            parent, text=label, variable=var,
            height=20, width=140,
            progress_color=C["switch_on"], button_color=C["switch_off"],
            text_color=C["text_primary"], font=("Microsoft YaHei UI", 11),
        )
        switch.grid(row=row, column=col, sticky="w", padx=12, pady=4)
        if tooltip:
            self.create_tooltip(switch, tooltip)

    def add_path_row(self, parent, row, label, var, browse_command, button_text="浏览", extra_command=None, tooltip=""):
        C = self.COLORS
        self.add_label(parent, row, label, tooltip)
        sty = self._input_style()
        entry = ctk.CTkEntry(parent, textvariable=var, **sty)
        entry.grid(row=row, column=1, sticky="ew", padx=(0, 6), pady=3)
        if tooltip:
            self.create_tooltip(entry, tooltip)

        btns = ctk.CTkFrame(parent, fg_color="transparent")
        btns.grid(row=row, column=2, sticky="e", padx=(0, 14), pady=4)
        ctk.CTkButton(
            btns, text=button_text, width=54, height=26, corner_radius=6,
            command=browse_command, fg_color=C["tab_bg"], hover_color=C["card_border"],
            text_color=C["text_primary"], font=("Microsoft YaHei UI", 10),
        ).pack(side=tk.LEFT)
        if extra_command:
            ctk.CTkButton(
                btns, text="刷新", width=54, height=26, corner_radius=6,
                command=extra_command, fg_color=C["tab_bg"], hover_color=C["card_border"],
                text_color=C["text_primary"], font=("Microsoft YaHei UI", 10),
            ).pack(side=tk.LEFT, padx=(4, 0))
        return row + 1

    def add_dropdown_row(self, parent, row, label, var, values, tooltip=""):
        self.add_label(parent, row, label, tooltip)
        sty = self._combo_style()
        combo = ctk.CTkComboBox(parent, variable=var, values=values, **sty, state="readonly")
        combo.grid(row=row, column=1, sticky="ew", padx=(0, 12), pady=3)
        if tooltip:
            self.create_tooltip(combo, tooltip)
        return row + 1

    def add_switch_row(self, parent, row, label, var, tooltip=""):
        C = self.COLORS
        # 标签 + 开关分开放置，避免拉伸变形
        lbl = ctk.CTkLabel(
            parent, text=label, text_color=C["text_secondary"],
            font=("Microsoft YaHei UI", 11), anchor="w", width=124,
        )
        lbl.grid(row=row, column=0, sticky="w", padx=(14, 8), pady=5)

        sw = ctk.CTkSwitch(
            parent, text="", variable=var,
            height=20, width=40,
            progress_color=C["switch_on"], button_color=C["switch_off"],
        )
        sw.grid(row=row, column=1, sticky="w", padx=(0, 0), pady=4)
        if tooltip:
            self.create_tooltip(lbl, tooltip)
            self.create_tooltip(sw, tooltip)
        return row + 1

    def add_metric(self, parent, col, label, var):
        C = self.COLORS
        box = ctk.CTkFrame(
            parent, fg_color=C["card"], corner_radius=8,
            border_width=1, border_color=C["card_border"],
        )
        box.grid(row=0, column=col, sticky="nsew", padx=4, pady=9)
        box.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            box, text=label, text_color=C["text_hint"],
            font=("Microsoft YaHei UI", 10),
        ).pack(anchor="w", padx=8, pady=(6, 0))
        ctk.CTkEntry(
            box, textvariable=var, height=27, corner_radius=6,
            border_width=0, fg_color=C["input_bg"],
            text_color=C["text_primary"], font=("Consolas", 11),
        ).pack(fill=tk.X, padx=6, pady=(2, 6))

    # ---- 参数容器（高级参数 Tab 内部使用）----
    # 注：原使用 CTkScrollableFrame，但每个实例都会 bind_all 注册全局
    # MouseWheel/Shift 事件并绑定 <Configure> 触发 bbox("all")，7个实例
    # 累积导致窗口拖动严重卡顿。内容在 minsize(1100,700) 内无需滚动。
    def make_scroll_frame(self, parent):
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        # 3列：标签 | 输入 | 按钮（可选）
        frame.grid_columnconfigure(0, weight=0, minsize=132)
        frame.grid_columnconfigure(1, weight=1, minsize=104)
        frame.grid_columnconfigure(2, weight=0, minsize=64)
        return frame

    def row_col(self, index):
        return index // 2, (index % 2) * 3

    # ---- 分区标题（Tab 内部的小标题）----
    def _section_header(self, parent, row, text):
        C = self.COLORS
        ctk.CTkLabel(
            parent, text=text, text_color=C["text_secondary"],
            font=("Microsoft YaHei UI", 12, "bold"),
        ).grid(row=row, column=0, columnspan=3, sticky="w", padx=14, pady=(6, 2))
        ctk.CTkFrame(parent, height=1, fg_color=C["divider"]).grid(
            row=row + 1, column=0, columnspan=3, sticky="ew", padx=14, pady=2
        )

    def _destroy_active_tooltip(self):
        """销毁当前活动的 tooltip 并取消待显示的定时器。"""
        if getattr(self, "_tooltip_after_id", None) is not None:
            self.root.after_cancel(self._tooltip_after_id)
            self._tooltip_after_id = None
        tip = getattr(self, "_active_tooltip", None)
        if tip is not None:
            try:
                tip.destroy()
            except Exception:
                pass
            self._active_tooltip = None
        self._tooltip_widget = None

    def create_tooltip(self, widget, text):
        C = self.COLORS

        def _in_widget():
            """检查鼠标是否仍在控件 bounding box 内（兼容 CTk 内部子控件）。"""
            px = widget.winfo_pointerx()
            py = widget.winfo_pointery()
            wx = widget.winfo_rootx()
            wy = widget.winfo_rooty()
            return (
                wx <= px <= wx + widget.winfo_width()
                and wy <= py <= wy + widget.winfo_height()
            )

        def show_tooltip(event=None):
            # 同一控件已有 tooltip 在显示则跳过
            if (
                getattr(self, "_tooltip_widget", None) is widget
                and self._active_tooltip is not None
            ):
                return
            self._destroy_active_tooltip()
            self._tooltip_widget = widget

            def _do_show():
                self._tooltip_after_id = None
                # 确认鼠标仍在该控件范围内
                if not _in_widget():
                    return
                tip = ctk.CTkToplevel(self.root)
                tip.wm_overrideredirect(True)
                tip.attributes("-topmost", True)
                ctk.CTkLabel(
                    tip, text=text,
                    fg_color=C["dark_bg"], text_color=C["dark_text"],
                    corner_radius=8, padx=10, pady=7,
                    wraplength=360, justify=tk.LEFT,
                    font=("Microsoft YaHei UI", 11),
                ).pack()
                x = widget.winfo_rootx() + 12
                y = widget.winfo_rooty() + widget.winfo_height() + 6
                tip.geometry(f"+{x}+{y}")
                self._active_tooltip = tip

            self._tooltip_after_id = self.root.after(500, _do_show)

        def hide_tooltip(event=None):
            # CTk 内部子元素会触发虚假 Leave，仅在鼠标真正离开时销毁
            if _in_widget():
                return
            self._destroy_active_tooltip()

        widget.bind("<Enter>", show_tooltip, add="+")
        widget.bind("<Leave>", hide_tooltip, add="+")
        widget.bind("<ButtonPress>", hide_tooltip, add="+")
