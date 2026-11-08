from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGroupBox, 
    QDoubleSpinBox, QPushButton, QMessageBox, QFrame
)
from PyQt5.QtCore import Qt
from database import get_db_connection

class SettingsPage(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(20, 20, 20, 20)
        self.layout.setSpacing(20)
        
        # Header
        title = QLabel("الإعدادات العامة")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #007bff; margin-bottom: 10px;")
        self.layout.addWidget(title)
        
        # --- Currency Settings ---
        currency_group = QGroupBox("إعدادات العملة")
        currency_group.setStyleSheet("QGroupBox { border: 1px solid #ced4da; border-radius: 5px; margin-top: 20px; font-size: 16px; color: #333333; padding: 15px; background-color: #f8f9fa; } QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 5px; }")
        curr_layout = QVBoxLayout(currency_group)
        
        lbl_rate = QLabel("سعر صرف الدولار الحالي:")
        lbl_rate.setStyleSheet("font-size: 14px; color: #666;")
        
        self.rate_input = QDoubleSpinBox()
        self.rate_input.setRange(1, 1000000)
        self.rate_input.setDecimals(2)
        self.rate_input.setPrefix("1 USD = ")
        self.rate_input.setSuffix(" SYP")
        self.rate_input.setStyleSheet("font-size: 16px; padding: 5px; font-weight: bold;")
        
        btn_save_rate = QPushButton("حفظ سعر الصرف")
        btn_save_rate.setStyleSheet("background-color: #27ae60; color: white; padding: 8px; font-weight: bold; font-size: 14px;")
        btn_save_rate.clicked.connect(self.save_exchange_rate)
        
        curr_layout.addWidget(lbl_rate)
        curr_layout.addWidget(self.rate_input)
        curr_layout.addWidget(btn_save_rate)
        self.layout.addWidget(currency_group)
        
        # --- Pricing Settings ---
        pricing_group = QGroupBox("إعدادات التسعير والمخزون")
        pricing_group.setStyleSheet("QGroupBox { border: 1px solid #ced4da; border-radius: 5px; margin-top: 20px; font-size: 16px; color: #333333; padding: 15px; background-color: #f8f9fa; } QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 5px; }")
        price_layout = QVBoxLayout(pricing_group)
        
        lbl_margin = QLabel("نسبة الربح الافتراضية (%):")
        lbl_margin.setStyleSheet("font-size: 14px; color: #666;")
        
        self.margin_input = QDoubleSpinBox()
        self.margin_input.setRange(0, 500)
        self.margin_input.setDecimals(2)
        self.margin_input.setSuffix("%")
        self.margin_input.setStyleSheet("font-size: 16px; padding: 5px; font-weight: bold;")
        
        btn_save_margin = QPushButton("حفظ النسبة وتحديث المخزون")
        btn_save_margin.setStyleSheet("background-color: #e67e22; color: white; padding: 8px; font-weight: bold; font-size: 14px;")
        btn_save_margin.clicked.connect(self.update_stock_prices)
        
        lbl_warning = QLabel("تنبيه: تحديث النسبة سيقوم بإعادة حساب 'سعر المبيع' لجميع المواد الموجودة في المخزون بناءً على سعر تكلفتها.")
        lbl_warning.setStyleSheet("color: #e74c3c; font-size: 12px; margin-top: 5px;")
        lbl_warning.setWordWrap(True)
        
        price_layout.addWidget(lbl_margin)
        price_layout.addWidget(self.margin_input)
        price_layout.addWidget(lbl_warning)
        price_layout.addWidget(btn_save_margin)
        self.layout.addWidget(pricing_group)
        
        self.layout.addStretch()
        
        self.load_settings()

    def get_setting(self, key):
        conn = get_db_connection()
        try:
            cur = conn.execute("SELECT value FROM settings WHERE key = ?", (key,))
            res = cur.fetchone()
            return res[0] if res else None
        finally:
            conn.close()

    def set_setting(self, key, value):
        conn = get_db_connection()
        try:
            conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, str(value)))
            conn.commit()
        finally:
            conn.close()

    def load_settings(self):
        try:
            rate = self.get_setting('exchange_rate')
            margin = self.get_setting('profit_margin')
            
            if rate:
                self.rate_input.setValue(float(rate))
            if margin:
                self.margin_input.setValue(float(margin))
        except Exception as e:
            print(f"Error loading settings: {e}")

    def save_exchange_rate(self):
        rate = self.rate_input.value()
        try:
            self.set_setting('exchange_rate', rate)
            QMessageBox.information(self, "تم الحفظ", "تم تحديث سعر صرف الدولار بنجاح.\nسيتم اعتماده في الفواتير الجديدة.")
        except Exception as e:
            QMessageBox.critical(self, "خطأ", str(e))

    def update_stock_prices(self):
        margin = self.margin_input.value()
        
        confirm = QMessageBox.question(
            self, "تأكيد التحديث", 
            f"هل أنت متأكد من إعادة تسعير جميع المواد بنسبة ربح {margin}%؟\nسيتم تغيير أسعار المبيع الحالية.",
            QMessageBox.Yes | QMessageBox.No
        )
        if confirm != QMessageBox.Yes:
            return
            
        conn = get_db_connection()
        try:
            # Save margin first
            conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", ('profit_margin', str(margin)))
            
            # Update all products: sell_price = price_usd * (1 + margin/100)
            multiplier = 1 + (margin / 100.0)
            conn.execute("UPDATE products SET sell_price = price_usd * ?", (multiplier,))
            conn.commit()
            
            QMessageBox.information(self, "تم التحديث", f"تم تحديث أسعار المخزون بنجاح.\nنسبة الربح الجديدة: {margin}%")
            
        except Exception as e:
            conn.rollback()
            QMessageBox.critical(self, "خطأ", str(e))
        finally:
            conn.close()
