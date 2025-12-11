import os
import sqlite3
from database import init_db, get_db_connection

def test_database():
    # Clean up existing db
    if os.path.exists("bike_shop.db"):
        os.remove("bike_shop.db")
    
    print("Initializing database...")
    init_db()
    
    if not os.path.exists("bike_shop.db"):
        print("FAIL: Database file not created.")
        return

    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Test Products Table
    print("Testing Products table...")
    cursor.execute("INSERT INTO products (name, code, quantity, price_usd) VALUES (?, ?, ?, ?)",
                   ("Spark Plug", "SP001", 10, 5.5))
    conn.commit()
    
    cursor.execute("SELECT * FROM products WHERE code = ?", ("SP001",))
    product = cursor.fetchone()
    if product and product['name'] == "Spark Plug" and product['price_usd'] == 5.5:
        print("PASS: Product inserted and retrieved.")
    else:
        print("FAIL: Product insertion/retrieval failed.")

    # Test Customers Table
    print("Testing Customers table...")
    cursor.execute("INSERT INTO customers (name, phone) VALUES (?, ?)", ("John Doe", "123456789"))
    conn.commit()
    
    cursor.execute("SELECT * FROM customers WHERE name = ?", ("John Doe",))
    customer = cursor.fetchone()
    if customer and customer['phone'] == "123456789":
        print("PASS: Customer inserted and retrieved.")
    else:
        print("FAIL: Customer insertion/retrieval failed.")

    conn.close()
    print("Database verification complete.")

if __name__ == "__main__":
    test_database()
