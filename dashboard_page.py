from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QTableWidget, 
    QTableWidgetItem, QHeaderView, QPushButton, QGridLayout
)
from PyQt5.QtCore import Qt, QTimer, QDate
from database import get_db_connection

class DashboardPage(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(20, 20, 20, 20)
        
        # Header
        header_layout = QHBoxLayout()
        title = QLabel("لوحة التحكم")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #007bff;")
        header_layout.addWidget(title)
        
        btn_refresh = QPushButton("🔄 تحديث")
        btn_refresh.clicked.connect(self.load_data)
        header_layout.addWidget(btn_refresh)
        header_layout.addStretch()
        
        self.layout.addLayout(header_layout)
        self.layout.addSpacing(20)
        
        # Stats Cards
        self.stats_layout = QGridLayout()
        self.layout.addLayout(self.stats_layout)
        
        # Low Stock Alert
        self.layout.addSpacing(30)
        lbl_alert = QLabel("⚠️ تنبيهات المخزون المنخفض (أقل من 5 قطع)")
        lbl_alert.setStyleSheet("font-size: 18px; font-weight: bold; color: #e74c3c;")
        self.layout.addWidget(lbl_alert)
        
        self.alert_table = QTableWidget()
        self.alert_table.setColumnCount(3)
        self.alert_table.setHorizontalHeaderLabels(["المادة", "الكود", "الكمية المتبقية"])
        self.alert_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.layout.addWidget(self.alert_table)
        
        self.load_data()

    def create_card(self, title, value, color):
        card = QFrame()
        card.setMinimumHeight(120)
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {color};
                border-radius: 10px;
                padding: 15px;
            }}
        """)
        layout = QVBoxLayout(card)
        
        lbl_title = QLabel(title)
        lbl_title.setStyleSheet("color: white; font-size: 16px; font-weight: bold; background-color: transparent;")
        
        lbl_value = QLabel(value)
        lbl_value.setStyleSheet("color: white; font-size: 28px; font-weight: bold; background-color: transparent;")
        
        layout.addWidget(lbl_title)
        layout.addWidget(lbl_value)
        layout.addStretch()
        return card

    def load_data(self):
        conn = get_db_connection()
        
        # 1. Daily Sales - Filter by Local Date in Python
        today_str = QDate.currentDate().toString("yyyy-MM-dd")
        
        rows = conn.execute("SELECT total_amount_syp, date FROM invoices").fetchall()
        
        count_today = 0
        total_sales_today = 0
        
        for row in rows:
            if row['date'] and row['date'].startswith(today_str):
                count_today += 1
                total_sales_today += row['total_amount_syp']
        
        # 2. Total Debts
        debts = conn.execute("SELECT SUM(total_debt) FROM customers").fetchone()[0] or 0
        
        # 3. Low Stock
        low_stock = conn.execute("SELECT name, code, quantity FROM products WHERE quantity < 5").fetchall()
        
        conn.close()
        
        # Update UI
        # Clear old cards
        for i in reversed(range(self.stats_layout.count())): 
            self.stats_layout.itemAt(i).widget().setParent(None)
            
        self.stats_layout.addWidget(self.create_card("مبيعات اليوم", f"{total_sales_today:,.0f} ل.س", "#27ae60"), 0, 0)
        self.stats_layout.addWidget(self.create_card("فواتير اليوم", str(count_today), "#2980b9"), 0, 1)
        self.stats_layout.addWidget(self.create_card("الديون المستحقة", f"{debts:,.0f} ل.س", "#c0392b"), 0, 2)
        
        # Update Table
        self.alert_table.setRowCount(0)
        for row, item in enumerate(low_stock):
            self.alert_table.insertRow(row)
            self.alert_table.setItem(row, 0, QTableWidgetItem(item['name']))
            self.alert_table.setItem(row, 1, QTableWidgetItem(item['code'] or ""))
            self.alert_table.setItem(row, 2, QTableWidgetItem(str(item['quantity'])))
