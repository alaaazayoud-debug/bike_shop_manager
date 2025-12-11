import hashlib
import uuid

SECRET_SALT = "BikeShop_Secure_Salt_2025"

def generate_activation_key(machine_id):
    """Generates an activation key from a machine ID."""
    raw_data = f"{machine_id}{SECRET_SALT}"
    # Use SHA256 and take first 12 chars for a readable key
    hashed = hashlib.sha256(raw_data.encode()).hexdigest().upper()
    return f"{hashed[:4]}-{hashed[4:8]}-{hashed[8:12]}"

if __name__ == "__main__":
    print("=== Bike Shop Manager Key Generator ===")
    print("أداة توليد مفاتيح التفعيل - خاصة بالمطور فقط")
    print("----------------------------------------")
    
    while True:
        machine_id = input("\nأدخل رقم جهاز العميل (Machine ID): ").strip()
        if not machine_id:
            break
            
        key = generate_activation_key(machine_id)
        print(f"\n✅ كود التفعيل لهذا الجهاز هو:")
        print(f"👉  {key}  👈")
        print("\n----------------------------------------")
