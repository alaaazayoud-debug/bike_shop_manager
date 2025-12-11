import sys
import os
import uuid
import hashlib
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, 
    QHBoxLayout, QPushButton, QStackedWidget, QLabel, QMessageBox,
    QDialog, QLineEdit, QFormLayout
)
from PyQt5.QtGui import QFont, QIcon, QPixmap
from PyQt5.QtCore import Qt

# Import Pages
from dashboard_page import DashboardPage
from products_page import ProductsPage
from invoices_page import InvoicesPage
from debts_page import DebtsPage
from invoice_history_page import InvoiceHistoryPage
from settings_page import SettingsPage
from database import init_db

SECRET_SALT = "BikeShop_Secure_Salt_2025"

def get_machine_id():
    return str(uuid.getnode())

def generate_expected_key(machine_id):
    raw_data = f"{machine_id}{SECRET_SALT}"
    hashed = hashlib.sha256(raw_data.encode()).hexdigest().upper()
    return f"{hashed[:4]}-{hashed[4:8]}-{hashed[8:12]}"

class ActivationDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("تفعيل البرنامج")
        self.setFixedSize(400, 250)
        self.setStyleSheet("""
            QDialog { background-color: #252526; color: white; }
            QLabel { color: white; font-size: 14px; }
            QLineEdit { padding: 8px; font-size: 14px; border: 1px solid #555; border-radius: 4px; background-color: #333; color: #00BFFF; font-weight: bold; }
            QPushButton { background-color: #0078d4; color: white; padding: 10px; border-radius: 5px; font-weight: bold; }
            QPushButton:hover { background-color: #106ebe; }
        """)
        
        layout = QVBoxLayout(self)
        
        # Instructions
        lbl_info = QLabel("هذه النسخة غير مفعلة.\nيرجى إرسال رقم الجهاز للمطور للحصول على كود التفعيل.")
        lbl_info.setAlignment(Qt.AlignCenter)
        layout.addWidget(lbl_info)
        
        # Machine ID Display
        self.machine_id = get_machine_id()
        layout.addSpacing(10)
        layout.addWidget(QLabel("رقم جهازك (Machine ID):"))
        self.txt_machine_id = QLineEdit(self.machine_id)
        self.txt_machine_id.setReadOnly(True)
        self.txt_machine_id.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.txt_machine_id)
        
        # Activation Key Input
        layout.addSpacing(10)
        layout.addWidget(QLabel("كود التفعيل (Activation Key):"))
        self.txt_key = QLineEdit()
        self.txt_key.setPlaceholderText("XXXX-XXXX-XXXX")
        self.txt_key.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.txt_key)
        
        # Activate Button
        layout.addSpacing(20)
        btn_activate = QPushButton("تفعيل الآن")
        btn_activate.clicked.connect(self.validate_key)
        layout.addWidget(btn_activate)
        
    def validate_key(self):
        entered_key = self.txt_key.text().strip().upper()
        expected_key = generate_expected_key(self.machine_id)
        
        if entered_key == expected_key:
            # Save license
            try:
                with open("bike_manager.lic", "w") as f:
                    f.write(entered_key)
                QMessageBox.information(self, "نجاح", "تم تفعيل البرنامج بنجاح!\nشكراً لشرائك النسخة الأصلية.")
                self.accept()
            except Exception as e:
                QMessageBox.critical(self, "خطأ", f"فشل حفظ الترخيص: {e}")
        else:
            QMessageBox.warning(self, "خطأ", "كود التفعيل غير صحيح.\nتأكد من إرسال رقم الجهاز الصحيح للمطور.")

