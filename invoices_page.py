# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget,
    QTableWidgetItem, QHeaderView, QDialog, QFormLayout, QLineEdit,
    QDoubleSpinBox, QSpinBox, QMessageBox, QLabel, QComboBox, QFrame,
    QSplitter, QGroupBox, QInputDialog
)
from PyQt5.QtCore import Qt, QTimer, QDateTime, QDate
from database import get_db_connection

class InvoicesPage(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)

        # ---------- أعلى الشاشة: الزبون ----------
        top_frame = QFrame()
        top_frame.setStyleSheet("background-color: #f8f9fa; border-radius: 8px; padding: 5px; border: 1px solid #ced4da;")
        top_layout = QHBoxLayout(top_frame)

        # اختيار الزبون
        self.customer_combo = QComboBox()
        self.customer_combo.setFixedHeight(35)
        self.customer_combo.setStyleSheet("font-size: 14px; background-color: #ffffff; color: #333333; border: 1px solid #ced4da;")
        self.refresh_customers()

        btn_new_customer = QPushButton("زبون جديد (+)")
        btn_new_customer.setFixedHeight(35)
        btn_new_customer.setStyleSheet("background-color: #0078d4; color: white; font-weight: bold; border-radius: 5px; padding: 5px;")
        btn_new_customer.clicked.connect(self.add_customer_dialog)
        
        top_layout.addWidget(QLabel("الزبون:"))
        top_layout.addWidget(self.customer_combo, 1)
        top_layout.addWidget(btn_new_customer)
        top_frame.setFixedHeight(70)
        self.layout.addWidget(top_frame)

        # ---------- التقسيم: قائمة المواد | سلة البيع ----------
        splitter = QSplitter(Qt.Horizontal)

        # ---- يسار: قائمة المواد ----
        products_widget = QWidget()
        products_layout = QVBoxLayout(products_widget)
        products_layout.setContentsMargins(0, 0, 5, 0)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 ابحث عن مادة...")
        self.search_input.textChanged.connect(self.filter_products)

        self.products_table = QTableWidget()
        self.products_table.setColumnCount(4)
        self.products_table.setHorizontalHeaderLabels(["ID", "المادة", "سعر المبيع ($)", "المخزون"])
        self.products_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.products_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.products_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.products_table.doubleClicked.connect(self.add_selected_product)

        products_layout.addWidget(self.search_input)
        products_layout.addWidget(self.products_table)

        products_group = QGroupBox("1. قائمة المواد (اضغط مرتين للإضافة)")
        products_group.setLayout(products_layout)
        splitter.addWidget(products_group)

        # ---- يمين: سلة البيع ----
        cart_widget = QWidget()
        cart_layout = QVBoxLayout(cart_widget)
        cart_layout.setContentsMargins(5, 0, 0, 0)

        self.cart_table = QTableWidget()
        self.cart_table.setColumnCount(6)
        self.cart_table.setHorizontalHeaderLabels(["م", "المادة", "السعر", "العدد", "الإجمالي", "حذف"])
        self.cart_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)

        cart_layout.addWidget(self.cart_table)

        # إجمالي الفاتورة
        totals_frame = QFrame()
        totals_frame.setStyleSheet("background-color: #f8f9fa; border: 1px solid #ced4da; border-radius: 5px; padding: 10px;")
        totals_layout = QVBoxLayout(totals_frame)
        self.lbl_total_usd = QLabel("المجموع: $0.00")
        self.lbl_total_syp = QLabel("0")
        totals_layout.addWidget(self.lbl_total_usd)
        totals_layout.addWidget(self.lbl_total_syp)
        cart_layout.addWidget(totals_frame)

        # أزرار
        btn_layout = QHBoxLayout()
        btn_checkout = QPushButton("بيع وطباعة (F5)")
        btn_checkout.setShortcut("F5")
        btn_checkout.setMinimumHeight(50)
        btn_checkout.setStyleSheet("background-color: #27ae60; color: white; font-size: 18px; font-weight: bold; border-radius: 5px;")
        btn_checkout.clicked.connect(self.checkout)
        
        # زر التحديث الفوري
        btn_refresh_data = QPushButton("🔄 تحديث الأسعار والكميات")
        btn_refresh_data.setMinimumHeight(45)
        btn_refresh_data.setStyleSheet("background-color: #17a2b8; color: white; font-size: 14px; border-radius: 5px;")
        btn_refresh_data.clicked.connect(self.refresh_product_data)
        
        btn_clear = QPushButton("تفريغ")
        btn_clear.setMinimumHeight(50)
        btn_clear.setStyleSheet("background-color: #e74c3c; color: white; font-size: 14px; border-radius: 5px;")
        btn_clear.clicked.connect(self.clear_cart)

        btn_report = QPushButton("تقرير اليومية")
        btn_report.setMinimumHeight(50)
        btn_report.setStyleSheet("background-color: #8e44ad; color: white; font-size: 14px; border-radius: 5px;")
        btn_report.clicked.connect(self.print_daily_report)
        
        btn_layout.addWidget(btn_refresh_data)
        btn_layout.addWidget(btn_clear)
        btn_layout.addWidget(btn_report)
        btn_layout.addWidget(btn_checkout, 2)
        cart_layout.addLayout(btn_layout)

        cart_group = QGroupBox("2. سلة البيع")
        cart_group.setLayout(cart_layout)
        splitter.addWidget(cart_group)

        splitter.setStretchFactor(0, 4)
        splitter.setStretchFactor(1, 5)
        self.layout.addWidget(splitter, 1)

        # متغيرات
        self.cart_items = []
        self.all_products = []
        self.exchange_rate = 15000
        self.load_exchange_rate()
        self.refresh_products()
        # تحديث فوري لما تفتح الصفحة
        self.refresh_product_data()

    def load_exchange_rate(self):
        try:
            conn = get_db_connection()
            res = conn.execute("SELECT value FROM settings WHERE key='exchange_rate'").fetchone()
            if res:
                self.exchange_rate = float(res[0])
            conn.close()
        except:
            pass

    # ----------- دوال بسيطة -----------
    def refresh_customers(self):
        self.customer_combo.clear()
        with get_db_connection() as conn:
            for c in conn.execute("SELECT * FROM customers").fetchall():
                self.customer_combo.addItem(c['name'], c['id'])

    def refresh_products(self):
        with get_db_connection() as conn:
            self.all_products = conn.execute("SELECT id, name, quantity, price_usd, sell_price FROM products").fetchall()
        self.filter_products()

    def filter_products(self):
        txt = self.search_input.text().lower()
        filtered = [p for p in self.all_products if txt in p['name'].lower()]
        self.products_table.setRowCount(0)
        for row, p in enumerate(filtered):
            self.products_table.insertRow(row)
            self.products_table.setItem(row, 0, QTableWidgetItem(str(p['id'])))
            self.products_table.setItem(row, 1, QTableWidgetItem(p['name']))
            s_price = p['sell_price'] if p['sell_price'] is not None else 0
            self.products_table.setItem(row, 2, QTableWidgetItem(f"${s_price:,.2f}"))
            self.products_table.setItem(row, 3, QTableWidgetItem(str(p['quantity'])))

    def add_selected_product(self):
        row = self.products_table.currentRow()
        if row < 0: return
        pid = int(self.products_table.item(row, 0).text())
        product = next((p for p in self.all_products if p['id'] == pid), None)
        if product: self.add_to_cart(product)

    def add_to_cart(self, product):
        if product['quantity'] <= 0:
            QMessageBox.warning(self, "تنبيه", "المادة نافذة من المخزون!")
            return
        rate = self.exchange_rate
        unit_usd = product['sell_price'] if product['sell_price'] is not None else 0
        unit_syp = unit_usd * rate
        
        for item in self.cart_items:
            if item['product_id'] == product['id']:
                if item['quantity'] + 1 > product['quantity']:
                    QMessageBox.warning(self, "تنبيه", f"المتاح: {product['quantity']}")
                    return
                item['quantity'] += 1
                item['price_syp'] = unit_syp
                self.update_cart_totals()
                return
        
        self.cart_items.append({
            'product_id': product['id'],
            'name': product['name'],
            'quantity': 1,
            'price_syp': unit_syp,
            'max_quantity': product['quantity']
        })
        self.update_cart_totals()

    def refresh_product_data(self):
        """تقرأ أحدث الكميات وتعيد حساب الأسعار بناءً على سعر الصرف الجديد"""
        self.load_exchange_rate()
        with get_db_connection() as conn:
            self.all_products = conn.execute("SELECT id, name, quantity, price_usd, sell_price FROM products").fetchall()
            for item in self.cart_items:
                row = conn.execute("SELECT sell_price, quantity FROM products WHERE id = ?", (item['product_id'],)).fetchone()
                if row:
                    unit_usd = row['sell_price'] or 0
                    item['price_syp'] = int(unit_usd * self.exchange_rate)
                    item['max_quantity'] = row['quantity'] or 0
        self.filter_products()
        self.update_cart_totals()

    def update_cart_totals(self):
        rate = self.exchange_rate
        self.cart_table.setRowCount(0)
        total_usd = 0
        total_syp = 0
        
        for row, item in enumerate(self.cart_items):
            p_syp = int(item['price_syp'])
            qty = item['quantity']
            
            syp_total = p_syp * qty
            usd_total = syp_total / rate if rate > 0 else 0
            
            total_syp += syp_total
            total_usd += usd_total

            self.cart_table.insertRow(row)
            self.cart_table.setItem(row, 0, QTableWidgetItem(str(row + 1)))
            self.cart_table.setItem(row, 1, QTableWidgetItem(item['name']))

            # حقل السعر (قابل للتعديل)
            price_edit = QLineEdit()
            price_edit.setAlignment(Qt.AlignCenter)
            price_edit.setText(f"{p_syp:,}")
            price_edit.setStyleSheet("background-color: #ffffff; color: #333333; border: 1px solid #ced4da; font-size: 14px;")
            # عند الانتهاء من التعديل، نعيد الحساب فقط (بدون إعادة بناء الجدول)
            price_edit.editingFinished.connect(self.recalc_totals_only)
            self.cart_table.setCellWidget(row, 2, price_edit)

            # حقل العدد
            qty_spin = QSpinBox()
            qty_spin.setRange(1, max(1, item['max_quantity']))
            qty_spin.setValue(qty)
            # عند تغيير العدد، نعيد الحساب أيضاً
            qty_spin.valueChanged.connect(self.recalc_totals_only)
            self.cart_table.setCellWidget(row, 3, qty_spin)

            # عمود الإجمالي
            self.cart_table.setItem(row, 4, QTableWidgetItem(f"{syp_total:,.0f}"))

            # زر الحذف
            btn_del = QPushButton("❌")
            btn_del.setStyleSheet("color: red; border: none; font-weight: bold;")
            btn_del.clicked.connect(lambda _, r=row: self.remove_item(r))
            self.cart_table.setCellWidget(row, 5, btn_del)

        self.lbl_total_usd.setText(f"المجموع: ${total_usd:,.2f}")
        self.lbl_total_syp.setText(f"{total_syp:,.0f}")

    def recalc_totals_only(self):
        """يحسب المجاميع بناءً على القيم الموجودة حالياً في الواجهة (لضمان التطابق التام)"""
        rate = self.exchange_rate
        total_syp = 0
        total_usd = 0
        
        rows = self.cart_table.rowCount()
        for row in range(rows):
            if row >= len(self.cart_items): break
            
            # 1. قراءة السعر من الواجهة
            price_widget = self.cart_table.cellWidget(row, 2)
            if price_widget and isinstance(price_widget, QLineEdit):
                txt = price_widget.text().replace(',', '')
                try:
                    price_val = int(txt)
                except:
                    price_val = 0
            else:
                price_val = self.cart_items[row]['price_syp']
            
            # 2. قراءة العدد من الواجهة
            qty_widget = self.cart_table.cellWidget(row, 3)
            if qty_widget and isinstance(qty_widget, QSpinBox):
                qty_val = qty_widget.value()
            else:
                qty_val = self.cart_items[row]['quantity']
            
            # 3. تحديث البيانات الداخلية
            self.cart_items[row]['price_syp'] = price_val
            self.cart_items[row]['quantity'] = qty_val
            
            # 4. الحساب وتحديث عمود الإجمالي
            row_total = price_val * qty_val
            row_usd = row_total / rate if rate > 0 else 0
            
            total_syp += row_total
            total_usd += row_usd
            
            self.cart_table.setItem(row, 4, QTableWidgetItem(f"{row_total:,.0f}"))
            
        self.lbl_total_usd.setText(f"المجموع: ${total_usd:,.2f}")
        self.lbl_total_syp.setText(f"{total_syp:,.0f}")

    def update_row_quantity(self, row, value):
        if value > self.cart_items[row]['max_quantity']:
            value = self.cart_items[row]['max_quantity']
        self.cart_items[row]['quantity'] = value
        self.update_cart_totals()

    def remove_item(self, row):
        self.cart_items.pop(row)
        self.update_cart_totals()

    def clear_cart(self):
        self.cart_items.clear()
        self.update_cart_totals()

    def add_customer_dialog(self):
        name, ok = QInputDialog.getText(self, "زبون جديد", "اسم الزبون:")
        if ok and name:
            with get_db_connection() as conn:
                conn.execute("INSERT INTO customers (name) VALUES (?)", (name,))
            self.refresh_customers()
            idx = self.customer_combo.findText(name)
            if idx >= 0: self.customer_combo.setCurrentIndex(idx)

    # ----------- باقي الدوال (checkout – print – إلخ) -----------
    def checkout(self):
        if not self.cart_items:
            QMessageBox.warning(self, "تنبيه", "السلة فارغة!")
            return
        rate = self.exchange_rate
        subtotal_syp = sum(item['quantity'] * item['price_syp'] for item in self.cart_items)

        dialog = QDialog(self)
        dialog.setWindowTitle("تأكيد الدفع والحسم")
        dialog.resize(400, 350)
        layout = QVBoxLayout(dialog)

        layout.addWidget(QLabel(f"الزبون: {self.customer_combo.currentText()}"))
        layout.addWidget(QLabel(f"المجموع الفرعي: {subtotal_syp:,.0f}"))

        discount_input = QDoubleSpinBox()
        discount_input.setRange(0, subtotal_syp)
        discount_input.setValue(0)
        discount_input.setPrefix("قيمة الحسم: ")
        discount_input.setStyleSheet("font-size: 16px; color: #e74c3c; font-weight: bold;")
        layout.addWidget(discount_input)

        lbl_final_total = QLabel(f"الصافي للدفع: {subtotal_syp:,.0f}")
        lbl_final_total.setStyleSheet("font-size: 18px; font-weight: bold; color: #00BFFF; margin: 10px 0;")
        layout.addWidget(lbl_final_total)

        paid_input = QDoubleSpinBox()
        paid_input.setRange(0, subtotal_syp * 2)
        paid_input.setValue(subtotal_syp)
        paid_input.setPrefix("المدفوع: ")
        paid_input.setStyleSheet("font-size: 18px; padding: 5px; font-weight: bold;")
        layout.addWidget(paid_input)

        lbl_remaining = QLabel("المتبقي (دين): 0")
        lbl_remaining.setStyleSheet("font-size: 16px; color: #c0392b; font-weight: bold;")
        layout.addWidget(lbl_remaining)

        def update_calculations():
            discount = discount_input.value()
            final_total = subtotal_syp - discount
            lbl_final_total.setText(f"الصافي للدفع: {final_total:,.0f}")
            paid = paid_input.value()
            rem = final_total - paid
            if rem > 0.1:
                lbl_remaining.setText(f"المتبقي (دين): {rem:,.0f}")
                lbl_remaining.setStyleSheet("color: #c0392b;")
            elif rem < -0.1:
                lbl_remaining.setText(f"المتبقي (زيادة): {abs(rem):,.0f}")
                lbl_remaining.setStyleSheet("color: green;")
            else:
                lbl_remaining.setText("المتبقي: 0")
                lbl_remaining.setStyleSheet("color: green;")

        discount_input.valueChanged.connect(update_calculations)
        paid_input.valueChanged.connect(update_calculations)

        btn_ok = QPushButton("تأكيد وطباعة")
        btn_ok.setStyleSheet("background-color: #27ae60; color: white; font-size: 16px; padding: 10px;")
        btn_ok.clicked.connect(dialog.accept)
        layout.addWidget(btn_ok)

        if dialog.exec_() == QDialog.Accepted:
            discount = discount_input.value()
            final_total = subtotal_syp - discount
            paid = paid_input.value()
            remaining = final_total - paid
            customer_id = self.customer_combo.currentData() or self.customer_combo.itemData(0)
            if not customer_id:
                QMessageBox.warning(self, "خطأ", "يجب اختيار زبون")
                return

            with get_db_connection() as conn:
                current_time = QDateTime.currentDateTime().toString("yyyy-MM-dd HH:mm:ss")
                cur = conn.execute(
                    "INSERT INTO invoices (customer_id, total_amount_syp, exchange_rate, paid_amount, discount_amount, date) VALUES (?, ?, ?, ?, ?, ?)",
                    (customer_id, final_total, rate, paid, discount, current_time)
                )
                invoice_id = cur.lastrowid
                for item in self.cart_items:
                    conn.execute(
                        "INSERT INTO invoice_items (invoice_id, product_id, quantity, unit_price_syp) VALUES (?, ?, ?, ?)",
                        (invoice_id, item['product_id'], item['quantity'], item['price_syp'])
                    )
                    conn.execute(
                        "UPDATE products SET quantity = quantity - ? WHERE id = ?",
                        (item['quantity'], item['product_id'])
                    )
                if remaining > 0:
                    conn.execute(
                        "UPDATE customers SET total_debt = total_debt + ? WHERE id = ?",
                        (remaining, customer_id)
                    )
                self.print_invoice(invoice_id, customer_id, paid, remaining, subtotal_syp, discount, final_total, rate)
                self.clear_cart()
                self.refresh_products()

    # ----------- دوال الطباعة -----------
    def print_invoice(self, invoice_id, customer_id, paid, remaining, subtotal, discount, final_total, rate):
        try:
            from PyQt5.QtPrintSupport import QPrinter, QPrintPreviewDialog
            from PyQt5.QtGui import QTextDocument
        except ImportError:
            QMessageBox.warning(self, "تنبيه", "مكتبة الطباعة غير متوفرة.")
            return

        customer_name = self.customer_combo.currentText()
        html = f"""
        <div style="direction: rtl; font-family: Arial, sans-serif; width: 100%;">
            <div style="text-align: center; margin-bottom: 20px;">
                <h1 style="font-size: 36pt; font-weight: bold; margin: 0;">فاتورة مبيعات</h1>
                <p style="font-size: 16pt; margin: 5px 0;">رقم الفاتورة: {invoice_id}</p>
                <p style="font-size: 16pt; margin: 5px 0;">التاريخ: {QDate.currentDate().toString("yyyy-MM-dd")}</p>
            </div>
            <div style="margin-bottom: 20px; border-bottom: 2px solid #000; padding-bottom: 10px;">
                <p style="font-size: 18pt; font-weight: bold;">الزبون: {customer_name}</p>
            </div>
            <table width="100%" border="1" cellspacing="0" cellpadding="8" style="border-collapse: collapse; font-size: 14pt; text-align: center;">
                <thead>
                    <tr style="background-color: #f0f0f0;">
                        <th width="40%">المادة</th>
                        <th width="15%">العدد</th>
                        <th width="20%">السعر</th>
                        <th width="25%">الإجمالي</th>
                    </tr>
                </thead>
                <tbody>
        """
        for item in self.cart_items:
            unit_syp = item['price_syp']
            total_item_syp = unit_syp * item['quantity']
            html += f"""
                <tr>
                    <td>{item['name']}</td>
                    <td>{item['quantity']}</td>
                    <td>{unit_syp:,.0f}</td>
                    <td>{total_item_syp:,.0f}</td>
                </tr>
            """
        html += f"""
                </tbody>
            </table>
            <div style="margin-top: 30px; text-align: left; padding-top: 10px; border-top: 2px solid #000;">
                <p style="font-size: 16pt; margin: 5px 0;">المجموع الفرعي: {subtotal:,.0f}</p>
                <p style="font-size: 16pt; color: red; margin: 5px 0;">قيمة الحسم: {discount:,.0f}</p>
                <p style="font-size: 22pt; font-weight: bold; margin: 10px 0;">الصافي للدفع: {final_total:,.0f}</p>
                <p style="font-size: 16pt; margin: 5px 0;">المدفوع: {paid:,.0f}</p>
                <p style="font-size: 16pt; margin: 5px 0;">المتبقي: {remaining:,.0f}</p>
            </div>
            <div style="margin-top: 50px; text-align: center; font-size: 12pt; color: #555;">
                <p>شكراً لزيارتكم</p>
            </div>
        </div>
        """
        doc = QTextDocument()
        doc.setHtml(html)
        printer = QPrinter(QPrinter.HighResolution)
        printer.setPageSize(QPrinter.A4)
        preview = QPrintPreviewDialog(printer, self)
        preview.paintRequested.connect(lambda p: doc.print_(p))
        preview.exec_()

    def print_daily_report(self):
        try:
            from PyQt5.QtPrintSupport import QPrinter, QPrintPreviewDialog
            from PyQt5.QtGui import QTextDocument
        except ImportError:
            QMessageBox.warning(self, "تنبيه", "مكتبة الطباعة غير متوفرة.")
            return

        with get_db_connection() as conn:
            res = conn.execute("SELECT id FROM customers WHERE name = 'مبيعات نقدية يومية'").fetchone()
            if not res:
                QMessageBox.warning(self, "تنبيه", "لم يتم العثور على زبون 'مبيعات نقدية يومية'")
                return
            cust_id = res['id']
            today_str = QDate.currentDate().toString("yyyy-MM-dd")
            rows = conn.execute("SELECT id, total_amount_syp, date FROM invoices WHERE customer_id = ?", (cust_id,)).fetchall()
            todays_ids = []
            total_cash = 0
            for r in rows:
                if r['date'] and r['date'].startswith(today_str):
                    todays_ids.append(r['id'])
                    total_cash += r['total_amount_syp']
            if not todays_ids:
                QMessageBox.information(self, "تقرير", f"لا توجد مبيعات نقدية بتاريخ {today_str}.")
                return
            placeholders = ','.join('?' * len(todays_ids))
            items = conn.execute(f"""
                SELECT p.name, SUM(ii.quantity) as qty, SUM(ii.quantity * ii.unit_price_syp) as total_price
                FROM invoice_items ii
                JOIN products p ON ii.product_id = p.id
                WHERE ii.invoice_id IN ({placeholders})
                GROUP BY p.name
            """, todays_ids).fetchall()
            html = f"""
            <div style="direction: rtl; font-family: Arial, sans-serif; width: 100%;">
                <div style="text-align: center; margin-bottom: 20px;">
                    <h1 style="font-size: 24pt; font-weight: bold; margin: 0;">تقرير المبيعات اليومية (مفرق)</h1>
                    <p style="font-size: 14pt; margin: 5px 0;">التاريخ: {today_str}</p>
                </div>
                <table width="100%" border="1" cellspacing="0" cellpadding="8" style="border-collapse: collapse; font-size: 14pt; text-align: center;">
                    <thead>
                        <tr style="background-color: #f0f0f0;">
                            <th width="50%">المادة</th>
                            <th width="20%">العدد المباع</th>
                            <th width="30%">الإجمالي</th>
                        </tr>
                    </thead>
                    <tbody>
            """
            for it in items:
                html += f"""
                        <tr>
                            <td>{it['name']}</td>
                            <td>{it['qty']}</td>
                            <td>{it['total_price']:,.0f}</td>
                        </tr>
                    """
            html += f"""
                    </tbody>
                </table>
                <div style="margin-top: 30px; text-align: left; border-top: 2px solid #000; padding-top: 10px;">
                    <h1 style="font-size: 22pt;">المجموع الكلي: {total_cash:,.0f}</h1>
                </div>
            </div>
            """
            doc = QTextDocument()
            doc.setHtml(html)
            printer = QPrinter(QPrinter.HighResolution)
            printer.setPageSize(QPrinter.A4)
            preview = QPrintPreviewDialog(printer, self)
            preview.setWindowTitle("معاينة تقرير اليومية")
            preview.paintRequested.connect(lambda p: doc.print_(p))
            preview.exec_()