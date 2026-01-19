# widgets.py
"""自定义组件模块 - 包含WeChat风格的按钮组件"""

import tkinter as tk
from config import COLORS

class WeChatButton(tk.Button):
    """微信风格按钮"""
    def __init__(self, master, text="", command=None, bg_color=COLORS['primary'], hover_color=COLORS['primary_hover'], fg_color='white', **kw):
        super().__init__(
            master, text=text, command=command,
            bg=bg_color, fg=fg_color,
            font=('Microsoft YaHei UI', 10, 'bold'),
            relief='flat', bd=0, highlightthickness=0,
            activebackground=hover_color,
            cursor='hand2', **kw
        )
        self.base_bg = bg_color
        self.hover_bg = hover_color
        self.bind("<Enter>", lambda e: self.config(bg=self.hover_bg))
        self.bind("<Leave>", lambda e: self.config(bg=self.base_bg))

class SidebarButton(tk.Button):
    """侧边栏按钮"""
    def __init__(self, master, text="", command=None):
        self.normal_bg = COLORS['sidebar']
        self.select_bg = COLORS['primary']
        self.hover_bg = COLORS['primary_hover']
        self.normal_fg = COLORS['text']
        self.select_fg = 'white'
        self.is_selected = False
        super().__init__(
            master, text=text, command=command,
            bg=self.normal_bg, fg=self.normal_fg,
            font=('Microsoft YaHei UI', 11, 'bold'),
            relief='flat', anchor='w', justify='left',
            padx=20, pady=12, bd=0,
            activebackground=self.hover_bg
        )
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)

    def _on_enter(self, e):
        if self.is_selected:
            self.config(bg=self.hover_bg, fg=self.select_fg)
        else:
            self.config(bg=self.select_bg, fg=self.select_fg)

    def _on_leave(self, e):
        if self.is_selected:
            self.config(bg=self.select_bg, fg=self.select_fg)
        else:
            self.config(bg=self.normal_bg, fg=self.normal_fg)

    def select(self):
        self.is_selected = True
        self.config(bg=self.select_bg, fg=self.select_fg)

    def deselect(self):
        self.is_selected = False
        self.config(bg=self.normal_bg, fg=self.normal_fg)
