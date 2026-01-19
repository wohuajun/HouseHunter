# furniture.py
"""家具管理模块 - 家具的增删改查功能"""

import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from config import COLORS
from widgets import WeChatButton

try:
    from tkcalendar import DateEntry
except ImportError:
    class DateEntry(tk.Entry):
        def __init__(self, master, **kwargs):
            super().__init__(master, **kwargs)
        def get_date(self):
            return None

class FurnitureManager:
    """家具管理器"""
    
    def __init__(self, content, user_id, update_costs_callback):
        self.content = content
        self.user_id = user_id
        self.update_costs_callback = update_costs_callback
        self.tree = None
        
    def create_page(self, preselected_room_id=None):
        """创建家具管理页面"""
        for widget in self.content.winfo_children():
            widget.destroy()
            
        tk.Label(self.content, text="家具管理", font=('Microsoft YaHei UI',18,'bold'),
                 bg=COLORS['bg'], fg=COLORS['text']).pack(pady=25)

        # 定义所有列 (ID, 房间名称, 家具名称, 数量, 单价, 总价, 备注, 房间ID)
        # 注意：columns 这里必须保留 fid 和 room_id，否则 data 索引会错位
        self.tree = ttk.Treeview(self.content, columns=("fid","room_name","furniture_name","count","cost","total_cost","note","room_id"), show="headings", height=18)
        
        # 【修改】只配置可见列的标题和宽度
        visible_cols = [
            ("room_name","所属房间",160),
            ("furniture_name","家具名称",200),
            ("count","数量",80),
            ("cost","单价",100),
            ("total_cost","总价",100),
            ("note","备注",200)
        ]
        for col, text, w in visible_cols:
            self.tree.heading(col, text=text)
            self.tree.column(col, width=w, anchor='center')
            
        # 【修改】强制隐藏 fid 和 room_id 列 (设宽度为0，且不可拉伸)
        self.tree.column("fid", width=0, stretch=False)
        self.tree.column("room_id", width=0, stretch=False)
        
        self.tree.pack(fill='both', expand=True, padx=30, pady=10)

        btns = tk.Frame(self.content, bg=COLORS['bg'])
        btns.pack(pady=10)
        WeChatButton(btns, text="添加家具", command=lambda: self.add_furniture(preselected_room_id)).pack(side='left', padx=8)
        # 复制家具按钮
        WeChatButton(btns, text="复制家具", command=self.copy_furniture).pack(side='left', padx=8)
        WeChatButton(btns, text="编辑家具", command=self.edit_furniture).pack(side='left', padx=8)
        WeChatButton(btns, text="删除家具", command=self.delete_furniture).pack(side='left', padx=8)

        self.load_furnitures()

    def load_furnitures(self):
        """加载家具数据"""
        try:
            for i in self.tree.get_children():
                self.tree.delete(i)
            conn = sqlite3.connect('landlord.db')
            c = conn.cursor()
            
            # 【修改】排序逻辑：先按房间ID (RID) 分组，再按家具ID (fid) 从小到大排序
            c.execute("""
                SELECT f.furniture_id, r.room_name, f.furniture, f.count, f.furniture_cost, f.total_cost, f.note, f.room_id
                FROM furniture f
                LEFT JOIN room r ON f.room_id = r.room_id
                WHERE f.user_id=?
                ORDER BY f.room_id ASC, f.furniture_id ASC
            """, (self.user_id,))
            
            for row in c.fetchall():
                self.tree.insert("", "end", values=row)
            conn.close()
        except Exception as e:
            print(f"加载家具数据出错: {e}")

    def add_furniture(self, preselected_room_id=None):
        """添加家具"""
        from dialogs import center_window
        win = tk.Toplevel(self.content.master)
        win.title("添加家具")
        center_window(win, 400, 350, self.content.master)
        win.configure(bg=COLORS['bg'])
        win.transient(self.content.master)
        win.grab_set()
        win.attributes('-topmost', True)

        f = tk.Frame(win, bg='white')
        f.pack(expand=True, fill='both', padx=40, pady=30)

        tk.Label(f, text="家具名称", bg='white', font=('Microsoft YaHei UI',10,'bold')).grid(row=0,column=0,sticky='w',pady=10)
        e_name = tk.Entry(f, width=30)
        e_name.grid(row=0,column=1,pady=10)

        tk.Label(f, text="所属房间", bg='white', font=('Microsoft YaHei UI',10,'bold')).grid(row=1,column=0,sticky='w',pady=10)
        conn = sqlite3.connect('landlord.db')
        c = conn.cursor()
        c.execute("SELECT room_id, room_name FROM room WHERE user_id=?", (self.user_id,))
        rooms = c.fetchall()
        conn.close()
        room_names = [r[1] for r in rooms]
        room_var = tk.StringVar()
        combo = ttk.Combobox(f, textvariable=room_var, values=room_names, state="readonly", width=27)
        combo.grid(row=1,column=1,pady=10)
        if room_names:
            if preselected_room_id:
                # 如果传入预选ID，尝试匹配
                sel_room = next((r[1] for r in rooms if r[0] == preselected_room_id), None)
                if sel_room: combo.set(sel_room)
            else:
                combo.set(room_names[0])

        tk.Label(f, text="数量", bg='white', font=('Microsoft YaHei UI',10,'bold')).grid(row=2,column=0,sticky='w',pady=10)
        e_count = tk.Entry(f, width=30)
        e_count.insert(0, "1")
        e_count.grid(row=2,column=1,pady=10)

        tk.Label(f, text="单价 (元)", bg='white', font=('Microsoft YaHei UI',10,'bold')).grid(row=3,column=0,sticky='w',pady=10)
        e_cost = tk.Entry(f, width=30)
        e_cost.insert(0, "0")
        e_cost.grid(row=3,column=1,pady=10)

        tk.Label(f, text="备注", bg='white', font=('Microsoft YaHei UI',10,'bold')).grid(row=4,column=0,sticky='w',pady=10)
        e_note = tk.Entry(f, width=30)
        e_note.grid(row=4,column=1,pady=10)

        def save():
            name = e_name.get().strip()
            rname = room_var.get()
            note = e_note.get().strip()
            if not name or not rname:
                messagebox.showerror("错误", "请填写完整",parent = win)
                return
            
            rid = next(h[0] for h in rooms if h[1] == rname)
            try:
                count = int(e_count.get())
                cost = float(e_cost.get())
            except ValueError:
                messagebox.showerror("错误", "数量和单价必须是数字",parent = win)
                return
            
            total = count * cost
            
            conn = sqlite3.connect('landlord.db')
            c = conn.cursor()
            c.execute("INSERT INTO furniture (user_id, room_id, furniture, note, count, furniture_cost, total_cost) VALUES (?, ?, ?, ?, ?, ?, ?)",
                      (self.user_id, rid, name, note, count, cost, total))
            conn.commit()
            conn.close()
            
            self.update_costs_callback()
            win.destroy()
            self.load_furnitures()

        WeChatButton(f, text="确定添加", command=save, width=20).grid(row=5,column=0,columnspan=2,pady=25)

    def copy_furniture(self):
        """复制选中的家具"""
        sel = self.tree.selection()
        if not sel:
            return messagebox.showwarning("提示", "请先选择一条家具记录")
        
        # 获取选中行的 ID (values[0] 是 fid)
        fid = self.tree.item(sel[0])["values"][0]
        
        # 二次确认
        if not messagebox.askyesno("确认", "确定复制选中的家具吗？(新家具将添加到相同房间)"):
            return

        try:
            conn = sqlite3.connect('landlord.db')
            c = conn.cursor()
            
            # 1. 读取原数据
            c.execute("""
                SELECT user_id, room_id, furniture, note, count, furniture_cost, total_cost 
                FROM furniture 
                WHERE furniture_id=?
            """, (fid,))
            row = c.fetchone()
            
            if row:
                # 2. 插入新数据 (ID 自动生成，其他数据保持一致)
                c.execute("""
                    INSERT INTO furniture (user_id, room_id, furniture, note, count, furniture_cost, total_cost)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, row)
                
                conn.commit()
                messagebox.showinfo("成功", "家具复制成功")
                
                self.update_costs_callback()
                self.load_furnitures()
                
            conn.close()
        except Exception as e:
            messagebox.showerror("错误", f"复制失败: {e}")

    def edit_furniture(self):
        """编辑家具"""
        from dialogs import center_window
        sel = self.tree.selection()
        if not sel:
            return messagebox.showwarning("提示", "请先选择家具")
        values = self.tree.item(sel[0])["values"]
        fid = values[0]

        win = tk.Toplevel(self.content.master)
        win.title("编辑家具")
        center_window(win, 400, 350, self.content.master)
        win.configure(bg=COLORS['bg'])
        win.transient(self.content.master)
        win.grab_set()
        win.attributes('-topmost', True)

        f = tk.Frame(win, bg='white')
        f.pack(expand=True, fill='both', padx=40, pady=30)

        tk.Label(f, text="家具名称", bg='white', font=('Microsoft YaHei UI',10,'bold')).grid(row=0,column=0,sticky='w',pady=10)
        e_name = tk.Entry(f, width=30)
        e_name.insert(0, values[2])
        e_name.grid(row=0,column=1,pady=10)

        tk.Label(f, text="所属房间", bg='white', font=('Microsoft YaHei UI',10,'bold')).grid(row=1,column=0,sticky='w',pady=10)
        conn = sqlite3.connect('landlord.db')
        c = conn.cursor()
        c.execute("SELECT room_id, room_name FROM room WHERE user_id=?", (self.user_id,))
        rooms = c.fetchall()
        conn.close()
        room_names = [r[1] for r in rooms]
        room_var = tk.StringVar(value=values[1])
        combo = ttk.Combobox(f, textvariable=room_var, values=room_names, state="readonly", width=27)
        combo.grid(row=1,column=1,pady=10)

        tk.Label(f, text="数量", bg='white', font=('Microsoft YaHei UI',10,'bold')).grid(row=2,column=0,sticky='w',pady=10)
        e_count = tk.Entry(f, width=30)
        e_count.insert(0, str(values[3]))
        e_count.grid(row=2,column=1,pady=10)

        tk.Label(f, text="单价 (元)", bg='white', font=('Microsoft YaHei UI',10,'bold')).grid(row=3,column=0,sticky='w',pady=10)
        e_cost = tk.Entry(f, width=30)
        e_cost.insert(0, str(values[4]))
        e_cost.grid(row=3,column=1,pady=10)

        tk.Label(f, text="备注", bg='white', font=('Microsoft YaHei UI',10,'bold')).grid(row=4,column=0,sticky='w',pady=10)
        e_note = tk.Entry(f, width=30)
        e_note.insert(0, values[6] if len(values) > 6 else '')
        e_note.grid(row=4,column=1,pady=10)

        def save():
            name = e_name.get().strip()
            rname = room_var.get()
            note = e_note.get().strip()
            if not name or not rname:
                messagebox.showerror("错误", "请填写完整",parent = win)
                return
            
            rid = next(h[0] for h in rooms if h[1] == rname)
            try:
                count = int(e_count.get())
                cost = float(e_cost.get())
            except ValueError:
                messagebox.showerror("错误", "数量和单价必须是数字",parent = win)
                return
            
            total = count * cost
            
            conn = sqlite3.connect('landlord.db')
            c = conn.cursor()
            c.execute("UPDATE furniture SET user_id=?, room_id=?, furniture=?, note=?, count=?, furniture_cost=?, total_cost=? WHERE furniture_id=?", 
                      (self.user_id, rid, name, note, count, cost, total, fid))
            conn.commit()
            conn.close()
            
            self.update_costs_callback()
            win.destroy()
            self.load_furnitures()

        WeChatButton(f, text="保存修改", command=save, width=20).grid(row=5,column=0,columnspan=2,pady=25)

    def delete_furniture(self):
        """删除家具"""
        sel = self.tree.selection()
        if not sel:
            return messagebox.showwarning("提示", "请先选择家具")
        if not messagebox.askyesno("确认", "删除家具会删除相关数据，确定吗？"):
            return
        fid = self.tree.item(sel[0])["values"][0]
        conn = sqlite3.connect('landlord.db')
        c = conn.cursor()
        c.execute("DELETE FROM furniture WHERE furniture_id=?", (fid,))
        conn.commit()
        conn.close()
        
        self.update_costs_callback()
        self.load_furnitures()
