# house.py
"""楼栋管理模块 - 楼栋的增删改查功能"""

import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from config import COLORS
from widgets import WeChatButton

class HouseManager:
    """楼栋管理器"""
    
    def __init__(self, content, user_id, on_update_callback):
        self.content = content
        self.user_id = user_id
        self.on_update_callback = on_update_callback
        self.tree = None
        
    def create_page(self):
        """创建楼栋管理页面"""
        tk.Label(self.content, text="楼栋管理", font=('Microsoft YaHei UI',18,'bold'),
                 bg=COLORS['bg'], fg=COLORS['text']).pack(pady=25)

        self.tree = ttk.Treeview(self.content, columns=("house_id","house_name","house_add","house_floor","room_count","house_cost","house_status"), show="headings", height=18)
        cols = [("house_id","ID",60),("house_name","名称",180),("house_add","地址",280),("house_floor","层数",80),("room_count","房间数",100),("house_cost","成本",120),("house_status","状态",100)]
        for col, text, w in cols:
            self.tree.heading(col, text=text)
            self.tree.column(col, width=w, anchor='center')
        self.tree.pack(fill='both', expand=True, padx=30, pady=10)

        btns = tk.Frame(self.content, bg=COLORS['bg'])
        btns.pack(pady=10)
        WeChatButton(btns, text="添加楼栋", command=self.add_house).pack(side='left', padx=8)
        WeChatButton(btns, text="编辑楼栋", command=self.edit_house).pack(side='left', padx=8)
        WeChatButton(btns, text="删除楼栋", command=self.delete_house).pack(side='left', padx=8)

        self.load_houses()
    
    def load_houses(self):
        """加载楼栋数据"""
        for i in self.tree.get_children():
            self.tree.delete(i)
        conn = sqlite3.connect('landlord.db')
        c = conn.cursor()
        c.execute("SELECT house_id, house_name, house_add, house_floor, room_count, house_cost, house_status FROM house WHERE user_id=?", (self.user_id,))
        for row in c.fetchall():
            row = list(row)
            row[5] = f"¥{row[5]:,.2f}"
            # 根据状态设置背景色
            status = row[6]
            if status == '维修中':
                row[6] = f"🔧 {status}"
            elif status == '不可用':
                row[6] = f"❌ {status}"
            else:
                row[6] = f"✅ {status}"
            self.tree.insert("", "end", values=row)
        conn.close()
    
    def add_house(self):
        """添加楼栋"""
        from dialogs import center_window
        win = tk.Toplevel(self.content.master)
        win.title("添加楼栋")
        center_window(win, 420, 350, self.content.master)
        win.configure(bg=COLORS['bg'])
        win.transient(self.content.master)
        win.grab_set()
        win.attributes('-topmost', True)

        f = tk.Frame(win, bg='white')
        f.pack(expand=True, fill='both', padx=40, pady=40)

        tk.Label(f, text="楼栋名称", bg='white', font=('Microsoft YaHei UI',10, 'bold')).grid(row=0,column=0,sticky='w',pady=12)
        e_name = tk.Entry(f, width=30)
        e_name.grid(row=0,column=1,pady=12,padx=10)

        tk.Label(f, text="地址", bg='white', font=('Microsoft YaHei UI',10, 'bold')).grid(row=1,column=0,sticky='w',pady=12)
        e_add = tk.Entry(f, width=30)
        e_add.grid(row=1,column=1,pady=12,padx=10)

        tk.Label(f, text="层数", bg='white', font=('Microsoft YaHei UI',10, 'bold')).grid(row=2,column=0,sticky='w',pady=12)
        e_floor = tk.Entry(f, width=30)
        e_floor.grid(row=2,column=1,pady=12,padx=10)

        tk.Label(f, text="房间数", bg='white', font=('Microsoft YaHei UI',10, 'bold')).grid(row=3,column=0,sticky='w',pady=12)
        e_room_count = tk.Entry(f, width=30)
        e_room_count.insert(0, "0")
        e_room_count.grid(row=3,column=1,pady=12,padx=10)

        def save():
            name = e_name.get().strip()
            add = e_add.get().strip()
            floor = e_floor.get().strip()
            room_count_str = e_room_count.get().strip()
            if not name or not add or not floor or not room_count_str:
                messagebox.showerror("错误", "请填写完整",parent = win)
                return
            try:
                floor = int(floor)
                room_count = int(room_count_str)
                if room_count < 0:
                    raise ValueError
            except ValueError:
                messagebox.showerror("错误", "层数和房间数必须是正整数",parent = win)
                return
            conn = sqlite3.connect('landlord.db')
            c = conn.cursor()
            c.execute("INSERT INTO house (user_id, house_name, house_add, house_floor, room_count, house_status) VALUES (?, ?, ?, ?, ?, ?)",
                      (self.user_id, name, add, floor, room_count, '可用'))
            hid = c.lastrowid
            for i in range(1, room_count + 1):
                room_name = f"{name}-{i}"
                c.execute("INSERT INTO room (user_id, house_id, room_name, room_status) VALUES (?, ?, ?, ?)",
                          (self.user_id, hid, room_name, '空置'))
            conn.commit()
            conn.close()
            win.destroy()
            self.on_update_callback()
            self.load_houses()

        WeChatButton(f, text="确定添加", command=save, width=20).grid(row=4,column=0,columnspan=2,pady=20)

    def edit_house(self):
        """编辑楼栋"""
        from dialogs import center_window
        sel = self.tree.selection()
        if not sel:
            return messagebox.showwarning("提示", "请先选择楼栋")
        values = self.tree.item(sel[0])["values"]
        hid = values[0]

        win = tk.Toplevel(self.content.master)
        win.title("编辑楼栋")
        center_window(win, 420, 380, self.content.master)  # 调整窗口大小
        win.configure(bg=COLORS['bg'])
        win.transient(self.content.master)
        win.grab_set()
        win.attributes('-topmost', True)

        f = tk.Frame(win, bg='white')
        f.pack(expand=True, fill='both', padx=40, pady=40)

        tk.Label(f, text="楼栋名称", bg='white', font=('Microsoft YaHei UI',10, 'bold')).grid(row=0,column=0,sticky='w',pady=12)
        e_name = tk.Entry(f, width=30)
        e_name.insert(0, values[1])
        e_name.grid(row=0,column=1,pady=12,padx=10)

        tk.Label(f, text="地址", bg='white', font=('Microsoft YaHei UI',10, 'bold')).grid(row=1,column=0,sticky='w',pady=12)
        e_add = tk.Entry(f, width=30)
        e_add.insert(0, values[2])
        e_add.grid(row=1,column=1,pady=12,padx=10)

        tk.Label(f, text="层数", bg='white', font=('Microsoft YaHei UI',10, 'bold')).grid(row=2,column=0,sticky='w',pady=12)
        e_floor = tk.Entry(f, width=30)
        e_floor.insert(0, values[3])
        e_floor.grid(row=2,column=1,pady=12,padx=10)

        tk.Label(f, text="房间数", bg='white', font=('Microsoft YaHei UI',10, 'bold')).grid(row=3,column=0,sticky='w',pady=12)
        lbl_room_count = tk.Label(f, text=values[4], bg='white', font=('Microsoft YaHei UI',10))
        lbl_room_count.grid(row=3,column=1,pady=12,padx=10, sticky='w')

        tk.Label(f, text="状态", bg='white', font=('Microsoft YaHei UI',10, 'bold')).grid(row=4,column=0,sticky='w',pady=12)
        status_var = tk.StringVar(value=values[6].replace('🔧 ', '').replace('❌ ', '').replace('✅ ', ''))
        status_combo = ttk.Combobox(f, textvariable=status_var, values=["可用", "维修中", "不可用"], state="readonly", width=27)
        status_combo.grid(row=4,column=1,pady=12)

        def save():
            name = e_name.get().strip()
            add = e_add.get().strip()
            floor = e_floor.get().strip()
            status = status_var.get()
            if not name or not add or not floor:
                messagebox.showerror("错误", "请填写完整",parent = win)
                return
            try:
                floor = int(floor)
            except ValueError:
                messagebox.showerror("错误", "层数必须是整数",parent = win)
                return
            conn = sqlite3.connect('landlord.db')
            c = conn.cursor()
            c.execute("UPDATE house SET house_name=?, house_add=?, house_floor=?, house_status=? WHERE house_id=?", (name, add, floor, status, hid))
            conn.commit()
            conn.close()
            win.destroy()
            self.load_houses()

        WeChatButton(f, text="保存修改", command=save, width=20).grid(row=5,column=0,columnspan=2,pady=20)

    def delete_house(self):
        """删除楼栋"""
        sel = self.tree.selection()
        if not sel:
            return messagebox.showwarning("提示", "请先选择楼栋")
        if not messagebox.askyesno("确认", "删除楼栋会删除下属所有数据，确定吗？"):
            return
        hid = self.tree.item(sel[0])["values"][0]
        conn = sqlite3.connect('landlord.db')
        c = conn.cursor()
        c.execute("DELETE FROM house WHERE house_id=?", (hid,))
        conn.commit()
        conn.close()
        self.on_update_callback()
        self.load_houses()
