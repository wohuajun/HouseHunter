# main.py
"""主程序入口 - 房东房屋管理软件"""

import tkinter as tk
from tkinter import messagebox
from config import COLORS
from widgets import SidebarButton
from database import init_db, update_all_costs
from auth import show_login_page
from dashboard import create_dashboard_page
from house import HouseManager
from room import RoomManager
from furniture import FurnitureManager
from renter import RenterManager
from contract import ContractManager

class App:
    def __init__(self):
        init_db()
        self.root = tk.Tk()
        self.root.title("HOUSE HUNTER")
        self.root.geometry("1480x800")
        self.root.configure(bg=COLORS['bg'])
        self.current_user_id = None
        self.current_page = None
        
        # 管理器实例
        self.house_manager = None
        self.room_manager = None
        self.furniture_manager = None
        self.renter_manager = None
        self.contract_manager = None
        
        self.show_login()
        self.root.mainloop()

    def show_login(self):
        """显示登录页面"""
        for w in self.root.winfo_children():
            w.destroy()
        show_login_page(self.root, self.on_login_success)

    def on_login_success(self, user_id):
        """登录成功回调"""
        self.current_user_id = user_id
        self.show_main()

    def show_main(self):
        """显示主界面"""
        for w in self.root.winfo_children():
            w.destroy()

        # 左侧导航
        sidebar = tk.Frame(self.root, bg=COLORS['sidebar'], width=220)
        sidebar.pack(side='left', fill='y')
        sidebar.pack_propagate(False)

        tk.Label(sidebar, text="功能菜单", bg=COLORS['sidebar'], fg=COLORS['text'],
                 font=('Microsoft YaHei UI',12,'bold')).pack(pady=25)

        self.nav_buttons = [
            SidebarButton(sidebar, text="📊 概览仪表盘", command=lambda: self.switch_page(0)),
            SidebarButton(sidebar, text="🏢 楼栋管理", command=lambda: self.switch_page(1)),
            SidebarButton(sidebar, text="🚪 房屋管理", command=lambda: self.switch_page(2)),
            SidebarButton(sidebar, text="🪑 家具管理", command=lambda: self.switch_page(3)),
            SidebarButton(sidebar, text="👥 租客管理", command=lambda: self.switch_page(4)),
            SidebarButton(sidebar, text="📝 合同管理", command=lambda: self.switch_page(5)),
        ]
        for btn in self.nav_buttons:
            btn.pack(fill='x', padx=10, pady=3)

        exit_btn = SidebarButton(sidebar, text="📴 退出登录", command=self.logout)
        exit_btn.config(bg=COLORS['exit'], fg='white', activebackground=COLORS['exit_hover'])
        exit_btn.unbind("<Enter>")
        exit_btn.unbind("<Leave>")
        exit_btn.pack(fill='x', padx=10, pady=3, side='bottom')

        # 右侧内容区
        self.content = tk.Frame(self.root, bg=COLORS['bg'])
        self.content.pack(side='right', fill='both', expand=True)

        self.pages = [
            self.page_dashboard,
            self.page_house,
            self.page_room,
            self.page_furniture,
            self.page_renter,
            self.page_contract
        ]
        self.switch_page(0)

    def switch_page(self, idx):
        """切换页面"""
        for w in self.content.winfo_children():
            w.destroy()
        for i, btn in enumerate(self.nav_buttons):
            if i == idx:
                btn.select()
            else:
                btn.deselect()
        self.current_page = idx
        self.pages[idx]()

    def logout(self):
        """退出登录"""
        if messagebox.askyesno("退出", "确定退出登录？"):
            self.current_user_id = None
            self.show_login()

    def update_all_costs(self):
        """更新所有成本"""
        update_all_costs(self.current_user_id)

    # ------------------- 页面创建函数 -------------------
    def page_dashboard(self):
        """概览仪表盘页面"""
        create_dashboard_page(self.content, self.current_user_id)

    def page_house(self):
        """楼栋管理页面"""
        self.house_manager = HouseManager(self.content, self.current_user_id, self.update_all_costs)
        self.house_manager.create_page()

    def page_room(self):
        """房屋管理页面"""
        self.room_manager = RoomManager(
            self.content, 
            self.current_user_id, 
            self.update_all_costs,
            lambda preselected_room_id=None: self.switch_page(3) or (self.furniture_manager and self.furniture_manager.add_furniture(preselected_room_id))
        )
        self.room_manager.create_page()

    def page_furniture(self):
        """家具管理页面"""
        self.furniture_manager = FurnitureManager(self.content, self.current_user_id, self.update_all_costs)
        self.furniture_manager.create_page()

    def page_renter(self):
        """租客管理页面"""
        self.renter_manager = RenterManager(self.content, self.current_user_id)
        self.renter_manager.create_page()

    def page_contract(self):
        """合同管理页面"""
        self.contract_manager = ContractManager(
            self.content, 
            self.current_user_id,
            lambda: self.room_manager and self.room_manager.load_rooms(),
            self.update_all_costs
        )
        self.contract_manager.create_page()

if __name__ == "__main__":
    App()
