from database import get_db_connection
import sqlite3

def seed_products():
    products = [
        {"name": "فحمات فرامل (Brake Pads)", "code": "101", "quantity": 50, "price_usd": 10.00},
        {"name": "فلتر زيت (Oil Filter)", "code": "102", "quantity": 30, "price_usd": 5.00},
        {"name": "فلتر هواء (Air Filter)", "code": "103", "quantity": 20, "price_usd": 8.00},
        {"name": "بوجية (Spark Plug)", "code": "104", "quantity": 100, "price_usd": 3.00},
        {"name": "جنزير (Chain)", "code": "105", "quantity": 15, "price_usd": 25.00}
    ]

    conn = get_db_connection()
    cursor = conn.cursor()

    print("Starting product import...")
    
    added_count = 0
    skipped_count = 0

    for product in products:
        try:
            # Check if product with same code exists
            cursor.execute("SELECT id FROM products WHERE code = ?", (product['code'],))
            existing = cursor.fetchone()

            if existing:
                print(f"Skipping {product['name']} (Code: {product['code']}) - Already exists.")
                skipped_count += 1
            else:
                cursor.execute(
                    "INSERT INTO products (name, code, quantity, price_usd) VALUES (?, ?, ?, ?)",
                    (product['name'], product['code'], product['quantity'], product['price_usd'])
                )
                print(f"Added {product['name']}")
                added_count += 1
        except sqlite3.Error as e:
            print(f"Error adding {product['name']}: {e}")

    conn.commit()
    conn.close()

    print("-" * 30)
    print(f"Import complete.")
    print(f"Added: {added_count}")
    print(f"Skipped: {skipped_count}")

if __name__ == "__main__":
    seed_products()
