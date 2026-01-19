# database.py
"""数据库模块 - 包含数据库初始化和数据操作"""

import sqlite3
import datetime
import warnings
import calendar
warnings.filterwarnings("ignore", category=UserWarning)

def init_db():
    conn = sqlite3.connect('landlord.db')
    # Register date adapter to avoid deprecation warning
    sqlite3.register_adapter(datetime.date, lambda val: val.isoformat())
    sqlite3.register_converter("DATE", lambda val: datetime.date.fromisoformat(val.decode()))
    c = conn.cursor()
    
    # 用户表
    c.execute('''CREATE TABLE IF NOT EXISTS user (
                 id INTEGER PRIMARY KEY AUTOINCREMENT,
                 user TEXT UNIQUE NOT NULL,
                 password TEXT NOT NULL)''')
    
    # 楼栋表 - 添加状态字段
    c.execute('''CREATE TABLE IF NOT EXISTS house (
                 house_id INTEGER PRIMARY KEY AUTOINCREMENT,
                 user_id INTEGER NOT NULL,
                 house_name TEXT NOT NULL,
                 house_add TEXT,
                 house_floor INTEGER,
                 room_count INTEGER DEFAULT 0,
                 house_cost REAL DEFAULT 0,
                 house_status TEXT DEFAULT '可用',  -- 可用/维修中/不可用
                 FOREIGN KEY(user_id) REFERENCES user(id) ON DELETE CASCADE)''')
    
    # 房屋表 - 添加状态字段
    c.execute('''CREATE TABLE IF NOT EXISTS room (
                 room_id INTEGER PRIMARY KEY AUTOINCREMENT,
                 user_id INTEGER NOT NULL,
                 house_id INTEGER NOT NULL,
                 room_name TEXT NOT NULL,
                 room_area REAL DEFAULT 0,
                 furniture_count INTEGER DEFAULT 0,
                 room_cost REAL DEFAULT 0,
                 room_status TEXT DEFAULT '空置',  -- 空置/出租中/维修中/不可用
                 room_rent REAL DEFAULT 0,
                 FOREIGN KEY(user_id) REFERENCES user(id) ON DELETE CASCADE,
                 FOREIGN KEY(house_id) REFERENCES house(house_id) ON DELETE CASCADE)''')
    
    # 家具表
    c.execute('''CREATE TABLE IF NOT EXISTS furniture (
                 furniture_id INTEGER PRIMARY KEY AUTOINCREMENT,
                 user_id INTEGER NOT NULL,
                 room_id INTEGER,
                 furniture TEXT NOT NULL,
                 note TEXT,
                 count INTEGER DEFAULT 1,
                 furniture_cost REAL DEFAULT 0,
                 total_cost REAL DEFAULT 0,
                 FOREIGN KEY(user_id) REFERENCES user(id) ON DELETE CASCADE,
                 FOREIGN KEY(room_id) REFERENCES room(room_id) ON DELETE SET NULL)''')
    
    # 合同表
    c.execute('''CREATE TABLE IF NOT EXISTS contract (
                 contract_id INTEGER PRIMARY KEY AUTOINCREMENT,
                 user_id INTEGER NOT NULL,
                 room_id INTEGER,
                 start_date DATE,
                 rent REAL,
                 pledge REAL,
                 note TEXT,
                 total_rent REAL DEFAULT 0,
                 total_cash REAL DEFAULT 0,
                 status TEXT DEFAULT '待生效',  -- 待生效/履行中/已结束
                 end_date DATE,
                 FOREIGN KEY(user_id) REFERENCES user(id) ON DELETE CASCADE,
                 FOREIGN KEY(room_id) REFERENCES room(room_id))''')
    
    # 租户表
    c.execute('''CREATE TABLE IF NOT EXISTS renter (
                 renter_id INTEGER PRIMARY KEY AUTOINCREMENT,
                 user_id INTEGER NOT NULL,
                 renter_name TEXT NOT NULL,
                 contract_id INTEGER,
                 renter_idcard TEXT,
                 renter_tel TEXT,
                 renter_wechat TEXT,
                 renter_lock_id TEXT,
                 renter_lock_pass TEXT,
                 renter_finger TEXT,
                 note TEXT,
                 is_blacklisted INTEGER DEFAULT 0,
                 FOREIGN KEY(user_id) REFERENCES user(id) ON DELETE CASCADE,
                 FOREIGN KEY(contract_id) REFERENCES contract(contract_id) ON DELETE CASCADE)''')
    
    # 黑名单表
    c.execute('''CREATE TABLE IF NOT EXISTS blacklist (
                 blacklist_id INTEGER PRIMARY KEY AUTOINCREMENT,
                 renter_id INTEGER NOT NULL,
                 reason TEXT,
                 create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                 FOREIGN KEY(renter_id) REFERENCES renter(renter_id) ON DELETE CASCADE)''')
    
    # 租客关联表
    c.execute('''CREATE TABLE IF NOT EXISTS renter_link (
                 link_id INTEGER PRIMARY KEY AUTOINCREMENT,
                 renter_id INTEGER NOT NULL,
                 linked_renter_id INTEGER NOT NULL,
                 FOREIGN KEY(renter_id) REFERENCES renter(renter_id) ON DELETE CASCADE,
                 FOREIGN KEY(linked_renter_id) REFERENCES renter(renter_id) ON DELETE CASCADE,
                 UNIQUE(renter_id, linked_renter_id))''')
    
    # ========== 数据库升级部分 ==========
    
    # 升级合同表：添加 payment_method
    c.execute("PRAGMA table_info(contract)")
    contract_cols = [col[1] for col in c.fetchall()]
    
    if 'payment_method' not in contract_cols:
        print("升级数据库: 添加 payment_method 字段...")
        c.execute("ALTER TABLE contract ADD COLUMN payment_method TEXT DEFAULT '月付'")
        c.execute("UPDATE contract SET payment_method='月付' WHERE payment_method IS NULL")
    
    # 升级合同表：添加 last_payment_date
    if 'last_payment_date' not in contract_cols:
        print("升级数据库: 添加 last_payment_date 字段...")
        c.execute("ALTER TABLE contract ADD COLUMN last_payment_date DATE")
        c.execute("UPDATE contract SET last_payment_date=start_date WHERE last_payment_date IS NULL")

    # 升级合同表：添加 renter_id
    if 'renter_id' not in contract_cols:
        print("升级数据库: 添加 renter_id 字段...")
        c.execute("ALTER TABLE contract ADD COLUMN renter_id INTEGER")
        c.execute("""
            UPDATE contract 
            SET renter_id = (
                SELECT renter_id FROM renter 
                WHERE renter.contract_id = contract.contract_id 
                LIMIT 1
            )
        """)

    # 升级合同表：添加 paid_until_date
    if 'paid_until_date' not in contract_cols:
        print("升级数据库: 添加 paid_until_date 字段...")
        c.execute("ALTER TABLE contract ADD COLUMN paid_until_date DATE")

    # 默认管理员
    c.execute("SELECT COUNT(*) FROM user")
    if c.fetchone()[0] == 0:
        c.execute("INSERT INTO user (user, password) VALUES (?,?)", ("admin", "admin123"))
    
    conn.commit()
    conn.close()

