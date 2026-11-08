from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget, 
    QTableWidgetItem, QHeaderView, QDialog, QFormLayout, QLineEdit, 
    QDoubleSpinBox, QSpinBox, QMessageBox, QLabel, QAbstractItemView,
    QFileDialog
)
from PyQt5.QtCore import Qt
from database import get_db_connection

class ProductDialog(QDialog):
    def __init__(self, parent=None, product_data=None):
        super().__init__(parent)
        self.product_data = product_data
        self.setWindowTitle("إضافة قطعة جديدة" if not product_data else "تعديل قطعة")
        self.resize(400, 250)
        
        layout = QFormLayout(self)
        
        self.name_input = QLineEdit()
        # Code input removed
        self.qty_input = QSpinBox()
        self.qty_input.setRange(0, 10000)
        
        self.price_input = QDoubleSpinBox()
        self.price_input.setRange(0, 10000)
        self.price_input.setDecimals(2)
        self.price_input.setPrefix("$")
        
        self.sell_price_input = QDoubleSpinBox()
        self.sell_price_input.setRange(0, 10000)
        self.sell_price_input.setDecimals(2)
        self.sell_price_input.setPrefix("$")
        
        if product_data:
            self.name_input.setText(product_data['name'])
            # Code handling removed
            self.qty_input.setValue(product_data['quantity'])
            self.price_input.setValue(product_data['price_usd'])
            self.sell_price_input.setValue(product_data['sell_price'] if 'sell_price' in product_data.keys() else 0)
        
        layout.addRow("اسم القطعة:", self.name_input)
        # Code row removed
        layout.addRow("الكمية:", self.qty_input)
        layout.addRow("سعر الشراء (التكلفة):", self.price_input)
        layout.addRow("سعر المبيع:", self.sell_price_input)
        
        btn_box = QHBoxLayout()
        btn_save = QPushButton("حفظ")
        btn_save.clicked.connect(self.accept)
        btn_cancel = QPushButton("إلغاء")
        btn_cancel.clicked.connect(self.reject)
        
        btn_box.addWidget(btn_save)
        btn_box.addWidget(btn_cancel)
        layout.addRow(btn_box)

    def get_data(self):
        return {
            'name': self.name_input.text(),
            'code': None, # Always None
            'quantity': self.qty_input.value(),
            'price_usd': self.price_input.value(),
            'sell_price': self.sell_price_input.value()
        }

