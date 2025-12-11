import sqlite3
import os

DB_NAME = "bike_shop.db"

def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Products Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            code TEXT UNIQUE,
            quantity INTEGER DEFAULT 0,
            price_usd REAL NOT NULL,
            sell_price REAL DEFAULT 0
        )
    ''')
    
    # Migration: Check if sell_price exists (for existing databases)
    cursor.execute("PRAGMA table_info(products)")
    columns = [info[1] for info in cursor.fetchall()]
    if 'sell_price' not in columns:
        print("Migrating database: Adding sell_price column...")
        cursor.execute("ALTER TABLE products ADD COLUMN sell_price REAL DEFAULT 0")
    
    # Customers Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT,
            total_debt REAL DEFAULT 0
        )
    ''')
    
    # Invoices Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS invoices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER,
            date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            total_amount_syp REAL NOT NULL,
            exchange_rate REAL NOT NULL,
            paid_amount REAL DEFAULT 0,
            discount_amount REAL DEFAULT 0,
            FOREIGN KEY (customer_id) REFERENCES customers (id)
        )
    ''')

    # Migration: Check for discount_amount in invoices
    cursor.execute("PRAGMA table_info(invoices)")
    cols = [info[1] for info in cursor.fetchall()]
    if 'discount_amount' not in cols:
        print("Migrating database: Adding discount_amount column...")
        cursor.execute("ALTER TABLE invoices ADD COLUMN discount_amount REAL DEFAULT 0")
    
    # Invoice Items Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS invoice_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_id INTEGER,
            product_id INTEGER,
            quantity INTEGER NOT NULL,
            unit_price_syp REAL NOT NULL,
            FOREIGN KEY (invoice_id) REFERENCES invoices (id),
            FOREIGN KEY (product_id) REFERENCES products (id)
        )
    ''')
    
    # Initialize Default Customer
    cursor.execute("SELECT id FROM customers WHERE name = 'مبيعات نقدية يومية'")
    if not cursor.fetchone():
        cursor.execute("INSERT INTO customers (name, phone, total_debt) VALUES (?, ?, ?)", 
                       ('مبيعات نقدية يومية', '0000', 0))
    
    # Settings Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    ''')
    
    # Initialize Defaults
    defaults = {
        'exchange_rate': '12000',
        'profit_margin': '4'
    }
    for key, val in defaults.items():
        cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", (key, val))
    
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print("Database initialized successfully.")
