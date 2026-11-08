from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget, 
    QTableWidgetItem, QHeaderView, QDialog, QFormLayout, QLabel, 
    QAbstractItemView, QMessageBox
)
from PyQt5.QtCore import Qt
from database import get_db_connection

class InvoiceHistoryPage(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout(self)
        
        # Header
        header_layout = QHBoxLayout()
        self.btn_refresh = QPushButton("تحديث")
        self.btn_refresh.clicked.connect(self.load_invoices)
        
        self.btn_revert = QPushButton("استرجاع (حذف + مخزون)")
        self.btn_revert.setStyleSheet("background-color: #e67e22; color: white; font-weight: bold;")
        self.btn_revert.clicked.connect(self.revert_invoice)

        self.btn_archive = QPushButton("أرشفة (حذف من السجل فقط)")
        self.btn_archive.setStyleSheet("background-color: #c0392b; color: white; font-weight: bold;")
        self.btn_archive.clicked.connect(self.archive_invoice)
        
        header_layout.addWidget(self.btn_refresh)
        header_layout.addWidget(self.btn_revert)
        header_layout.addWidget(self.btn_archive)
        header_layout.addStretch()
        self.layout.addLayout(header_layout)
        
        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["ID", "التاريخ", "الزبون", "الإجمالي (ل.س)", "المدفوع", "المتبقي"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.doubleClicked.connect(self.show_details)
        self.layout.addWidget(self.table)
        
        self.load_invoices()

    def load_invoices(self):
        conn = get_db_connection()
        query = """
            SELECT i.id, i.date, c.name as customer_name, i.total_amount_syp, i.paid_amount
            FROM invoices i
            LEFT JOIN customers c ON i.customer_id = c.id
            ORDER BY i.date DESC
        """
        invoices = conn.execute(query).fetchall()
        conn.close()
        
        self.table.setRowCount(0)
        for row, inv in enumerate(invoices):
            self.table.insertRow(row)
            remaining = inv['total_amount_syp'] - inv['paid_amount']
            
            self.table.setItem(row, 0, QTableWidgetItem(str(inv['id'])))
            self.table.setItem(row, 1, QTableWidgetItem(str(inv['date'])))
            self.table.setItem(row, 2, QTableWidgetItem(inv['customer_name'] or "زبون عام"))
            self.table.setItem(row, 3, QTableWidgetItem(f"{inv['total_amount_syp']:,.0f}"))
            self.table.setItem(row, 4, QTableWidgetItem(f"{inv['paid_amount']:,.0f}"))
            self.table.setItem(row, 5, QTableWidgetItem(f"{remaining:,.0f}"))

    def show_details(self):
        selected_items = self.table.selectedItems()
        if not selected_items: return
        
        row = selected_items[0].row()
        invoice_id = int(self.table.item(row, 0).text())
        
        # Fetch details
        conn = get_db_connection()
        items = conn.execute("""
            SELECT p.name, ii.quantity, ii.unit_price_syp
            FROM invoice_items ii
            JOIN products p ON ii.product_id = p.id
            WHERE ii.invoice_id = ?
        """, (invoice_id,)).fetchall()
        conn.close()
        
        # Show Dialog
        dialog = QDialog(self)
        dialog.setWindowTitle(f"تفاصيل الفاتورة #{invoice_id}")
        dialog.resize(500, 400)
        layout = QVBoxLayout(dialog)
        
        table = QTableWidget()
        table.setColumnCount(4)
        table.setHorizontalHeaderLabels(["المادة", "الكمية", "الإفرادي (ل.س)", "الإجمالي"])
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
        table.setRowCount(0)
        total = 0
        for r, item in enumerate(items):
            table.insertRow(r)
            line_total = item['quantity'] * item['unit_price_syp']
            total += line_total
            
            table.setItem(r, 0, QTableWidgetItem(item['name']))
            table.setItem(r, 1, QTableWidgetItem(str(item['quantity'])))
            table.setItem(r, 2, QTableWidgetItem(f"{item['unit_price_syp']:,.0f}"))
            table.setItem(r, 3, QTableWidgetItem(f"{line_total:,.0f}"))
            
        layout.addWidget(table)
        
        lbl_total = QLabel(f"المجموع الكلي: {total:,.0f} ل.س")
        lbl_total.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(lbl_total)
        
        dialog.exec_()

    def revert_invoice(self):
        selected_items = self.table.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "تنبيه", "يرجى تحديد فاتورة للاسترجاع.")
            return
            
        row = selected_items[0].row()
        invoice_id = int(self.table.item(row, 0).text())
        
        confirm = QMessageBox.question(
            self, "تأكيد الاسترجاع", 
            "هل أنت متأكد من استرجاع الفاتورة؟\nسيتم إعادة الكميات للمخزون وإلغاء الدين (إن وجد).",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if confirm != QMessageBox.Yes:
            return

        conn = get_db_connection()
        try:
            # 1. Restore Stock
            items = conn.execute("SELECT product_id, quantity FROM invoice_items WHERE invoice_id = ?", (invoice_id,)).fetchall()
            for item in items:
                conn.execute("UPDATE products SET quantity = quantity + ? WHERE id = ?", (item['quantity'], item['product_id']))
                
            # 2. Revert Customer Debt (if any)
            invoice = conn.execute("SELECT customer_id, total_amount_syp, paid_amount FROM invoices WHERE id = ?", (invoice_id,)).fetchone()
            if invoice:
                remaining = invoice['total_amount_syp'] - invoice['paid_amount']
                if remaining > 0 and invoice['customer_id']:
                    conn.execute("UPDATE customers SET total_debt = total_debt - ? WHERE id = ?", (remaining, invoice['customer_id']))

            # 3. Delete Record
            conn.execute("DELETE FROM invoice_items WHERE invoice_id = ?", (invoice_id,))
            conn.execute("DELETE FROM invoices WHERE id = ?", (invoice_id,))
            
            conn.commit()
            QMessageBox.information(self, "نجاح", "تم استرجاع الفاتورة للمخزون بنجاح.")
            self.load_invoices()
            
        except Exception as e:
            conn.rollback()
            QMessageBox.critical(self, "خطأ", f"حدث خطأ أثناء الاسترجاع: {e}")
        finally:
            conn.close()

    def archive_invoice(self):
        selected_items = self.table.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "تنبيه", "يرجى تحديد فاتورة للأرشفة.")
            return
            
        row = selected_items[0].row()
        invoice_id = int(self.table.item(row, 0).text())
        
        confirm = QMessageBox.question(
            self, "تأكيد الأرشفة (الحذف)", 
            "هل أنت متأكد من حذف الفاتورة من السجل؟\n\nتنبيه: لن يتم استرجاع الكميات للمخزون ولن يتم تعديل ديون الزبون.\nاستخدم هذا الخيار فقط لتنظيف السجل.",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if confirm != QMessageBox.Yes:
            return

        conn = get_db_connection()
        try:
            # Just Delete Record
            conn.execute("DELETE FROM invoice_items WHERE invoice_id = ?", (invoice_id,))
            conn.execute("DELETE FROM invoices WHERE id = ?", (invoice_id,))
            
            conn.commit()
            QMessageBox.information(self, "نجاح", "تم حذف الفاتورة من السجل بنجاح.")
            self.load_invoices()
            
        except Exception as e:
            conn.rollback()
            QMessageBox.critical(self, "خطأ", f"حدث خطأ أثناء الأرشفة: {e}")
        finally:
            conn.close()
