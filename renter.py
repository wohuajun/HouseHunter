# renter.py
"""租客管理模块 - 租客的增删改查功能，增加黑名单和合同状态显示，以及租客关联功能"""

import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from config import COLORS
from widgets import WeChatButton


class RenterManager:
    """租客管理器"""
    
    def __init__(self, content, user_id):
        self.content = content
        self.user_id = user_id
        self.tree = None
        
    def create_page(self):
        """创建租客管理页面"""
        tk.Label(self.content, text="租客管理", font=('Microsoft YaHei UI',18,'bold'),
                 bg=COLORS['bg'], fg=COLORS['text']).pack(pady=25)

        self.tree = ttk.Treeview(self.content, columns=("renter_id","renter_name","room_name","renter_idcard","renter_tel","renter_wechat","renter_lock_id","renter_lock_pass","renter_finger","note","contract_status","is_blacklisted","linked_info"), show="headings", height=18)
        cols = [
            ("renter_id","ID",60),
            ("renter_name","姓名",140),
            ("room_name","房间",160),
            ("renter_idcard","身份证",180),
            ("renter_tel","电话",120),
            ("renter_wechat","微信",120),
            ("renter_lock_id","密码锁ID",120),
            ("renter_lock_pass","密码锁密码",120),
            ("renter_finger","指纹ID",120),
            ("note","备注",200),
            ("contract_status","合同状态",100),
            ("is_blacklisted","黑名单",80),
            ("linked_info","关联租客",150)
        ]
        for col, text, w in cols:
            self.tree.heading(col, text=text)
            self.tree.column(col, width=w, anchor='center')
        self.tree.pack(fill='both', expand=True, padx=30, pady=10)

        btns = tk.Frame(self.content, bg=COLORS['bg'])
        btns.pack(pady=10)
        WeChatButton(btns, text="添加租客", command=self.add_renter).pack(side='left', padx=8)
        WeChatButton(btns, text="编辑租客", command=self.edit_renter).pack(side='left', padx=8)
        WeChatButton(btns, text="删除租客", command=self.delete_renter).pack(side='left', padx=8)
        WeChatButton(btns, text="关联租客", command=self.link_renters).pack(side='left', padx=8)

        self.load_renters()
    
    def load_renters(self):
        """加载租客数据"""
        try:
            for i in self.tree.get_children():
                self.tree.delete(i)
            conn = sqlite3.connect('landlord.db')
            c = conn.cursor()
            
            c.execute("""
                SELECT r.renter_id, r.renter_name, rm.room_name, r.renter_idcard, r.renter_tel, r.renter_wechat, 
                       r.renter_lock_id, r.renter_lock_pass, r.renter_finger, r.note, 
                       c.status as contract_status, r.is_blacklisted,
                       (
                           SELECT GROUP_CONCAT(sub_r.renter_name, ', ')
                           FROM renter_link rl
                           JOIN renter sub_r ON rl.renter_id = sub_r.renter_id
                           WHERE rl.linked_renter_id = r.renter_id
                       ) as sub_renters,
                       (
                           SELECT main_r.renter_name
                           FROM renter_link rl
                           JOIN renter main_r ON rl.linked_renter_id = main_r.renter_id
                           WHERE rl.renter_id = r.renter_id
                       ) as main_renter
                FROM renter r 
                LEFT JOIN contract c ON r.contract_id = c.contract_id 
                LEFT JOIN room rm ON c.room_id = rm.room_id 
                WHERE r.user_id=?
            """, (self.user_id,))
            
            rows = c.fetchall()
            for row in rows:
                row = list(row)
                
                if row[13]: 
                    link_info = f"主租客: {row[13]}"
                elif row[12]:
                    link_info = row[12]
                else:
                    link_info = ""
                
                final_row = row[:12]
                final_row[3] = final_row[3][:6] + '********' + final_row[3][-4:] if final_row[3] else ''
                final_row.append(link_info)
                
                contract_status = final_row[10] 
                is_blacklisted = final_row[11]
                room_name = final_row[2]
                
                # 只有"履行中"才显示房间，否则视为无房
                if contract_status != '履行中':
                    room_name = ''
                
                if is_blacklisted:
                    bg_color = '#FF0000'
                elif contract_status == '履行中':
                    bg_color = '#FFA500'
                else:
                    bg_color = 'white'
                
                final_row[2] = room_name
                
                self.tree.insert("", "end", values=final_row, tags=(bg_color,))
                self.tree.tag_configure(bg_color, background=bg_color)
            
            conn.close()
        except Exception as e:
            print(f"加载租客列表出错: {e}")

    def add_renter(self):
        """添加租客"""
        from dialogs import center_window
        win = tk.Toplevel(self.content.master)
        win.title("添加租客")
        center_window(win, 420, 550, self.content.master)
        win.configure(bg=COLORS['bg'])
        win.transient(self.content.master)
        win.grab_set()
        win.attributes('-topmost', True)

        f = tk.Frame(win, bg='white')
        f.pack(expand=True, fill='both', padx=40, pady=30)

        tk.Label(f, text="租客姓名", bg='white', font=('Microsoft YaHei UI',10,'bold')).grid(row=0,column=0,sticky='w',pady=10)
        e_name = tk.Entry(f, width=30)
        e_name.grid(row=0,column=1,pady=10)

        tk.Label(f, text="身份证号", bg='white', font=('Microsoft YaHei UI',10,'bold')).grid(row=1,column=0,sticky='w',pady=10)
        e_idcard = tk.Entry(f, width=30)
        e_idcard.grid(row=1,column=1,pady=10)

        tk.Label(f, text="电话", bg='white', font=('Microsoft YaHei UI',10,'bold')).grid(row=2,column=0,sticky='w',pady=10)
        e_tel = tk.Entry(f, width=30)
        e_tel.grid(row=2,column=1,pady=10)

        tk.Label(f, text="微信", bg='white', font=('Microsoft YaHei UI',10,'bold')).grid(row=3,column=0,sticky='w',pady=10)
        e_wechat = tk.Entry(f, width=30)
        e_wechat.grid(row=3,column=1,pady=10)

        tk.Label(f, text="密码锁ID", bg='white', font=('Microsoft YaHei UI',10,'bold')).grid(row=4,column=0,sticky='w',pady=10)
        e_lock_id = tk.Entry(f, width=30)
        e_lock_id.grid(row=4,column=1,pady=10)

        tk.Label(f, text="密码锁密码", bg='white', font=('Microsoft YaHei UI',10,'bold')).grid(row=5,column=0,sticky='w',pady=10)
        e_lock_pass = tk.Entry(f, width=30)
        e_lock_pass.grid(row=5,column=1,pady=10)

        tk.Label(f, text="指纹ID", bg='white', font=('Microsoft YaHei UI',10,'bold')).grid(row=6,column=0,sticky='w',pady=10)
        e_finger = tk.Entry(f, width=30)
        e_finger.grid(row=6,column=1,pady=10)

        tk.Label(f, text="备注", bg='white', font=('Microsoft YaHei UI',10,'bold')).grid(row=7,column=0,sticky='w',pady=10)
        e_note = tk.Entry(f, width=30)
        e_note.grid(row=7,column=1,pady=10)

        tk.Label(f, text="黑名单", bg='white', font=('Microsoft YaHei UI',10,'bold')).grid(row=8,column=0,sticky='w',pady=10)
        is_blacklisted_var = tk.IntVar(value=0)
        blacklisted_check = tk.Checkbutton(f, variable=is_blacklisted_var, bg='white', font=('Microsoft YaHei UI',10))
        blacklisted_check.grid(row=8,column=1,sticky='w',pady=10)

        tk.Label(f, text="关联租客", bg='white', font=('Microsoft YaHei UI',10,'bold')).grid(row=9,column=0,sticky='w',pady=10)
        conn = sqlite3.connect('landlord.db')
        c = conn.cursor()
        c.execute("SELECT renter_id, renter_name FROM renter WHERE user_id=?", (self.user_id,))
        renters = c.fetchall()
        conn.close()
        renter_names = [r[1] for r in renters]
        renter_var = tk.StringVar()
        combo = ttk.Combobox(f, textvariable=renter_var, values=renter_names, state="readonly", width=27)
        combo.grid(row=9,column=1,pady=10)

        def save():
            name = e_name.get().strip()
            if not name:
                messagebox.showerror("错误", "请填写姓名")
                return
            idcard = e_idcard.get().strip()
            tel = e_tel.get().strip()
            wechat = e_wechat.get().strip()
            lock_id = e_lock_id.get().strip()
            lock_pass = e_lock_pass.get().strip()
            finger = e_finger.get().strip()
            note = e_note.get().strip()
            is_blacklisted = is_blacklisted_var.get()
            linked_renter_name = renter_var.get()
            
            conn = sqlite3.connect('landlord.db')
            c = conn.cursor()
            c.execute("INSERT INTO renter (user_id, renter_name, renter_idcard, renter_tel, renter_wechat, renter_lock_id, renter_lock_pass, renter_finger, note, is_blacklisted) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                      (self.user_id, name, idcard, tel, wechat, lock_id, lock_pass, finger, note, is_blacklisted))
            
            new_renter_id = c.lastrowid
            
            if linked_renter_name:
                linked_renter_id = next(r[0] for r in renters if r[1] == linked_renter_name)
                c.execute("INSERT INTO renter_link (renter_id, linked_renter_id) VALUES (?, ?)", (new_renter_id, linked_renter_id))
                c.execute("SELECT contract_id FROM renter WHERE renter_id=?", (linked_renter_id,))
                contract_row = c.fetchone()
                if contract_row and contract_row[0]:
                    c.execute("UPDATE renter SET contract_id=? WHERE renter_id=?", (contract_row[0], new_renter_id))
            
            conn.commit()
            conn.close()
            win.destroy()
            self.load_renters()

        WeChatButton(f, text="确定添加", command=save, width=20).grid(row=10,column=0,columnspan=2,pady=25)

    def edit_renter(self):
        """编辑租客"""
        from dialogs import center_window
        sel = self.tree.selection()
        if not sel:
            return messagebox.showwarning("提示", "请先选择租客")
        values = self.tree.item(sel[0])["values"]
        rid = values[0]

        win = tk.Toplevel(self.content.master)
        win.title("编辑租客")
        center_window(win, 420, 600, self.content.master)
        win.configure(bg=COLORS['bg'])
        win.transient(self.content.master)
        win.grab_set()
        win.attributes('-topmost', True)

        f = tk.Frame(win, bg='white')
        f.pack(expand=True, fill='both', padx=40, pady=30)

        tk.Label(f, text="租客姓名", bg='white', font=('Microsoft YaHei UI',10,'bold')).grid(row=0,column=0,sticky='w',pady=10)
        e_name = tk.Entry(f, width=30)
        e_name.insert(0, values[1])
        e_name.grid(row=0,column=1,pady=10)

        tk.Label(f, text="身份证号", bg='white', font=('Microsoft YaHei UI',10,'bold')).grid(row=1,column=0,sticky='w',pady=10)
        e_idcard = tk.Entry(f, width=30)
        e_idcard.insert(0, values[3])
        e_idcard.grid(row=1,column=1,pady=10)

        tk.Label(f, text="电话", bg='white', font=('Microsoft YaHei UI',10,'bold')).grid(row=2,column=0,sticky='w',pady=10)
        e_tel = tk.Entry(f, width=30)
        e_tel.insert(0, values[4])
        e_tel.grid(row=2,column=1,pady=10)

        tk.Label(f, text="微信", bg='white', font=('Microsoft YaHei UI',10,'bold')).grid(row=3,column=0,sticky='w',pady=10)
        e_wechat = tk.Entry(f, width=30)
        e_wechat.insert(0, values[5])
        e_wechat.grid(row=3,column=1,pady=10)

        tk.Label(f, text="密码锁ID", bg='white', font=('Microsoft YaHei UI',10,'bold')).grid(row=4,column=0,sticky='w',pady=10)
        e_lock_id = tk.Entry(f, width=30)
        e_lock_id.insert(0, values[6])
        e_lock_id.grid(row=4,column=1,pady=10)

        tk.Label(f, text="密码锁密码", bg='white', font=('Microsoft YaHei UI',10,'bold')).grid(row=5,column=0,sticky='w',pady=10)
        e_lock_pass = tk.Entry(f, width=30)
        e_lock_pass.insert(0, values[7])
        e_lock_pass.grid(row=5,column=1,pady=10)

        tk.Label(f, text="指纹ID", bg='white', font=('Microsoft YaHei UI',10,'bold')).grid(row=6,column=0,sticky='w',pady=10)
        e_finger = tk.Entry(f, width=30)
        e_finger.insert(0, values[8] if len(values) > 8 else '')
        e_finger.grid(row=6,column=1,pady=10)

        tk.Label(f, text="备注", bg='white', font=('Microsoft YaHei UI',10,'bold')).grid(row=7,column=0,sticky='w',pady=10)
        e_note = tk.Entry(f, width=30)
        e_note.insert(0, values[9] if len(values) > 9 else '')
        e_note.grid(row=7,column=1,pady=10)

        tk.Label(f, text="黑名单", bg='white', font=('Microsoft YaHei UI',10,'bold')).grid(row=8,column=0,sticky='w',pady=10)
        is_blacklisted_var = tk.IntVar(value=1 if values[11] else 0)
        blacklisted_check = tk.Checkbutton(f, variable=is_blacklisted_var, bg='white', font=('Microsoft YaHei UI',10))
        blacklisted_check.grid(row=8,column=1,sticky='w',pady=10)

        tk.Label(f, text="关联租客", bg='white', font=('Microsoft YaHei UI',10,'bold')).grid(row=9,column=0,sticky='w',pady=10)
        
        conn = sqlite3.connect('landlord.db')
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM renter_link WHERE linked_renter_id=?", (rid,))
        has_subs = c.fetchone()[0] > 0
        c.execute("SELECT r.renter_name FROM renter_link rl JOIN renter r ON rl.linked_renter_id = r.renter_id WHERE rl.renter_id=?", (rid,))
        main_renter_row = c.fetchone()
        conn.close()

        if has_subs:
            renter_var = tk.StringVar(value="主租客")
            combo = ttk.Combobox(f, textvariable=renter_var, values=["主租客"], state="disabled", width=27)
            combo.grid(row=9,column=1,pady=10)
            current_main_name = None
        elif main_renter_row:
            current_main_name = main_renter_row[0]
            display_text = f"主租客: {current_main_name}"
            renter_var = tk.StringVar(value=display_text)
            combo = ttk.Combobox(f, textvariable=renter_var, values=[display_text, "无"], state="readonly", width=27)
            combo.grid(row=9,column=1,pady=10)
        else:
            conn = sqlite3.connect('landlord.db')
            c = conn.cursor()
            c.execute("SELECT renter_id, renter_name FROM renter WHERE user_id=? AND renter_id!=?", (self.user_id, rid))
            renters = c.fetchall()
            conn.close()
            renter_names = [r[1] for r in renters]
            renter_var = tk.StringVar(value="")
            combo = ttk.Combobox(f, textvariable=renter_var, values=renter_names, state="readonly", width=27)
            combo.grid(row=9,column=1,pady=10)
            current_main_name = None

        def save():
            name = e_name.get().strip()
            if not name:
                messagebox.showerror("错误", "请填写姓名")
                return
            idcard = e_idcard.get().strip()
            tel = e_tel.get().strip()
            wechat = e_wechat.get().strip()
            lock_id = e_lock_id.get().strip()
            lock_pass = e_lock_pass.get().strip()
            finger = e_finger.get().strip()
            note = e_note.get().strip()
            is_blacklisted = is_blacklisted_var.get()
            
            conn = sqlite3.connect('landlord.db')
            c = conn.cursor()
            
            c.execute("UPDATE renter SET renter_name=?, renter_idcard=?, renter_tel=?, renter_wechat=?, renter_lock_id=?, renter_lock_pass=?, renter_finger=?, note=?, is_blacklisted=? WHERE renter_id=?",
                      (name, idcard, tel, wechat, lock_id, lock_pass, finger, note, is_blacklisted, rid))
            
            selected_value = renter_var.get()
            
            if has_subs:
                pass
            elif main_renter_row:
                if selected_value == "无" or not selected_value:
                    c.execute("DELETE FROM renter_link WHERE renter_id=?", (rid,))
                    c.execute("UPDATE renter SET contract_id=NULL WHERE renter_id=?", (rid,))
            else:
                if selected_value:
                    conn2 = sqlite3.connect('landlord.db')
                    c2 = conn2.cursor()
                    c2.execute("SELECT renter_id FROM renter WHERE user_id=? AND renter_name=?", (self.user_id, selected_value))
                    target_row = c2.fetchone()
                    conn2.close()
                    if target_row:
                        target_id = target_row[0]
                        c.execute("INSERT INTO renter_link (renter_id, linked_renter_id) VALUES (?, ?)", (rid, target_id))
                        c.execute("SELECT contract_id FROM renter WHERE renter_id=?", (target_id,))
                        contract_row = c.fetchone()
                        if contract_row and contract_row[0]:
                            c.execute("UPDATE renter SET contract_id=? WHERE renter_id=?", (contract_row[0], rid))
            
            conn.commit()
            conn.close()
            win.destroy()
            self.load_renters()

        WeChatButton(f, text="保存修改", command=save, width=20).grid(row=10,column=0,columnspan=2,pady=25)

    def delete_renter(self):
        """删除租客"""
        sel = self.tree.selection()
        if not sel:
            return messagebox.showwarning("提示", "请先选择租客")
        if not messagebox.askyesno("确认", "确定删除？"):
            return
        rid = self.tree.item(sel[0])["values"][0]
        conn = sqlite3.connect('landlord.db')
        c = conn.cursor()
        c.execute("DELETE FROM renter WHERE renter_id=?", (rid,))
        conn.commit()
        conn.close()
        self.load_renters()

    def link_renters(self):
        """关联租客"""
        from dialogs import center_window
        sel = self.tree.selection()
        if not sel:
            return messagebox.showwarning("提示", "请先选择要关联的租客")
        
        sub_renter_id = self.tree.item(sel[0])["values"][0]
        win = tk.Toplevel(self.content.master)
        win.title("关联租客")
        center_window(win, 420, 400, self.content.master)
        win.configure(bg=COLORS['bg'])
        win.transient(self.content.master)
        win.grab_set()
        win.attributes('-topmost', True)

        f = tk.Frame(win, bg='white')
        f.pack(expand=True, fill='both', padx=40, pady=30)

        tk.Label(f, text="选择主租客", bg='white', font=('Microsoft YaHei UI',10,'bold')).grid(row=0,column=0,sticky='w',pady=10)
        
        conn = sqlite3.connect('landlord.db')
        c = conn.cursor()
        c.execute("SELECT renter_id, renter_name FROM renter WHERE user_id=? AND renter_id!=?", (self.user_id, sub_renter_id))
        renters = c.fetchall()
        conn.close()
        
        renter_names = [r[1] for r in renters]
        renter_var = tk.StringVar()
        combo = ttk.Combobox(f, textvariable=renter_var, values=renter_names, state="readonly", width=27)
        combo.grid(row=0,column=1,pady=10)

        def save_link():
            selected_name = renter_var.get()
            if not selected_name:
                messagebox.showerror("错误", "请选择主租客", parent=win)
                return
            
            main_renter_id = next(r[0] for r in renters if r[1] == selected_name)
            
            conn = sqlite3.connect('landlord.db')
            c = conn.cursor()
            
            c.execute("SELECT 1 FROM renter_link WHERE renter_id=? AND linked_renter_id=?", (sub_renter_id, main_renter_id))
            if c.fetchone():
                messagebox.showwarning("提示", "这两个租客已经关联过了", parent=win)
                conn.close()
                return
            
            c.execute("INSERT INTO renter_link (renter_id, linked_renter_id) VALUES (?, ?)", (sub_renter_id, main_renter_id))
            
            c.execute("SELECT contract_id FROM renter WHERE renter_id=?", (main_renter_id,))
            contract_row = c.fetchone()
            if contract_row and contract_row[0]:
                c.execute("UPDATE renter SET contract_id=? WHERE renter_id=?", (contract_row[0], sub_renter_id))
            
            conn.commit()
            conn.close()
            win.destroy()
            self.load_renters()

        WeChatButton(f, text="确认关联", command=save_link, width=20).grid(row=1,column=0,columnspan=2,pady=25)
