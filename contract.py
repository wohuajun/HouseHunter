# contract.py
"""合同管理模块 - 合同的增删改查功能"""

import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import datetime
import calendar
from config import COLORS
from widgets import WeChatButton

try:
    from tkcalendar import DateEntry
except ImportError:
    class DateEntry(tk.Entry):
        def __init__(self, master, **kwargs):
            super().__init__(master, **kwargs)
        def get_date(self):
            return datetime.date.today()

class ContractManager:
    """合同管理器"""
    
    def __init__(self, content, user_id, update_rooms_callback, update_dashboard_callback):
        self.content = content
        self.user_id = user_id
        self.update_rooms_callback = update_rooms_callback
        self.update_dashboard_callback = update_dashboard_callback
        self.tree = None
        self._upgrade_db_schema()
        
    def _upgrade_db_schema(self):
        """升级数据库结构"""
        try:
            conn = sqlite3.connect('landlord.db')
            c = conn.cursor()
            c.execute("PRAGMA table_info(contract)")
            columns = [col[1] for col in c.fetchall()]
            
            if 'renter_id' not in columns:
                print("升级数据库: 添加 renter_id...")
                c.execute("ALTER TABLE contract ADD COLUMN renter_id INTEGER")
                c.execute("""
                    UPDATE contract 
                    SET renter_id = (
                        SELECT renter_id FROM renter 
                        WHERE renter.contract_id = contract.contract_id 
                        LIMIT 1
                    )
                """)
            
            if 'payment_method' not in columns:
                print("升级数据库: 添加 payment_method...")
                c.execute("ALTER TABLE contract ADD COLUMN payment_method TEXT DEFAULT '月付'")
                c.execute("UPDATE contract SET payment_method='月付' WHERE payment_method IS NULL")

            if 'last_payment_date' not in columns:
                print("升级数据库: 添加 last_payment_date...")
                c.execute("ALTER TABLE contract ADD COLUMN last_payment_date DATE")
                c.execute("UPDATE contract SET last_payment_date=start_date WHERE last_payment_date IS NULL")

            if 'paid_until_date' not in columns:
                print("升级数据库: 添加 paid_until_date...")
                c.execute("ALTER TABLE contract ADD COLUMN paid_until_date DATE")
                
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"数据库升级警告: {e}")

    def create_page(self):
        """创建合同管理页面"""
        tk.Label(self.content, text="合同管理", font=('Microsoft YaHei UI',18,'bold'),
                 bg=COLORS['bg'], fg=COLORS['text']).pack(pady=25)

        self.tree = ttk.Treeview(self.content, columns=("contract_id","room_name","renter_names","start_date","end_date","rent","pledge","status","total_rent","total_cash"), show="headings", height=18)
        cols = [
            ("contract_id","ID",60),
            ("room_name","房间",140),
            ("renter_names","租客",200),
            ("start_date","开始日期",120),
            ("end_date","结束日期",120),
            ("rent","租金",100),
            ("pledge","押金",100),
            ("status","状态",100),
            ("total_rent","已交租金",120),
            ("total_cash","总金额",120)
        ]
        for col, text, w in cols:
            self.tree.heading(col, text=text)
            self.tree.column(col, width=w, anchor='center')
        
        self.tree.tag_configure('active', background='#FFA500')
        self.tree.tag_configure('ended', background='#CCCCCC')
        self.tree.tag_configure('pending', background='#90EE90')
        
        self.tree.pack(fill='both', expand=True, padx=30, pady=10)

        btns = tk.Frame(self.content, bg=COLORS['bg'])
        btns.pack(pady=10)
        
        # 【新增】租金记录按钮放在最前面
        WeChatButton(btns, text="租金记录", command=self.open_rental_record).pack(side='left', padx=8)
        WeChatButton(btns, text="添加合同", command=self.add_contract).pack(side='left', padx=8)
        WeChatButton(btns, text="编辑合同", command=self.edit_contract).pack(side='left', padx=8)
        WeChatButton(btns, text="删除合同", command=self.delete_contract).pack(side='left', padx=8)

        self.load_contracts()
    
    def load_contracts(self):
        """加载合同数据"""
        for i in self.tree.get_children():
            self.tree.delete(i)
        conn = sqlite3.connect('landlord.db')
        c = conn.cursor()
        c.execute("""
            SELECT c.contract_id, rm.room_name, 
                   GROUP_CONCAT(rt.renter_name, ', ') as renter_names,
                   c.start_date, c.end_date, c.rent, c.pledge, c.status, c.total_rent, c.total_cash
            FROM contract c 
            LEFT JOIN room rm ON c.room_id = rm.room_id 
            LEFT JOIN renter rt ON c.renter_id = rt.renter_id
            WHERE c.user_id=?
            GROUP BY c.contract_id, rm.room_name, c.start_date, c.end_date, c.rent, c.pledge, c.status, c.total_rent, c.total_cash
            ORDER BY c.contract_id
        """, (self.user_id,))
        
        for row in c.fetchall():
            row = list(row)
            status = row[7]
            if status == '履行中':
                tag = 'active'
            elif status in ['已结束', '已终止']:
                tag = 'ended'
            else:
                tag = 'pending'
            
            row.append(row[5])
            row.append(row[6])
            row.append(row[8])
            
            row[5] = f"¥{row[5]:,.2f}" if row[5] is not None else ''
            row[6] = f"¥{row[6]:,.2f}" if row[6] is not None else ''
            row[8] = f"¥{row[8]:,.2f}" if row[8] is not None else ''
            row[9] = f"¥{row[9]:,.2f}" if row[9] is not None else ''
            
            self.tree.insert("", "end", values=row, tags=(tag,)) 
        conn.close()

    def _add_months_local(self, sourcedate, months):
        """内部辅助函数：增加月份"""
        month = sourcedate.month - 1 + months
        year = sourcedate.year + month // 12
        month = month % 12 + 1
        day = min(sourcedate.day, calendar.monthrange(year, month)[1])
        return datetime.date(year, month, day)

    def open_rental_record(self):
        """打开租金记录窗口（编辑已付截止日期）"""
        sel = self.tree.selection()
        if not sel:
            return messagebox.showwarning("提示", "请先选择一条合同", parent=self.content.master)
        
        values = self.tree.item(sel[0])["values"]
        cid = values[0]
        
        from dialogs import center_window
        win = tk.Toplevel(self.content.master)
        win.title("租金记录")
        center_window(win, 350, 250, self.content.master)
        win.configure(bg=COLORS['bg'])
        win.transient(self.content.master)
        win.grab_set()
        win.attributes('-topmost', True)

        f = tk.Frame(win, bg='white')
        f.pack(expand=True, fill='both', padx=40, pady=30)

        # 获取当前信息
        conn = sqlite3.connect('landlord.db')
        c = conn.cursor()
        c.execute("SELECT room_id, renter_id, paid_until_date, payment_method FROM contract WHERE contract_id=?", (cid,))
        info = c.fetchone()
        
        c.execute("SELECT room_name FROM room WHERE room_id=?", (info[0],))
        rname = c.fetchone()[0]
        c.execute("SELECT renter_name FROM renter WHERE renter_id=?", (info[1],))
        rtname = c.fetchone()[0] if info[1] else "未知"
        
        current_paid_until = info[2]
        pay_method = info[3] if len(info) > 3 else '月付'
        conn.close()

        tk.Label(f, text=f"房间: {rname}", bg='white', font=('Microsoft YaHei UI', 10, 'bold'), anchor='w').pack(fill='x', pady=(10, 5))
        tk.Label(f, text=f"租客: {rtname}", bg='white', font=('Microsoft YaHei UI', 10, 'bold'), anchor='w').pack(fill='x', pady=(0, 5))
        
        tk.Label(f, text="租金已付截止日期:", bg='white', font=('Microsoft YaHei UI', 10, 'bold'), anchor='w').pack(fill='x', pady=(10, 5))
        
        e_date = DateEntry(f, width=30, background='darkblue', foreground='white', borderwidth=2, locale='zh_CN', date_pattern='yyyy-mm-dd')
        if current_paid_until:
            try:
                e_date.set_date(datetime.date.fromisoformat(current_paid_until))
            except:
                e_date.set_date(datetime.date.today())
        else:
            e_date.set_date(datetime.date.today())
        e_date.pack(fill='x')

        def save_record():
            new_date = e_date.get_date()
            if not new_date:
                messagebox.showerror("错误", "日期无效", parent=win)
                return
            
            conn = sqlite3.connect('landlord.db')
            c = conn.cursor()
            c.execute("UPDATE contract SET paid_until_date=? WHERE contract_id=?", (new_date.isoformat(), cid))
            conn.commit()
            conn.close()
            
            messagebox.showinfo("成功", "租金记录已更新", parent=win)
            win.destroy()
            self.update_dashboard_callback() # 刷新Dashboard

        WeChatButton(f, text="保存", command=save_record, width=15).pack(side='bottom', pady=20)

    def add_contract(self):
        """添加合同"""
        from dialogs import center_window
        win = tk.Toplevel(self.content.master)
        win.title("添加合同")
        center_window(win, 420, 520, self.content.master)
        win.configure(bg=COLORS['bg'])
        win.transient(self.content.master)
        win.grab_set()
        win.attributes('-topmost', True)

        f = tk.Frame(win, bg='white')
        f.pack(expand=True, fill='both', padx=40, pady=30)

        # 获取可用的房间（排除履行中的合同关联的房间）
        conn = sqlite3.connect('landlord.db')
        c = conn.cursor()
        c.execute("""
            SELECT r.room_id, r.room_name 
            FROM room r 
            LEFT JOIN contract c ON r.room_id = c.room_id AND c.status='履行中'
            WHERE r.user_id=? AND c.contract_id IS NULL
        """, (self.user_id,))
        rooms = c.fetchall()

        c.execute("""
            SELECT r.renter_id, r.renter_name 
            FROM renter r 
            LEFT JOIN contract c ON r.renter_id = c.renter_id AND c.status='履行中'
            WHERE r.user_id=? AND c.contract_id IS NULL
        """, (self.user_id,))
        renters = c.fetchall()
        conn.close()

        tk.Label(f, text="房间", bg='white', font=('Microsoft YaHei UI',10,'bold')).grid(row=0,column=0,sticky='w',pady=10)
        room_names = [r[1] for r in rooms]
        room_var = tk.StringVar()
        room_combo = ttk.Combobox(f, textvariable=room_var, values=room_names, state="readonly", width=27)
        room_combo.grid(row=0,column=1,pady=10)

        tk.Label(f, text="租客", bg='white', font=('Microsoft YaHei UI',10,'bold')).grid(row=1,column=0,sticky='w',pady=10)
        renter_names = [r[1] for r in renters]
        renter_var = tk.StringVar()
        renter_combo = ttk.Combobox(f, textvariable=renter_var, values=renter_names, state="readonly", width=27)
        renter_combo.grid(row=1,column=1,pady=10)

        tk.Label(f, text="开始日期", bg='white', font=('Microsoft YaHei UI',10,'bold')).grid(row=2,column=0,sticky='w',pady=10)
        e_start = DateEntry(f, width=27, background='darkblue', foreground='white', borderwidth=2, locale='zh_CN', date_pattern='yyyy-mm-dd')
        e_start.set_date(datetime.date.today())
        e_start.grid(row=2,column=1,pady=10)

        tk.Label(f, text="结束日期", bg='white', font=('Microsoft YaHei UI',10,'bold')).grid(row=3,column=0,sticky='w',pady=10)
        e_end = DateEntry(f, width=27, background='darkblue', foreground='white', borderwidth=2, locale='zh_CN', date_pattern='yyyy-mm-dd')
        e_end.grid(row=3,column=1,pady=10)

        tk.Label(f, text="租金", bg='white', font=('Microsoft YaHei UI',10,'bold')).grid(row=4,column=0,sticky='w',pady=10)
        e_rent = tk.Entry(f, width=30)
        e_rent.grid(row=4,column=1,pady=10)

        tk.Label(f, text="支付方式", bg='white', font=('Microsoft YaHei UI',10,'bold')).grid(row=5,column=0,sticky='w',pady=10)
        pay_method_var = tk.StringVar(value='月付')
        pay_method_combo = ttk.Combobox(f, textvariable=pay_method_var, values=['月付', '季付', '半年付', '年付'], state="readonly", width=27)
        pay_method_combo.grid(row=5,column=1,pady=10)

        tk.Label(f, text="押金", bg='white', font=('Microsoft YaHei UI',10,'bold')).grid(row=6,column=0,sticky='w',pady=10)
        e_pledge = tk.Entry(f, width=30)
        e_pledge.grid(row=6,column=1,pady=10)

        tk.Label(f, text="备注", bg='white', font=('Microsoft YaHei UI',10,'bold')).grid(row=7,column=0,sticky='w',pady=10)
        e_note = tk.Entry(f, width=30)
        e_note.grid(row=7,column=1,pady=10)

        def save():
            rname = room_var.get()
            rtname = renter_var.get()
            note = e_note.get().strip()
            if not rname or not rtname:
                messagebox.showerror("错误", "请选择房间和租客", parent=win)
                return
            
            start_date = e_start.get_date()
            end_date = e_end.get_date()
            start = start_date.isoformat()
            end = end_date.isoformat()
            
            if start_date > end_date:
                messagebox.showerror("错误", "开始日期不能晚于结束日期", parent=win)
                return

            valid_r, rent = self.validate_money(e_rent.get(), "租金")
            if not valid_r:
                messagebox.showerror("错误", "租金格式不正确", parent=win)
                e_rent.focus_set()
                return
                
            valid_p, pledge = self.validate_money(e_pledge.get(), "押金")
            if not valid_p:
                messagebox.showerror("错误", "押金格式不正确", parent=win)
                e_pledge.focus_set()
                return
            
            today = datetime.date.today()
            if start_date > today:
                status = "待开始"
            elif end_date and today > end_date:
                status = "已终止"
            else:
                status = "履行中"
            
            rid = next(r[0] for r in rooms if r[1] == rname) if rooms else None
            rtid = next(r[0] for r in renters if r[1] == rtname) if renters else None
            
            conn = sqlite3.connect('landlord.db')
            c = conn.cursor()
            
            total_rent = 0.0
            total_cash = total_rent + pledge
            pay_method = pay_method_var.get()
            
            # 初始化 last_payment_date (为了兼容旧逻辑)
            months_to_add = 1
            if '季付' in pay_method: months_to_add = 3
            elif '半年' in pay_method: months_to_add = 6
            elif '年付' in pay_method: months_to_add = 12
            init_last_pay_date = self._add_months_local(start_date, -months_to_add)
            
            # 【修改】初始化 paid_until_date
            # 默认设置为 开始日期 - 1天，意味着第一期还没付，Dashboard会立即提醒
            init_paid_until = start_date - datetime.timedelta(days=1)
            
            c.execute("INSERT INTO contract (user_id, room_id, renter_id, start_date, end_date, rent, pledge, note, status, total_rent, total_cash, payment_method, last_payment_date, paid_until_date) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                      (self.user_id, rid, rtid, start, end, rent, pledge, note, status, total_rent, total_cash, pay_method, init_last_pay_date, init_paid_until.isoformat()))
            cid = c.lastrowid
            
            c.execute("UPDATE renter SET contract_id=? WHERE renter_id=?", (cid, rtid))
            c.execute("SELECT renter_id FROM renter_link WHERE linked_renter_id=?", (rtid,))
            linked_renters = c.fetchall()
            for (lr_id,) in linked_renters:
                c.execute("UPDATE renter SET contract_id=? WHERE renter_id=?", (cid, lr_id))
            
            conn.commit()
            conn.close()
            win.destroy()
            self.update_dashboard_callback()
            self.load_contracts()
            self.update_rooms_callback()

        WeChatButton(f, text="确定添加", command=save, width=20).grid(row=8,column=0,columnspan=2,pady=25)

    def edit_contract(self):
        """编辑合同"""
        from dialogs import center_window
        sel = self.tree.selection()
        if not sel:
            return messagebox.showwarning("提示", "请先选择合同", parent=self.content.master)
        values = self.tree.item(sel[0])["values"]
        cid = values[0]

        win = tk.Toplevel(self.content.master)
        win.title("编辑合同")
        center_window(win, 420, 600, self.content.master)
        win.configure(bg=COLORS['bg'])
        win.transient(self.content.master)
        win.grab_set()
        win.attributes('-topmost', True)

        f = tk.Frame(win, bg='white')
        f.pack(expand=True, fill='both', padx=40, pady=30)

        conn = sqlite3.connect('landlord.db')
        c = conn.cursor()
        c.execute("SELECT room_id, renter_id, note, payment_method FROM contract WHERE contract_id=?", (cid,))
        contract_info = c.fetchone()
        current_room_id = contract_info[0]
        current_renter_id = contract_info[1]
        current_note = contract_info[2]
        current_pay_method = contract_info[3] if len(contract_info) > 3 else '月付'
        
        c.execute("""
            SELECT r.room_id, r.room_name 
            FROM room r 
            LEFT JOIN contract c ON r.room_id = c.room_id AND c.status='履行中'
            WHERE r.user_id=? AND (c.contract_id IS NULL OR c.contract_id=?)
        """, (self.user_id, cid))
        rooms = c.fetchall()
        
        c.execute("""
            SELECT r.renter_id, r.renter_name 
            FROM renter r 
            LEFT JOIN contract c ON r.renter_id = c.renter_id AND c.status='履行中'
            WHERE r.user_id=? AND (c.contract_id IS NULL OR c.contract_id=?)
        """, (self.user_id, cid))
        
        renters = c.fetchall()
        conn.close()

        tk.Label(f, text="房间", bg='white', font=('Microsoft YaHei UI',10,'bold')).grid(row=0,column=0,sticky='w',pady=10)
        room_names = [r[1] for r in rooms]
        current_room_name = next((r[1] for r in rooms if r[0] == current_room_id), "")
        room_var = tk.StringVar(value=current_room_name)
        room_combo = ttk.Combobox(f, textvariable=room_var, values=room_names, state="readonly", width=27)
        room_combo.grid(row=0,column=1,pady=10)

        tk.Label(f, text="租客", bg='white', font=('Microsoft YaHei UI',10,'bold')).grid(row=1,column=0,sticky='w',pady=10)
        renter_names = [r[1] for r in renters]
        current_renter_name = next((r[1] for r in renters if r[0] == current_renter_id), "")
        renter_var = tk.StringVar(value=current_renter_name)
        renter_combo = ttk.Combobox(f, textvariable=renter_var, values=renter_names, state="readonly", width=27)
        renter_combo.grid(row=1,column=1,pady=10)

        tk.Label(f, text="开始日期", bg='white', font=('Microsoft YaHei UI',10,'bold')).grid(row=2,column=0,sticky='w',pady=10)
        e_start = DateEntry(f, width=27, background='darkblue', foreground='white', borderwidth=2, locale='zh_CN', date_pattern='yyyy-mm-dd')
        try:
            e_start.set_date(datetime.date.fromisoformat(values[3]))
        except: pass
        e_start.grid(row=2,column=1,pady=10)

        tk.Label(f, text="结束日期", bg='white', font=('Microsoft YaHei UI',10,'bold')).grid(row=3,column=0,sticky='w',pady=10)
        e_end = DateEntry(f, width=27, background='darkblue', foreground='white', borderwidth=2, locale='zh_CN', date_pattern='yyyy-mm-dd')
        try:
            e_end.set_date(datetime.date.fromisoformat(values[4]))
        except: pass
        e_end.grid(row=3,column=1,pady=10)

        tk.Label(f, text="租金", bg='white', font=('Microsoft YaHei UI',10,'bold')).grid(row=4,column=0,sticky='w',pady=10)
        e_rent = tk.Entry(f, width=30)
        e_rent.insert(0, str(values[10]) if len(values) > 10 else '')
        e_rent.grid(row=4,column=1,pady=10)

        tk.Label(f, text="支付方式", bg='white', font=('Microsoft YaHei UI',10,'bold')).grid(row=5,column=0,sticky='w',pady=10)
        pay_method_var = tk.StringVar(value=current_pay_method)
        pay_method_combo = ttk.Combobox(f, textvariable=pay_method_var, values=['月付', '季付', '半年付', '年付'], state="readonly", width=27)
        pay_method_combo.grid(row=5,column=1,pady=10)

        tk.Label(f, text="押金", bg='white', font=('Microsoft YaHei UI',10,'bold')).grid(row=6,column=0,sticky='w',pady=10)
        e_pledge = tk.Entry(f, width=30)
        e_pledge.insert(0, str(values[11]) if len(values) > 11 else '')
        e_pledge.grid(row=6,column=1,pady=10)

        tk.Label(f, text="状态", bg='white', font=('Microsoft YaHei UI',10,'bold')).grid(row=7,column=0,sticky='w',pady=10)
        status_var = tk.StringVar(value=values[7])
        status_combo = ttk.Combobox(f, textvariable=status_var, values=["待开始", "履行中", "已结束", "已终止"], state="readonly", width=27)
        status_combo.grid(row=7,column=1,pady=10)

        tk.Label(f, text="已交租金", bg='white', font=('Microsoft YaHei UI',10,'bold')).grid(row=8,column=0,sticky='w',pady=10)
        e_total_rent = tk.Entry(f, width=30)
        e_total_rent.insert(0, str(values[12]) if len(values) > 12 else '')
        e_total_rent.grid(row=8,column=1,pady=10)

        tk.Label(f, text="备注", bg='white', font=('Microsoft YaHei UI',10,'bold')).grid(row=9,column=0,sticky='w',pady=10)
        e_note = tk.Entry(f, width=30)
        e_note.insert(0, current_note or '')
        e_note.grid(row=9,column=1,pady=10)

        def save():
            selected_room_name = room_var.get()
            selected_renter_name = renter_var.get()
            if not selected_room_name or not selected_renter_name:
                messagebox.showerror("错误", "请选择房间和租客", parent=win)
                return
            new_room_id = next((r[0] for r in rooms if r[1] == selected_room_name), None)
            new_renter_id = next((r[0] for r in renters if r[1] == selected_renter_name), None)
            
            start_date = e_start.get_date()
            end_date = e_end.get_date()
            status = status_var.get()
            note = e_note.get().strip()
            
            valid_r, rent = self.validate_money(e_rent.get(), "租金")
            if not valid_r: return
            valid_p, pledge = self.validate_money(e_pledge.get(), "押金")
            if not valid_p: return
            valid_t, total_rent = self.validate_money(e_total_rent.get(), "已交租金")
            if not valid_t: return
            
            conn = sqlite3.connect('landlord.db')
            c = conn.cursor()
            
            c.execute("UPDATE contract SET room_id=?, renter_id=?, start_date=?, end_date=?, rent=?, pledge=?, status=?, total_rent=?, total_cash=?, note=?, payment_method=? WHERE contract_id=?", 
                      (new_room_id, new_renter_id, start_date.isoformat(), end_date.isoformat(), rent, pledge, status, total_rent, total_rent+pledge, note, pay_method_var.get(), cid))
            
            if status == '履行中':
                c.execute("UPDATE renter SET contract_id=? WHERE renter_id=?", (cid, new_renter_id))
            else:
                c.execute("UPDATE renter SET contract_id=NULL WHERE contract_id=?", (cid,))
            
            conn.commit()
            conn.close()
            win.destroy()
            self.load_contracts()
            self.update_rooms_callback()

        WeChatButton(f, text="保存修改", command=save, width=20).grid(row=10,column=0,columnspan=2,pady=25)

    def delete_contract(self):
        """删除合同"""
        sel = self.tree.selection()
        if not sel: return
        if not messagebox.askyesno("确认", "确定删除？"): return
        cid = self.tree.item(sel[0])["values"][0]
        conn = sqlite3.connect('landlord.db')
        c = conn.cursor()
        c.execute("SELECT room_id FROM contract WHERE contract_id=?", (cid,))
        rid = c.fetchone()[0]
        c.execute("DELETE FROM contract WHERE contract_id=?", (cid,))
        c.execute("UPDATE renter SET contract_id=NULL WHERE contract_id=?", (cid,))
        conn.commit()
        conn.close()
        self.load_contracts()

    def validate_money(self, val, name):
        val = val.strip()
        if not val: return True, 0.0
        clean_val = val.replace('¥', '').replace(',', '').replace(' ', '')
        try:
            num = float(clean_val)
            return num >= 0, num
        except:
            return False, 0.0
