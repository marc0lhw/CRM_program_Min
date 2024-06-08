import sqlite3

def init_db():
    conn = sqlite3.connect('customer_management.db')
    c = conn.cursor()

    # 고객 정보 테이블
    c.execute('''
    CREATE TABLE IF NOT EXISTS customers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        phone TEXT,
        mileage REAL DEFAULT 0,
        group_type TEXT DEFAULT '일반',
        deleted_status TEXT DEFAULT '',
        refusal_status TEXT DEFAULT ''
    )
    ''')

    # 구매 내역 테이블
    c.execute('''
    CREATE TABLE IF NOT EXISTS purchases (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_id INTEGER,
        amount REAL,
        payment_method TEXT,
        date TIMESTAMP DEFAULT (datetime('now', 'localtime')),
        FOREIGN KEY (customer_id) REFERENCES customers (id)
    )
    ''')

    # 환불 내역 테이블
    c.execute('''
    CREATE TABLE IF NOT EXISTS refunds (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_id INTEGER,
        amount REAL,
        date TIMESTAMP DEFAULT (datetime('now', 'localtime')),
        FOREIGN KEY (customer_id) REFERENCES customers (id)
    )
    ''')

    conn.commit()
    conn.close()

init_db()