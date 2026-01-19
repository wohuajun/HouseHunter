# room.py
"""房间管理模块 - 房间的增删改查功能"""

import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from config import COLORS
from widgets import WeChatButton
from dialogs import center_window

class RoomManager:
    """房间管理器"""
    
    def __init__(self, content, user_id, on_update_callback, to_furniture_callback=None):
        self.content = content
        self.user_id = user_id
        self.on_update_callback = on_update_callback       # 用于更新楼栋/家具数据的回调
        self.to_furniture_callback = to_furniture_callback # 用于跳转家具页面的回调
        self.tree = None
        
    def create_page(self):
        """创建房间管理页面"""
        tk.Label(self.content, text="房间管理", font=('Microsoft YaHei UI',18,'bold'),
                 bg=COLORS['bg'], fg=COLORS['text']).pack(pady=25)

        # 定义列：ID, 楼栋名称, 房间名称, 面积, 家具数, 成本, 租金, 状态, 楼栋ID(隐藏), 合同状态(隐藏)
        self.tree = ttk.Treeview(self.content, columns=("room_id","house_name","room_name","room_area","furniture_count","room_cost","room_rent","room_status","house_id","contract_status"), show="headings", height=18)
        
        # 可见列配置
        visible_cols = [
            ("room_id","ID",50),
            ("house_name","所属楼栋",140),
            ("room_name","房间名称",140),
            ("room_area","面积",80),
            ("furniture_count","家具数",80),
            ("room_cost","成本",100),
            ("room_rent","租金",100),
            ("room_status","状态",100)
        ]
        for col, text, w in visible_cols:
            self.tree.heading(col, text=text)
            self.tree.column(col, width=w, anchor='center')
            
        # 隐藏列
        self.tree.column("house_id", width=0, stretch=False)
        self.tree.column("contract_status", width=0, stretch=False)
        
        # 状态颜色标签
        self.tree.tag_configure('vacant', background='#E8F5E9')      # 绿色 - 空置
        self.tree.tag_configure('rented', background='#FFF3E0')      # 橙色 - 出租中
        self.tree.tag_configure('repair', background='#FFCDD2')      # 红色 - 维修中/不可用/自住
        self.tree.tag_configure('unavailable', background='#FFCDD2')
        self.tree.tag_configure('self_occupied', background='#FFCDD2')

        self.tree.pack(fill='both', expand=True, padx=30, pady=10)

        btns = tk.Frame(self.content, bg=COLORS['bg'])
        btns.pack(pady=10)
        WeChatButton(btns, text="添加房间", command=self.add_room).pack(side='left', padx=8)
        WeChatButton(btns, text="编辑房间", command=self.edit_room).pack(side='left', padx=8)
        WeChatButton(btns, text="删除房间", command=self.delete_room).pack(side='left', padx=8)
        WeChatButton(btns, text="家具管理", command=self.manage_furniture).pack(side='left', padx=8)

        self.load_rooms()
    
    def manage_furniture(self):
        """跳转到家具管理页面，并预选当前房间"""
        sel = self.tree.selection()
        if not sel:
            return messagebox.showwarning("提示", "请先选择一个房间，以管理其家具")
        
        values = self.tree.item(sel[0])["values"]
        room_id = values[0] 
        
        if self.to_furniture_callback:
            self.to_furniture_callback(room_id)
        else:
            messagebox.showwarning("提示", "未配置跳转功能")
    
    def load_rooms(self):
        """加载房间数据 - 租金优先显示有效合同的金额"""
        try:
            if not (self.tree and str(self.tree.winfo_exists()) == "1"):
                return
        except tk.TclError:
            return

        for i in self.tree.get_children():
            self.tree.delete(i)
            
        conn = sqlite3.connect('landlord.db')
        c = conn.cursor()
        
        c.execute("""
            SELECT 
                r.room_id,
                h.house_name,
                r.room_name,
                r.room_area,
                r.furniture_count,
                r.room_cost,
                COALESCE(c.rent, r.room_rent) AS display_rent,   -- 优先使用合同租金
                CASE 
                    WHEN c.status = '履行中' THEN '🔑 出租中'
                    WHEN r.room_status = '空置' THEN '✅ 空置'
                    WHEN r.room_status = '维修中' THEN '🔧 维修中'
                    WHEN r.room_status = '不可用' THEN '❌ 不可用'
                    WHEN r.room_status = '自住' THEN '🏠 自住'
                    ELSE r.room_status
                END AS display_status,
                r.house_id,
                c.status AS contract_status
            FROM room r
            LEFT JOIN house h ON r.house_id = h.house_id
            LEFT JOIN contract c ON r.room_id = c.room_id AND c.status = '履行中'
            WHERE r.user_id = ?
            ORDER BY h.house_name, r.room_name
        """, (self.user_id,))
        
        for row in c.fetchall():
            values = list(row)
            # 格式化租金
            rent_value = values[6] if values[6] is not None else 0.0
            values[6] = f"¥{float(rent_value):,.2f}"
            
            # 确定颜色标签
            tag = 'vacant'
            status_text = str(values[7])
            if '履行中' in status_text or '出租中' in status_text:
                tag = 'rented'
            elif '维修中' in status_text or '不可用' in status_text or '自住' in status_text:
                tag = 'repair'
                
            self.tree.insert("", "end", values=values, tags=(tag,))
        
        conn.close()

    def add_room(self):
        """添加房间（保持原有逻辑）"""
        from dialogs import center_window
        win = tk.Toplevel(self.content.master)
        win.title("添加房间")
        center_window(win, 420, 380, self.content.master)
        win.configure(bg=COLORS['bg'])
        win.transient(self.content.master)
        win.grab_set()
        win.attributes('-topmost', True)

        f = tk.Frame(win, bg='white')
        f.pack(expand=True, fill='both', padx=40, pady=40)

        tk.Label(f, text="所属楼栋", bg='white', font=('Microsoft YaHei UI',10, 'bold')).grid(row=0,column=0,sticky='w',pady=12)
        house_var = tk.StringVar()
        house_combo = ttk.Combobox(f, textvariable=house_var, state="readonly", width=27)
        house_combo.grid(row=0,column=1,pady=12)
        
        conn = sqlite3.connect('landlord.db')
        c = conn.cursor()
        c.execute("SELECT house_id, house_name FROM house WHERE user_id=?", (self.user_id,))
        houses = c.fetchall()
        house_names = [h[1] for h in houses]
        house_combo['values'] = house_names
        conn.close()

        tk.Label(f, text="房间名称", bg='white', font=('Microsoft YaHei UI',10, 'bold')).grid(row=1,column=0,sticky='w',pady=12)
        e_name = tk.Entry(f, width=30)
        e_name.grid(row=1,column=1,pady=12)

        tk.Label(f, text="面积(㎡)", bg='white', font=('Microsoft YaHei UI',10, 'bold')).grid(row=2,column=0,sticky='w',pady=12)
        e_area = tk.Entry(f, width=30)
        e_area.grid(row=2,column=1,pady=12)

        tk.Label(f, text="租金(元/月)", bg='white', font=('Microsoft YaHei UI',10, 'bold')).grid(row=3,column=0,sticky='w',pady=12)
        e_rent = tk.Entry(f, width=30)
        e_rent.grid(row=3,column=1,pady=12)

        tk.Label(f, text="状态", bg='white', font=('Microsoft YaHei UI',10, 'bold')).grid(row=4,column=0,sticky='w',pady=12)
        status_var = tk.StringVar(value="空置")
        status_combo = ttk.Combobox(f, textvariable=status_var, 
                                   values=["空置", "出租中", "维修中", "不可用", "自住"], 
                                   state="readonly", width=27)
        status_combo.grid(row=4,column=1,pady=12)

        def save():
            hname = house_var.get()
            name = e_name.get().strip()
            area_str = e_area.get().strip()
            rent_str = e_rent.get().strip()
            status = status_var.get()
            
            if not hname or not name:
                messagebox.showerror("错误", "请填写完整", parent=win)
                return
                
            hid = next((h[0] for h in houses if h[1] == hname), None)
            if not hid:
                messagebox.showerror("错误", "无效的楼栋", parent=win)
                return

            try:
                area = float(area_str)
                rent = float(rent_str) if rent_str else 0.0
            except ValueError:
                messagebox.showerror("错误", "面积和租金必须是数字", parent=win)
                return

            conn = sqlite3.connect('landlord.db')
            c = conn.cursor()
            c.execute("INSERT INTO room (user_id, house_id, room_name, room_area, room_rent, room_status) VALUES (?,?,?,?,?,?)",
                      (self.user_id, hid, name, area, rent, status))
            conn.commit()
            conn.close()
            
            if self.on_update_callback:
                self.on_update_callback()
                
            win.destroy()
            self.load_rooms()

        WeChatButton(f, text="确定添加", command=save, width=20).grid(row=5,column=0,columnspan=2,pady=20)

    def edit_room(self):
        """编辑房间 - 租金改为只读展示"""
        sel = self.tree.selection()
        if not sel:
            return messagebox.showwarning("提示", "请先选择房间")
        
        values = self.tree.item(sel[0])["values"]
        rid = values[0]

        win = tk.Toplevel(self.content.master)
        win.title("编辑房间")
        center_window(win, 420, 400, self.content.master)
        win.configure(bg=COLORS['bg'])
        win.transient(self.content.master)
        win.grab_set()
        win.attributes('-topmost', True)

        f = tk.Frame(win, bg='white')
        f.pack(expand=True, fill='both', padx=40, pady=40)

        # 楼栋
        tk.Label(f, text="所属楼栋", bg='white', font=('Microsoft YaHei UI',10, 'bold')).grid(row=0,column=0,sticky='w',pady=12)
        house_var = tk.StringVar()
        house_combo = ttk.Combobox(f, textvariable=house_var, state="readonly", width=27)
        house_combo.grid(row=0,column=1,pady=12)
        
        conn = sqlite3.connect('landlord.db')
        c = conn.cursor()
        c.execute("SELECT house_id, house_name FROM house WHERE user_id=?", (self.user_id,))
        houses = c.fetchall()
        house_names = [h[1] for h in houses]
        house_combo['values'] = house_names
        
        current_house_name = values[1]
        if current_house_name in house_names:
            house_var.set(current_house_name)

        # 房间名称
        tk.Label(f, text="房间名称", bg='white', font=('Microsoft YaHei UI',10, 'bold')).grid(row=1,column=0,sticky='w',pady=12)
        e_name = tk.Entry(f, width=30)
        e_name.insert(0, values[2])
        e_name.grid(row=1,column=1,pady=12)

        # 面积
        tk.Label(f, text="面积(㎡)", bg='white', font=('Microsoft YaHei UI',10, 'bold')).grid(row=2,column=0,sticky='w',pady=12)
        e_area = tk.Entry(f, width=30)
        area_val = values[3] if isinstance(values[3], (int, float)) else 0
        e_area.insert(0, str(area_val))
        e_area.grid(row=2,column=1,pady=12)

        # 租金 - 只读显示
        tk.Label(f, text="租金(元/月)", bg='white', font=('Microsoft YaHei UI',10, 'bold')).grid(row=3,column=0,sticky='w',pady=12)
        rent_display = values[6]  # 已格式化好的 ¥x,xxx.xx
        tk.Label(f, text=rent_display, bg='white', fg='#D32F2F', font=('Microsoft YaHei UI',11,'bold'),
                 anchor='w').grid(row=3, column=1, pady=12, sticky='w')
        
        tk.Label(f, text="（租金以当前有效合同为准，不可在此修改）", 
                 bg='white', fg='#888888', font=('Microsoft YaHei UI',9)).grid(row=4,column=0,columnspan=2,sticky='w',pady=(0,12))

        # 状态
        tk.Label(f, text="房间状态", bg='white', font=('Microsoft YaHei UI',10, 'bold')).grid(row=5,column=0,sticky='w',pady=12)
        raw_status = values[7].replace('✅ ', '').replace('🔑 ', '').replace('🔧 ', '').replace('❌ ', '').replace('🏠 ', '')
        status_var = tk.StringVar(value=raw_status)
        status_combo = ttk.Combobox(f, textvariable=status_var, 
                                   values=["空置", "出租中", "维修中", "不可用", "自住"], 
                                   state="readonly", width=27)
        status_combo.grid(row=5,column=1,pady=12)

        def save():
            hname = house_var.get()
            name = e_name.get().strip()
            area_str = e_area.get().strip()
            status = status_var.get()
            
            if not hname or not name:
                messagebox.showerror("错误", "请填写完整", parent=win)
                return
                
            hid = next((h[0] for h in houses if h[1] == hname), None)
            if not hid:
                messagebox.showerror("错误", "无效的楼栋", parent=win)
                return

            try:
                area = float(area_str)
            except ValueError:
                messagebox.showerror("错误", "面积必须是数字", parent=win)
                return

            conn = sqlite3.connect('landlord.db')
            c = conn.cursor()
            # 不再更新 room_rent
            c.execute("UPDATE room SET house_id=?, room_name=?, room_area=?, room_status=? WHERE room_id=?", 
                      (hid, name, area, status, rid))
            conn.commit()
            conn.close()
            
            if self.on_update_callback:
                self.on_update_callback()
                
            win.destroy()
            self.load_rooms()

        WeChatButton(f, text="保存修改", command=save, width=20).grid(row=6,column=0,columnspan=2,pady=25)

    def delete_room(self):
        """删除房间"""
        sel = self.tree.selection()
        if not sel:
            return messagebox.showwarning("提示", "请先选择房间")
        if not messagebox.askyesno("确认", "删除房间会删除相关家具数据，确定吗？"):
            return
        rid = self.tree.item(sel[0])["values"][0]
        conn = sqlite3.connect('landlord.db')
        c = conn.cursor()
        c.execute("DELETE FROM room WHERE room_id=?", (rid,))
        conn.commit()
        conn.close()
        
        if self.on_update_callback:
            self.on_update_callback()
        
        self.load_rooms()