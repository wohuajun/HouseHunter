# auth.py
"""用户认证模块 - 包含登录和注册功能"""

import tkinter as tk
from tkinter import messagebox
import sqlite3
from config import COLORS
from widgets import WeChatButton
from dialogs import center_window  # 确保正确导入

def show_login_page(parent, on_login_success):
    """显示登录页面"""
    frame = tk.Frame(parent, bg=COLORS['bg'])
    frame.place(relx=0.5, rely=0.5, anchor='center')

    tk.Label(frame, text="HOUSE HUNTER", font=('Microsoft YaHei UI', 22, 'bold'),
             bg=COLORS['bg'], fg=COLORS['primary']).pack(pady=(0,40))

    card = tk.Frame(frame, bg='white', relief='flat', bd=1)
    card.pack(padx=40, pady=30)

    tk.Label(card, text="用户名", bg='white', font=('Microsoft YaHei UI',10, 'bold')).grid(row=0,column=0,sticky='w',pady=10,padx=20)
    entry_user = tk.Entry(card, width=30, font=('Microsoft YaHei UI',10), relief='solid', bd=1)
    entry_user.grid(row=0,column=1,pady=10,padx=20)

    tk.Label(card, text="密码", bg='white', font=('Microsoft YaHei UI',10, 'bold')).grid(row=1,column=0,sticky='w',pady=10,padx=20)
    entry_pass = tk.Entry(card, width=30, show='*', font=('Microsoft YaHei UI',10), relief='solid', bd=1)
    entry_pass.grid(row=1,column=1,pady=10,padx=20)

    btn_frame = tk.Frame(card, bg='white')
    btn_frame.grid(row=2, column=0, columnspan=2, pady=20)

    def do_login():
        user = entry_user.get().strip()
        password = entry_pass.get()
        conn = sqlite3.connect('landlord.db')
        c = conn.cursor()
        c.execute("SELECT id FROM user WHERE user=? AND password=?", (user, password))
        row = c.fetchone()
        conn.close()
        if row:
            on_login_success(row[0])
        else:
            messagebox.showerror("错误", "用户名或密码错误", parent=parent)

    def show_register():
        show_register_dialog(parent)

    WeChatButton(btn_frame, text="登录", width=12, command=do_login).pack(side='left', padx=10)
    WeChatButton(btn_frame, text="注册", width=12, command=show_register).pack(side='left', padx=10)
    
    return frame

def show_register_dialog(parent):
    """显示注册对话框 - 修复版"""
    win = tk.Toplevel(parent)
    win.title("注册")
    win.configure(bg=COLORS['bg'])
    win.transient(parent)
    win.grab_set()
    win.attributes('-topmost', True)
    
    # 使用修复后的center_window函数
    center_window(win, 400, 350, parent)

    card = tk.Frame(win, bg='white')
    card.pack(expand=True, fill='both', padx=40, pady=40)

    tk.Label(card, text="用户名", bg='white', font=('Microsoft YaHei UI',10, 'bold')).grid(row=0,column=0,sticky='w',pady=10)
    e_user = tk.Entry(card, width=25)
    e_user.grid(row=0,column=1,pady=10,padx=10)

    tk.Label(card, text="密码", bg='white', font=('Microsoft YaHei UI',10, 'bold')).grid(row=1,column=0,sticky='w',pady=10)
    e_pass = tk.Entry(card, width=25, show='*')
    e_pass.grid(row=1,column=1,pady=10,padx=10)

    tk.Label(card, text="确认密码", bg='white', font=('Microsoft YaHei UI',10, 'bold')).grid(row=2,column=0,sticky='w',pady=10)
    e_confirm = tk.Entry(card, width=25, show='*')
    e_confirm.grid(row=2,column=1,pady=10,padx=10)

    def reg():
        u = e_user.get().strip()
        p = e_pass.get()
        cp = e_confirm.get()
        if not u or not p or not cp:
            messagebox.showerror("错误", "请填写完整", parent=win)
            return
        if p != cp:
            messagebox.showerror("错误", "密码不一致", parent=win)
            return
        if len(u) < 4 or len(u) > 20 or not u.isalnum():
            messagebox.showerror("错误", "用户名4-20位字母数字", parent=win)
            return
        if len(p) < 6 or len(p) > 20 or not any(c.isdigit() for c in p) or not any(c.isalpha() for c in p):
            messagebox.showerror("错误", "密码6-20位含字母数字", parent=win)
            return
        conn = sqlite3.connect('landlord.db')
        c = conn.cursor()
        try:
            c.execute("INSERT INTO user (user, password) VALUES (?,?)", (u, p))
            conn.commit()
            messagebox.showinfo("成功", "注册成功", parent=win)
            win.destroy()
        except sqlite3.IntegrityError:
            messagebox.showerror("错误", "用户名已存在", parent=win)
        conn.close()

    WeChatButton(card, text="注册", width=15, command=reg).grid(row=3,column=0,columnspan=2,pady=20)
