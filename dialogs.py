# dialogs.py
"""对话框辅助模块 - 包含窗口居中等辅助函数"""

def center_window(win, width, height, root):
    """窗口居中函数 - 修复版"""
    # 确保窗口已经完全初始化
    win.update_idletasks()
    
    # 获取主窗口的位置和大小
    root_x = root.winfo_x()
    root_y = root.winfo_y()
    root_width = root.winfo_width()
    root_height = root.winfo_height()
    
    # 计算新窗口的位置（居中）
    x = root_x + (root_width - width) // 2
    y = root_y + (root_height - height) // 2
    
    # 设置窗口位置和大小
    win.geometry(f"{width}x{height}+{x}+{y}")