class ProductsPage(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout(self)
        
        # Header
        header_layout = QHBoxLayout()
        self.btn_add = QPushButton("إضافة قطعة")
        self.btn_add.clicked.connect(self.add_product)
        self.btn_edit = QPushButton("تعديل")
        self.btn_edit.clicked.connect(self.edit_selected_product)
        self.btn_delete = QPushButton("حذف")
        self.btn_delete.clicked.connect(self.delete_product)
        self.btn_refresh = QPushButton("تحديث")
        self.btn_refresh.clicked.connect(self.load_products)
        self.btn_import = QPushButton("استيراد Excel")
        self.btn_import.clicked.connect(self.import_excel)
        
        header_layout.addWidget(self.btn_add)
        header_layout.addWidget(self.btn_edit)
        header_layout.addWidget(self.btn_delete)
        header_layout.addWidget(self.btn_refresh)
        header_layout.addWidget(self.btn_import)
        header_layout.addStretch()
        self.layout.addLayout(header_layout)
        
        # Search Bar
        search_layout = QHBoxLayout()
        lbl_search = QLabel("بحث:")
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 ابحث عن مادة بالاسم...")
        self.search_input.textChanged.connect(self.filter_products)
        search_layout.addWidget(lbl_search)
        search_layout.addWidget(self.search_input)
        
        self.layout.addLayout(search_layout)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(5) # Decreased column count
        self.table.setHorizontalHeaderLabels(["ID", "الاسم", "الكمية", "التكلفة ($)", "المبيع ($)"]) # Removed "Code"
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSortingEnabled(True) 
        self.table.doubleClicked.connect(self.edit_selected_product)
        self.layout.addWidget(self.table)
        
        self.load_products()

    def filter_products(self):
        filter_text = self.search_input.text().lower()
        for row in range(self.table.rowCount()):
            name_item = self.table.item(row, 1)
            # code_item removed
            
            show_row = False
            if name_item and filter_text in name_item.text().lower():
                show_row = True
            # Code filter check removed
                
            self.table.setRowHidden(row, not show_row)

    def load_products(self):
        conn = None
        products = []
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM products")
            products = cursor.fetchall()
        finally:
            if conn: conn.close()
        
        self.table.setRowCount(0)
        self.table.setSortingEnabled(False)
        for row_idx, product in enumerate(products):
            self.table.insertRow(row_idx)
            self.table.setItem(row_idx, 0, QTableWidgetItem(str(product['id'])))
            self.table.setItem(row_idx, 1, QTableWidgetItem(product['name']))
            # Code column removed (was index 2)
            self.table.setItem(row_idx, 2, QTableWidgetItem(str(product['quantity'])))
            self.table.setItem(row_idx, 3, QTableWidgetItem(f"${product['price_usd']:.2f}"))
            
            sell_price = product['sell_price'] if 'sell_price' in product.keys() else 0
            self.table.setItem(row_idx, 4, QTableWidgetItem(f"${sell_price:.2f}"))
            
            if product['quantity'] < 5:
                for col in range(5):
                    self.table.item(row_idx, col).setBackground(Qt.red)
                    self.table.item(row_idx, col).setForeground(Qt.white)
        self.table.setSortingEnabled(True)

    def add_product(self):
        dialog = ProductDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            data = dialog.get_data()
            if not data['name']:
                QMessageBox.warning(self, "خطأ", "يجب إدخال اسم القطعة")
                return
            
            conn = None
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO products (name, code, quantity, price_usd, sell_price) VALUES (?, ?, ?, ?, ?)",
                    (data['name'], None, data['quantity'], data['price_usd'], data['sell_price'])
                )
                conn.commit()
                self.load_products()
                QMessageBox.information(self, "نجاح", "تمت إضافة القطعة بنجاح")
            except Exception as e:
                QMessageBox.critical(self, "خطأ", f"حدث خطأ أثناء الحفظ: {str(e)}")
            finally:
                if conn: conn.close()

    def edit_selected_product(self):
        selected_items = self.table.selectedItems()
        if not selected_items:
            if self.table.rowCount() > 0:
                 QMessageBox.warning(self, "تنبيه", "الرجاء تحديد قطعة للتعديل")
            return
            
        row = selected_items[0].row()
        product_id = int(self.table.item(row, 0).text())
        
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM products WHERE id = ?", (product_id,))
            product = cursor.fetchone()
        except:
            return
        finally:
            if conn: conn.close()
        
        if not product:
            return

        dialog = ProductDialog(self, product)
        if dialog.exec_() == QDialog.Accepted:
            data = dialog.get_data()
            if not data['name']:
                QMessageBox.warning(self, "خطأ", "يجب إدخال اسم القطعة")
                return
            
            conn = None
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute(
                    """UPDATE products 
                       SET name=?, code=?, quantity=?, price_usd=?, sell_price=? 
                       WHERE id=?""",
                    (data['name'], None, data['quantity'], data['price_usd'], data['sell_price'], product_id)
                )
                conn.commit()
                self.load_products()
                QMessageBox.information(self, "نجاح", "تم تعديل القطعة بنجاح")
            except Exception as e:
                QMessageBox.critical(self, "خطأ", f"حدث خطأ أثناء التعديل: {str(e)}")
            finally:
                if conn: conn.close()

    def delete_product(self):
        selected_rows = sorted(set(item.row() for item in self.table.selectedItems()), reverse=True)
        
        if not selected_rows:
            QMessageBox.warning(self, "تنبيه", "الرجاء تحديد قطعة (أو أكثر) للحذف")
            return
            
        count = len(selected_rows)
        msg_text = "هل أنت متأكد من حذف القطعة المحددة؟" if count == 1 else f"هل أنت متأكد من حذف {count} قطع محددة؟"
        
        reply = QMessageBox.question(
            self, "تأكيد الحذف", 
            msg_text,
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            conn = None
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                
                for row in selected_rows:
                    product_id = int(self.table.item(row, 0).text())
                    cursor.execute("DELETE FROM products WHERE id = ?", (product_id,))
                
                conn.commit()
                self.load_products()
                QMessageBox.information(self, "نجاح", "تم الحذف بنجاح")
            except Exception as e:
                QMessageBox.critical(self, "خطأ", f"حدث خطأ أثناء الحذف: {str(e)}")
            finally:
                if conn: conn.close()

    def import_excel(self):
        try:
            import pandas as pd
        except ImportError:
            QMessageBox.critical(self, "خطأ", "مكتبة pandas غير مثبتة.\nالرجاء تثبيتها باستخدام الأمر:\npip install pandas openpyxl")
            return

        file_path, _ = QFileDialog.getOpenFileName(self, "استيراد ملف إكسل", "", "Excel Files (*.xlsx *.xls)")
        if not file_path:
            return

        try:
            # Read Excel file
            df = pd.read_excel(file_path)
            
            # Standard columns expected
            required_columns = ['اسم المادة', 'سعر الشراء ($)']
            
            # Check if columns exist
            missing = [col for col in required_columns if col not in df.columns]
            if missing:
                QMessageBox.warning(self, "تنسيق غير مدعوم", 
                    f"الملف لا يحتوي على الأعمدة المطلوبة:\n{', '.join(missing)}\n\nيرجى استخدام القالب الموحد.")
                return
            
            conn = None
            conn = None
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                
                # Fetch Profit Margin
                cur_s = conn.execute("SELECT value FROM settings WHERE key='profit_margin'")
                res_s = cur_s.fetchone()
                margin_percent = float(res_s[0]) if res_s else 0
                multiplier = 1 + (margin_percent / 100.0)
                
                added_count = 0
                updated_count = 0
                error_count = 0
                
                for index, row in df.iterrows():
                    try:
                        name = str(row['اسم المادة']).strip()
                        if pd.isna(name) or not name: continue
                        
                        price_usd = float(row['سعر الشراء ($)']) if not pd.isna(row['سعر الشراء ($)']) else 0
                        
                        # Calculate Sell Price based on Margin
                        sell_price = price_usd * multiplier
                        
                        quantity = int(row.get('الكمية', 0)) if not pd.isna(row.get('الكمية', 0)) else 0
                        
                        # Check if exists by Name only
                        cursor.execute("SELECT id FROM products WHERE name = ?", (name,))
                        existing = cursor.fetchone()
                        
                        if existing:
                            cursor.execute("""
                                UPDATE products 
                                SET price_usd = ?, sell_price = ?, quantity = quantity + ?
                                WHERE id = ?
                            """, (price_usd, sell_price, quantity, existing['id']))
                            updated_count += 1
                        else:
                            cursor.execute("""
                                INSERT INTO products (name, code, quantity, price_usd, sell_price) 
                                VALUES (?, ?, ?, ?, ?)
                            """, (name, None, quantity, price_usd, sell_price))
                            added_count += 1
                            
                    except Exception as row_error:
                        print(f"Error processing row {index}: {row_error}")
                        error_count += 1
                        continue
                
                conn.commit()
            
            finally:
                if conn: conn.close()
            
            self.load_products()
            
            msg = f"تمت العملية بنجاح.\n\nتمت إضافة: {added_count}\nتم تحديث: {updated_count}"
            if error_count > 0:
                msg += f"\n\nفشل في: {error_count} صفوف"
            QMessageBox.information(self, "تقرير الاستيراد", msg)
            
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"حدث خطأ أثناء الاستيراد: {str(e)}")