def update_all_costs(user_id):
    """更新所有成本数据和房间数统计"""
    import sqlite3
    conn = sqlite3.connect('landlord.db')
    c = conn.cursor()
    uid = user_id
    # 1. 更新家具总成本
    c.execute("UPDATE furniture SET total_cost = count * furniture_cost WHERE user_id=?", (uid,))
    
    # 2. 更新房间的家具数和成本
    # 注意：这里统计家具数和成本时不限制房间状态，只要房间存在就计算其所属家具
    c.execute("""UPDATE room SET
                 furniture_count = (SELECT COUNT(*) FROM furniture WHERE room_id = room.room_id AND room.user_id = furniture.user_id),
                 room_cost = (SELECT IFNULL(SUM(total_cost), 0) FROM furniture WHERE room_id = room.room_id AND room.user_id = furniture.user_id)
                 WHERE user_id=?""", (uid,))
    
    # 3. 更新楼栋的房间数和成本
    # 【关键修改】更新 room_count 时，不再限制 room_status
    # 统计所有属于该楼栋的房间数，确保添加或删除任何房间后楼栋房间数都会变化
    c.execute("""UPDATE house SET
                 room_count = (SELECT COUNT(*) FROM room WHERE room.house_id = house.house_id AND room.user_id = house.user_id),
                 house_cost = (SELECT IFNULL(SUM(room_cost), 0) FROM room WHERE room.house_id = house.house_id AND room.user_id = house.user_id)
                 WHERE user_id=?""", (uid,))
    conn.commit()
    conn.close()
