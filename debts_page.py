from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget, 
    QTableWidgetItem, QHeaderView, QDialog, QFormLayout, QDoubleSpinBox, 
    QMessageBox, QLabel, QInputDialog
)
from database import get_db_connection

class DebtsPage(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout(self)
        
        # Header
        header_layout = QHBoxLayout()
        self.btn_refresh = QPushButton("تحديث")
        self.btn_refresh.clicked.connect(self.load_debts)
        
        header_layout.addWidget(self.btn_refresh)
        header_layout.addStretch()
        self.layout.addLayout(header_layout)
        
        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["ID", "اسم الزبون", "رقم الهاتف", "الدين المتبقي (ل.س)"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.layout.addWidget(self.table)
        
        # Pay Button
        self.btn_pay = QPushButton("تسديد دين")
        self.btn_pay.setStyleSheet("background-color: #27ae60; color: white; padding: 10px; font-weight: bold; font-size: 14px;")
        self.btn_pay.clicked.connect(self.pay_debt)
        self.layout.addWidget(self.btn_pay)
        
        self.load_debts()

    def load_debts(self):
        conn = get_db_connection()
        customers = conn.execute("SELECT * FROM customers WHERE total_debt > 0").fetchall()
        conn.close()
        
        self.table.setRowCount(0)
        for row, c in enumerate(customers):
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(str(c['id'])))
            self.table.setItem(row, 1, QTableWidgetItem(c['name']))
            self.table.setItem(row, 2, QTableWidgetItem(c['phone'] or ""))
            self.table.setItem(row, 3, QTableWidgetItem(f"{c['total_debt']:,.0f}"))

    def pay_debt(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "تنبيه", "الرجاء اختيار زبون من الجدول")
            return
            
        customer_id = int(self.table.item(row, 0).text())
        customer_name = self.table.item(row, 1).text()
        current_debt = float(self.table.item(row, 3).text().replace(',', ''))
        
        amount, ok = QInputDialog.getDouble(self, "تسديد دين", 
                                          f"الزبون: {customer_name}\nالدين الحالي: {current_debt:,.0f}\n\nالمبلغ المدفوع:", 
                                          0, 0, current_debt, 0)
        if ok and amount > 0:
            conn = get_db_connection()
            try:
                # Update debt
                new_debt = current_debt - amount
                conn.execute("UPDATE customers SET total_debt = ? WHERE id = ?", (new_debt, customer_id))
                conn.commit()
                
                QMessageBox.information(self, "نجاح", f"تم تسديد {amount:,.0f} ل.س بنجاح.\nالباقي: {new_debt:,.0f} ل.س")
                self.load_debts()
            except Exception as e:
                conn.rollback()
                QMessageBox.critical(self, "خطأ", str(e))
            finally:
                conn.close()
