# dashboard.py (最新修改版)
"""仪表盘模块 - 数据统计概览"""

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

class DashboardManager:
    """仪表盘管理器"""
    GLOBAL_APP_DATE = datetime.date.today()

    def __init__(self, content, user_id, to_room_page_callback=None):
        self.content = content
        self.user_id = user_id
        self.to_room_page_callback = to_room_page_callback
        self.payment_tree = None
        self.btn_edit_payment = None  # 用于保存编辑按钮的引用
        
    def create_page(self):
        """创建仪表盘页面"""
        for widget in self.content.winfo_children():
            widget.destroy()
            
        # === 顶部标题栏 ===
        header_frame = tk.Frame(self.content, bg=COLORS['bg'])
        header_frame.pack(fill='x', padx=30, pady=20)
        
        tk.Label(header_frame, text="系统概览", font=('Microsoft YaHei UI',18,'bold'),
                 bg=COLORS['bg'], fg=COLORS['text']).pack(side='left')
        
        date_frame = tk.Frame(header_frame, bg=COLORS['bg'])
        date_frame.pack(side='right')
        
        self.date_label = tk.Label(date_frame, text="", 
                                    bg=COLORS['bg'], fg="#555", font=('Microsoft YaHei UI', 11, 'bold'))
        self.date_label.pack(side='left')
        
        WeChatButton(date_frame, text="修改日期", command=self.open_date_picker, 
                     width=8).pack(side='left', padx=(10, 0))
        
        self.update_date_display()

        # === 统计数据容器 ===
        stats_frame = tk.Frame(self.content, bg=COLORS['bg'])
        stats_frame.pack(fill='both', expand=True, padx=30, pady=10)

        stats_frame.columnconfigure(0, weight=1)
        stats_frame.columnconfigure(1, weight=1)
        stats_frame.columnconfigure(2, weight=1)

        # 第一行卡片
        self.lbl_total_rooms = self._create_stat_card(stats_frame, "总房间数", "0", "蓝色", "#E3F2FD", "#1976D2", 0, 0)
        self.lbl_vacant_rooms = self._create_stat_card(stats_frame, "空置房间", "0", "绿色", "#E8F5E9", "#388E3C", 0, 1)
        self.lbl_total_cost = self._create_stat_card(stats_frame, "房屋总成本", "¥0.00", "青色", "#E0F7FA", "#0097A7", 0, 2)  # 恢复总成本卡片

        # 第二行卡片
        self.lbl_active_contracts = self._create_stat_card(stats_frame, "履行中合同", "0", "紫色", "#F3E5F5", "#7B1FA2", 1, 0)
        self.lbl_monthly_income = self._create_stat_card(stats_frame, "本月租金收益", "¥0.00", "红色", "#FFEBEE", "#D32F2F", 1, 1)
        self.lbl_total_received = self._create_stat_card(stats_frame, "累计租金收入", "¥0.00", "蓝色", "#E3F2FD", "#1976D2", 1, 2)

        # 第三行：近期到期提醒列表
        row3 = tk.Frame(stats_frame, bg=COLORS['bg'])
        row3.grid(row=2, column=0, columnspan=3, sticky="nsew", pady=10)
        
        tk.Label(row3, text="即将到期合同 (7天内)", font=('Microsoft YaHei UI',14,'bold'),
                 bg=COLORS['bg'], fg=COLORS['text'], anchor='w').pack(fill='x', pady=(0, 5))

        cols = ("room", "renter", "end_date", "days_left")
        self.tree = ttk.Treeview(row3, columns=cols, show="headings", height=6)
        self.tree.heading("room", text="房间")
        self.tree.heading("renter", text="租客")
        self.tree.heading("end_date", text="到期日期")
        self.tree.heading("days_left", text="剩余天数")
        self.tree.column("room", width=150, anchor='center')
        self.tree.column("renter", width=150, anchor='center')
        self.tree.column("end_date", width=150, anchor='center')
        self.tree.column("days_left", width=100, anchor='center')
        self.tree.pack(fill='both', expand=True)

        # 第四行：即将到期租金提醒
        row4 = tk.Frame(stats_frame, bg=COLORS['bg'])
        row4.grid(row=3, column=0, columnspan=3, sticky="nsew", pady=(20, 10))
        
        header4 = tk.Frame(row4, bg=COLORS['bg'])
        header4.pack(fill='x', pady=(0, 5))
        tk.Label(header4, text="租金催缴提醒 (逾期或10天内)", font=('Microsoft YaHei UI',14,'bold'),
                 bg=COLORS['bg'], fg='#FF5722', anchor='w').pack(side='left')
        
        # 【修改】移除了“√ 标记已付”，改为“编辑租金”按钮，初始禁用
        self.btn_edit_payment = WeChatButton(header4, text="编辑租金", command=self.open_rental_record, 
                                             bg_color='#FF5722', hover_color='#E64A19', width=10)
        self.btn_edit_payment.pack(side='right')
        self.btn_edit_payment.config(state=tk.DISABLED)  # 初始状态禁用

        pay_cols = ("room", "renter", "due_date", "days_left", "amount", "contract_id")
        self.payment_tree = ttk.Treeview(row4, columns=pay_cols, show="headings", height=6)
        self.payment_tree.heading("room", text="房间")
        self.payment_tree.heading("renter", text="租客")
        self.payment_tree.heading("due_date", text="已付截止日期")
        self.payment_tree.heading("days_left", text="剩余天数")
        self.payment_tree.heading("amount", text="金额")
        self.payment_tree.heading("contract_id", text="ID")
        
        self.payment_tree.column("room", width=120, anchor='center')
        self.payment_tree.column("renter", width=120, anchor='center')
        self.payment_tree.column("due_date", width=120, anchor='center')
        self.payment_tree.column("days_left", width=100, anchor='center')
        self.payment_tree.column("amount", width=100, anchor='center')
        self.payment_tree.column("contract_id", width=0, stretch=False)
        self.payment_tree.pack(fill='both', expand=True)
        
        # 绑定选择事件
        self.payment_tree.bind('<<TreeviewSelect>>', self.on_payment_select)

        self.load_dashboard_data()

    def _create_stat_card(self, parent, title, value, color_name, bg_color, text_color, row, col):
        """创建统计卡片"""
        card = tk.Frame(parent, bg=bg_color, relief="flat", bd=0)
        card.grid(row=row, column=col, sticky="nsew", padx=5, pady=5)
        
        tk.Label(card, text=title, font=('Microsoft YaHei UI', 10), 
                 bg=bg_color, fg=text_color).pack(pady=(10, 0))
        
        val_label = tk.Label(card, text=value, font=('Microsoft YaHei UI', 24, 'bold'), 
                             bg=bg_color, fg=text_color)
        val_label.pack(pady=(5, 10))
        
        return val_label

    def update_date_display(self):
        """更新日期显示"""
        date_str = self.GLOBAL_APP_DATE.strftime("%Y年%m月%d日")
        self.date_label.config(text=f"当前日期: {date_str}")

    def open_date_picker(self):
        """打开日期选择窗口"""
        win = tk.Toplevel(self.content.master)
        win.title("修改系统日期")
        win.geometry("300x150")
        screen_width = win.winfo_screenwidth()
        screen_height = win.winfo_screenheight()
        x = (screen_width // 2) - (300 // 2)
        y = (screen_height // 2) - (150 // 2)
        win.geometry(f"+{x}+{y}")
        win.configure(bg=COLORS['bg'])
        win.transient(self.content.master)
        win.grab_set()
        
        f = tk.Frame(win, bg='white')
        f.pack(expand=True, fill='both', padx=30, pady=20)
        
        tk.Label(f, text="选择日期:", bg='white', font=('Microsoft YaHei UI', 10, 'bold')).pack(pady=10)
        e_date = DateEntry(f, width=25, background='darkblue', foreground='white', borderwidth=2, locale='zh_CN', date_pattern='yyyy-mm-dd')
        e_date.set_date(self.GLOBAL_APP_DATE)
        e_date.pack(pady=10)
        
        def save_date():
            new_date = e_date.get_date()
            if new_date:
                DashboardManager.GLOBAL_APP_DATE = new_date
                self.update_date_display()
                self.load_dashboard_data()
                messagebox.showinfo("成功", "系统日期已更新")
                win.destroy()
            else:
                messagebox.showerror("错误", "无效的日期")
                
        WeChatButton(f, text="确定", command=save_date, width=15).pack(pady=10)

    def on_payment_select(self, event):
        """处理租金记录选择"""
        selected = self.payment_tree.selection()
        if selected:
            self.btn_edit_payment.config(state=tk.NORMAL)
        else:
            self.btn_edit_payment.config(state=tk.DISABLED)

    def open_rental_record(self):
        """打开租金记录编辑窗口"""
        sel = self.payment_tree.selection()
        if not sel:
            return
        
        vals = self.payment_tree.item(sel[0])["values"]
        contract_id = vals[5]
        
        from dialogs import center_window
        win = tk.Toplevel(self.content.master)
        win.title("编辑租金记录")
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
        c.execute("SELECT room_id, renter_id, paid_until_date FROM contract WHERE contract_id=?", (contract_id,))
        info = c.fetchone()
        
        c.execute("SELECT room_name FROM room WHERE room_id=?", (info[0],))
        rname = c.fetchone()[0]
        c.execute("SELECT renter_name FROM renter WHERE renter_id=?", (info[1],))
        rtname = c.fetchone()[0] if info[1] else "未知"
        
        current_paid_until = info[2]
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
            c.execute("UPDATE contract SET paid_until_date=? WHERE contract_id=?", (new_date.isoformat(), contract_id))
            conn.commit()
            conn.close()
            
            messagebox.showinfo("成功", "租金记录已更新", parent=win)
            win.destroy()
            self.load_dashboard_data()

        WeChatButton(f, text="保存", command=save_record, width=15).pack(side='bottom', pady=20)

    def load_dashboard_data(self):
        """加载仪表盘数据"""
        try:
            conn = sqlite3.connect('landlord.db')
            c = conn.cursor()
            
            # 1. 基础统计
            c.execute("SELECT COUNT(*) FROM room WHERE user_id=?", (self.user_id,))
            total_rooms = c.fetchone()[0]
            
            c.execute("SELECT COUNT(*) FROM contract WHERE user_id=? AND status='履行中'", (self.user_id,))
            active_contracts = c.fetchone()[0]
            
            c.execute("SELECT SUM(room_cost) FROM room WHERE user_id=?", (self.user_id,))
            total_cost = c.fetchone()[0] or 0.0
            
            c.execute("SELECT SUM(rent) FROM contract WHERE user_id=? AND status='履行中'", (self.user_id,))
            monthly_income = c.fetchone()[0] or 0.0
            
            # 新增累计租金统计
            c.execute("""
                SELECT COALESCE(SUM(total_rent), 0) 
                FROM contract 
                WHERE user_id=? AND status IN ('履行中', '已结束')
            """, (self.user_id,))
            total_received = c.fetchone()[0] or 0.0
            
            # 更新所有统计卡片
            self.lbl_total_rooms.config(text=str(total_rooms))
            self.lbl_vacant_rooms.config(text=str(total_rooms - active_contracts))  # 空置房间数 = 总房间数 - 履行中合同数
            self.lbl_total_cost.config(text=f"¥{total_cost:,.2f}")  # 恢复总成本显示
            self.lbl_active_contracts.config(text=str(active_contracts))
            self.lbl_monthly_income.config(text=f"¥{monthly_income:,.2f}")
            self.lbl_total_received.config(text=f"¥{total_received:,.2f}")  # 更新累计租金
            
            # 2. 即将到期合同列表
            current_date = self.GLOBAL_APP_DATE
            end_date_limit = current_date + datetime.timedelta(days=7)
            
            c.execute("""
                SELECT rm.room_name, rt.renter_name, c.end_date, c.contract_id
                FROM contract c
                LEFT JOIN room rm ON c.room_id = rm.room_id
                LEFT JOIN renter rt ON c.renter_id = rt.renter_id
                WHERE c.user_id=? AND c.end_date <= ? AND c.status='履行中'
                ORDER BY c.end_date
            """, (self.user_id, end_date_limit.isoformat()))
            
            for i in self.tree.get_children(): self.tree.delete(i)
            for row in c.fetchall():
                r_name, rt_name, end_str, cid = row
                end_date = datetime.date.fromisoformat(end_str) if end_str else None
                days_left = (end_date - current_date).days if end_date else 0
                self.tree.insert("", "end", values=(r_name, rt_name, end_str, f"{days_left}天"))
            
            # 3. 即将到期租金提醒
            c.execute("""
                SELECT c.contract_id, rm.room_name, rt.renter_name, c.rent, 
                       c.start_date, c.payment_method, c.paid_until_date
                FROM contract c
                LEFT JOIN room rm ON c.room_id = rm.room_id
                LEFT JOIN renter rt ON c.renter_id = rt.renter_id
                WHERE c.user_id=? AND c.status='履行中'
            """, (self.user_id,))
            
            for i in self.payment_tree.get_children(): self.payment_tree.delete(i)
            
            contracts = c.fetchall()
            
            for cid, room_name, renter_name, rent, start_str, pay_method, paid_until_str in contracts:
                try:
                    start_date = datetime.date.fromisoformat(start_str)
                except:
                    continue
                
                # 优先使用 paid_until_date
                paid_until_date = datetime.date.fromisoformat(paid_until_str) if paid_until_str else start_date
                
                # 计算剩余天数
                days_diff = (paid_until_date - current_date).days
                
                # 显示逻辑
                if days_diff < 0:
                    day_str = f"已逾期{abs(days_diff)}天"
                elif 0 <= days_diff <= 10:
                    day_str = f"剩余{days_diff}天"
                else:
                    continue  # 超过10天不显示
                
                self.payment_tree.insert("", "end", values=(
                    room_name, 
                    renter_name, 
                    paid_until_date.isoformat(), 
                    day_str,
                    f"¥{rent:,.2f}",
                    cid
                ))
            
            # 列表刷新后，如果没有选中项，确保按钮禁用
            if not self.payment_tree.selection():
                self.btn_edit_payment.config(state=tk.DISABLED)
            
            conn.close()
        except Exception as e:
            messagebox.showerror("错误", f"数据加载失败: {str(e)}")
            import traceback
            traceback.print_exc()

# 主程序入口适配
def create_dashboard_page(content, user_id, to_room_page_callback=None):
    manager = DashboardManager(content, user_id, to_room_page_callback)
    manager.create_page()