def check_license():
    license_file = "bike_manager.lic"
    machine_id = get_machine_id()
    expected_key = generate_expected_key(machine_id)
    
    if os.path.exists(license_file):
        try:
            with open(license_file, "r") as f:
                saved_key = f.read().strip()
            if saved_key == expected_key:
                return True
        except:
            pass
            
    # If no valid license found, show dialog
    app = QApplication.instance() or QApplication(sys.argv)
    dialog = ActivationDialog()
    if dialog.exec_() == QDialog.Accepted:
        return True
    return False

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("نظام إدارة محل قطع غيار الدراجات - حسين ديب")
        self.setGeometry(100, 100, 1200, 800)
        
        # Try to load logo icon
        if os.path.exists('logo.png'):
            self.setWindowIcon(QIcon('logo.png'))
        
        # Initialize DB
        init_db()

        # Main Layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ===== Sidebar =====
        sidebar = QWidget()
        sidebar.setFixedWidth(250)
        sidebar.setStyleSheet("background-color: #252526; border-right: 1px solid #3e3e42;")
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(10, 20, 10, 20)
        sidebar_layout.setSpacing(10)

        # Logo
        lbl_logo = QLabel()
        if os.path.exists('logo.png'):
            pixmap = QPixmap('logo.png')
            if not pixmap.isNull():
                lbl_logo.setPixmap(pixmap.scaled(150, 150, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            lbl_logo.setText("Bike Shop")
            lbl_logo.setStyleSheet("font-size: 24px; font-weight: bold; color: #00BFFF;")
        
        lbl_logo.setAlignment(Qt.AlignCenter)
        sidebar_layout.addWidget(lbl_logo)
        sidebar_layout.addSpacing(20)

        # Buttons
        btn_dashboard = QPushButton("الرئيسية")
        btn_products = QPushButton("القطع (المخزون)")
        btn_invoices = QPushButton("فاتورة جديدة")
        btn_history = QPushButton("سجل الفواتير")
        btn_debts = QPushButton("الديون")
        btn_settings = QPushButton("الإعدادات")

        for btn in [btn_dashboard, btn_products, btn_invoices, btn_history, btn_debts, btn_settings]:
            btn.setFixedHeight(50)
            btn.setCursor(Qt.PointingHandCursor)
            sidebar_layout.addWidget(btn)

        sidebar_layout.addStretch()
        
        # Footer
        lbl_footer = QLabel("v1.0 - Licensed")
        lbl_footer.setStyleSheet("color: #666; font-size: 12px;")
        lbl_footer.setAlignment(Qt.AlignCenter)
        sidebar_layout.addWidget(lbl_footer)

        # ===== Content Pages =====
        self.pages = QStackedWidget()
        self.pages.setStyleSheet("background-color: #1e1e1e;") # Softer Dark Background
        
        self.page_dashboard = DashboardPage()
        self.page_products = ProductsPage()
        self.page_invoices = InvoicesPage()
        self.page_debts = DebtsPage()
        self.page_history = InvoiceHistoryPage()
        self.page_settings = SettingsPage()

        self.pages.addWidget(self.page_dashboard)
        self.pages.addWidget(self.page_products)
        self.pages.addWidget(self.page_invoices)
        self.pages.addWidget(self.page_debts)
        self.pages.addWidget(self.page_history)
        self.pages.addWidget(self.page_settings)

        # Connect Buttons
        btn_dashboard.clicked.connect(lambda: self.pages.setCurrentIndex(0))
        btn_dashboard.clicked.connect(self.page_dashboard.load_data)
        
        btn_products.clicked.connect(lambda: self.pages.setCurrentIndex(1))
        btn_invoices.clicked.connect(lambda: self.pages.setCurrentIndex(2))
        btn_debts.clicked.connect(lambda: self.pages.setCurrentIndex(3))
        btn_history.clicked.connect(lambda: self.pages.setCurrentIndex(4))
        btn_history.clicked.connect(self.page_history.load_invoices)
        
        btn_settings.clicked.connect(lambda: self.pages.setCurrentIndex(5))
        btn_settings.clicked.connect(self.page_settings.load_settings)

        main_layout.addWidget(sidebar)
        main_layout.addWidget(self.pages)

# ===== Run Application =====
if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Check License (Shows Activation Dialog if needed)
    if not check_license():
        sys.exit(0) # User cancelled activation

    # Apply Visual Identity (Softer Professional Dark Theme)
    app.setStyleSheet("""
        QWidget {
            color: #f0f0f0;
            font-family: 'Segoe UI', sans-serif;
            font-size: 14px;
        }
        
        /* Sidebar Buttons */
        QPushButton {
            background-color: transparent;
            color: #f0f0f0;
            border: none;
            text-align: right;
            padding: 10px 20px;
            font-size: 16px;
            border-radius: 5px;
        }
        QPushButton:hover {
            background-color: #3e3e42;
            color: #00BFFF;
        }
        QPushButton:checked {
            background-color: #3e3e42;
            color: #00BFFF;
            border-right: 3px solid #00BFFF;
        }
        
        /* Action Buttons (Green/Blue/Red in pages) */
        QPushButton[text="إضافة قطعة"], QPushButton[text="تعديل"], QPushButton[text="حذف"], 
        QPushButton[text="تحديث"], QPushButton[text="بيع وطباعة (F5)"], QPushButton[text="تسديد دين"],
        QPushButton[text="زبون جديد (+)"], QPushButton[text="طباعة / حفظ PDF"] {
            background-color: #0078d4; /* Standard Blue */
            color: white;
            text-align: center;
        }
        QPushButton[text="إضافة قطعة"]:hover, QPushButton[text="تعديل"]:hover {
            background-color: #106ebe;
        }
        
        /* Inputs */
        QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QDateEdit {
            background-color: #2d2d30; /* Input Dark */
            color: #f0f0f0;
            border: 1px solid #3e3e42;
            padding: 6px;
            border-radius: 4px;
        }
        QLineEdit:focus, QComboBox:focus {
            border: 1px solid #00BFFF;
            background-color: #252526;
        }
        
        /* Tables */
        QTableWidget {
            background-color: #252526;
            alternate-background-color: #2d2d30;
            color: #f0f0f0;
            gridline-color: #3e3e42;
            border: 1px solid #3e3e42;
            selection-background-color: #0078d4;
            selection-color: #ffffff;
        }
        QHeaderView::section {
            background-color: #2d2d30;
            color: #f0f0f0;
            padding: 8px;
            border: none;
            border-bottom: 2px solid #3e3e42;
            font-weight: bold;
        }
        
        /* Scrollbars */
        QScrollBar:vertical {
            background: #1e1e1e;
            width: 14px;
        }
        QScrollBar::handle:vertical {
            background: #424242;
            min-height: 20px;
            border-radius: 7px;
            margin: 2px;
        }
        QScrollBar::handle:vertical:hover {
            background: #686868;
        }
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
            height: 0px;
        }
    """)
    
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
