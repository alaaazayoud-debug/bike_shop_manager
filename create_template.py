import pandas as pd
import os

def create_template():
    # Define the standard columns
    data = {
        'اسم المادة': ['مثال: إطار دراجة', 'مثال: زيت محرك'],
        'الكمية': [50, 20],
        'سعر الشراء ($)': [10.5, 5.0],
        'سعر المبيع ($)': [15.0, 8.0]
    }
    
    df = pd.DataFrame(data)
    
    # Save to Excel
    file_name = 'product_import_template.xlsx'
    try:
        df.to_excel(file_name, index=False)
        print(f"✅ تم إنشاء ملف القالب بنجاح: {file_name}")
        print("يرجى تعبئة هذا الملف بالبيانات واستخدامه في الاستيراد.")
    except Exception as e:
        print(f"❌ حدث خطأ أثناء إنشاء الملف: {e}")
        print("تأكد من تثبيت المكتبات: pip install pandas openpyxl")

if __name__ == "__main__":
    create_template()
