import sys
import json
import os
from PySide6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
                              QLineEdit, QPushButton, QToolButton, QLabel, QTableWidget, 
                              QTableWidgetItem, QHeaderView, QMessageBox, QFileDialog)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QIcon, QRegion, QPainterPath
from googletrans import Translator

translator = Translator()
try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.lib.enums import TA_LEFT, TA_RIGHT, TA_CENTER # Crucial: Import TA_CENTER

    # Import for Arabic text shaping
    from arabic_reshaper import ArabicReshaper
    from bidi.algorithm import get_display

    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    print("Warning: 'reportlab', 'arabic-reshaper', or 'python-bidi' not installed. PDF export will be disabled.")


class TableEditorWindow(QWidget):
    def __init__(self, parent, language):
        super().__init__()
        self.parent = parent
        self.language = language

        self.json_file = rf"C:\Users\hp\AppData\Roaming\dictionary_app_by_Anas_Moneer\main\dict_{language}.json"

        self.setWindowTitle(f"Dictionary Editor - {language.upper()}")
        self.setGeometry(200, 200, 600, 400)

        icon_path = r"C:\Users\hp\AppData\Roaming\dictionary_app_by_Anas_Moneer\dictionary1.ico"
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        else:
            print(f"Uyarı: İkon dosyası bulunamadı: {icon_path}")

        layout = QVBoxLayout(self)

        self.table = QTableWidget(self)
        self.table.setColumnCount(2)

        if language == "en":
            headers = ["English", "Arabic"]
        else:
            headers = ["Turkish", "Arabic"]

        self.table.setHorizontalHeaderLabels(headers)

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.Stretch)

        button_layout = QHBoxLayout()

        add_button = QPushButton("Add Row", self)
        add_button.clicked.connect(self.add_row)

        delete_button = QPushButton("Delete Row", self)
        delete_button.clicked.connect(self.delete_row)

        save_button = QPushButton("Save", self)
        save_button.clicked.connect(self.save_data)

        export_button = QPushButton("Export PDF", self)
        if not REPORTLAB_AVAILABLE:
            export_button.setEnabled(False)
            export_button.setToolTip("PDF dışa aktarma için 'reportlab', 'arabic-reshaper', 'python-bidi' yüklenmeli.")
        export_button.clicked.connect(self.export_pdf)

        button_layout.addWidget(add_button)
        button_layout.addWidget(delete_button)
        button_layout.addWidget(save_button)
        button_layout.addWidget(export_button)

        layout.addWidget(self.table)
        layout.addLayout(button_layout)

        self.load_data()

    def load_data(self):
        try:
            if os.path.exists(self.json_file):
                with open(self.json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                self.table.setRowCount(len(data))

                for row, item in enumerate(data):
                    word_item = QTableWidgetItem(item.get('word', ''))
                    meaning_item = QTableWidgetItem(item.get('meaning', ''))

                    self.table.setItem(row, 0, word_item)
                    self.table.setItem(row, 1, meaning_item)
            else:
                self.table.setRowCount(0)
                os.makedirs(os.path.dirname(self.json_file), exist_ok=True)
                with open(self.json_file, 'w', encoding='utf-8') as f:
                    json.dump([], f, ensure_ascii=False, indent=2)
                QMessageBox.information(self, "Bilgi", f"Sözlük dosyası bulunamadı. '{os.path.basename(self.json_file)}' oluşturuldu.")

        except json.JSONDecodeError:
            QMessageBox.critical(self, "Hata", f"JSON dosyası bozuk: {self.json_file}. Lütfen kontrol edin veya silin.")
            self.table.setRowCount(0)
        except Exception as e:
            QMessageBox.warning(self, "Hata", f"Dosya yüklenirken hata: {str(e)}")

    def add_row(self):
        row_count = self.table.rowCount()
        self.table.insertRow(row_count)

        self.table.setItem(row_count, 0, QTableWidgetItem(""))
        self.table.setItem(row_count, 1, QTableWidgetItem(""))

    def delete_row(self):
        current_row = self.table.currentRow()
        if current_row >= 0:
            self.table.removeRow(current_row)

    def save_data(self):
        try:
            data = []

            for row in range(self.table.rowCount()):
                word_item = self.table.item(row, 0)
                meaning_item = self.table.item(row, 1)

                if word_item and meaning_item:
                    word = word_item.text().strip()
                    meaning = meaning_item.text().strip()

                    if word or meaning:
                        data.append({
                            'word': word,
                            'meaning': meaning
                        })

            os.makedirs(os.path.dirname(self.json_file), exist_ok=True)
            with open(self.json_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Kaydetme hatası: {str(e)}")

    def export_pdf(self):
        if not REPORTLAB_AVAILABLE:
            QMessageBox.critical(self, "Hata", "PDF dışa aktarma için 'reportlab', 'arabic-reshaper', 'python-bidi' kütüphaneleri gerekli.\n\nKurulum: pip install reportlab arabic-reshaper python-bidi")
            return

        try:
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "PDF Olarak Kaydet",
                f"dictionary_{self.language}.pdf",
                "PDF Files (*.pdf)"
            )

            if not file_path:
                return

            # Re-import ReportLab components to ensure they are available within this scope
            from reportlab.lib.pagesizes import A4
            from reportlab.lib import colors
            from reportlab.lib.units import inch
            from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
            from reportlab.lib.styles import getSampleStyleSheet
            from reportlab.pdfbase import pdfmetrics
            from reportlab.pdfbase.ttfonts import TTFont
            from reportlab.lib.enums import TA_LEFT, TA_RIGHT, TA_CENTER # Crucial: Import TA_CENTER

            # --- Amiri Fontunu Buraya Kaydedin ---
            AMIRI_FONT_PATH = r"C:\Users\hp\AppData\Roaming\dictionary_app_by_Anas_Moneer\main\Amiri-Regular.ttf"
            AMIRI_FONT_NAME = 'Amiri' # ReportLab içinde kullanacağınız isim

            if os.path.exists(AMIRI_FONT_PATH):
                try:
                    pdfmetrics.registerFont(TTFont(AMIRI_FONT_NAME, AMIRI_FONT_PATH))
                    # Verify if the font was actually registered
                    if pdfmetrics.getFont(AMIRI_FONT_NAME):
                        print(f"DEBUG: Amiri fontu başarıyla yüklendi: {AMIRI_FONT_PATH}")
                    else:
                        raise RuntimeError("Font registration failed silently.")
                except Exception as e:
                    QMessageBox.warning(self, "Font Hatası", f"Amiri fontu yüklenirken hata oluştu: {e}\nPDF'deki Arapça metinler doğru görünmeyebilir.")
                    AMIRI_FONT_NAME = 'Helvetica' # Fallback
            else:
                QMessageBox.warning(self, "Font Hatası", f"Amiri fontu bulunamadı: {AMIRI_FONT_PATH}\nPDF'deki Arapça metinler doğru görünmeyebilir.")
                AMIRI_FONT_NAME = 'Helvetica' # Fallback

            doc = SimpleDocTemplate(file_path, pagesize=A4)
            elements = []

            table_data = []

            # Header'ları Paragraph olarak ekleyin ve hizalamaları ayarlayın
            styles = getSampleStyleSheet()
            header_ltr_style = styles['h2'].clone('HeaderLTRStyle') # Clone for safety
            header_ltr_style.fontName = 'Helvetica-Bold'
            header_ltr_style.alignment = TA_CENTER # Changed to TA_CENTER

            header_rtl_style = styles['h2'].clone('HeaderRTLStyle') # Clone for safety
            header_rtl_style.fontName = 'Helvetica-Bold'
            header_rtl_style.alignment = TA_CENTER # Changed to TA_CENTER

            processed_headers = []
            if self.language == "en":
                processed_headers.append(Paragraph("English", header_ltr_style))
                processed_headers.append(Paragraph("Arabic", header_rtl_style))
            else:
                processed_headers.append(Paragraph("Turkish", header_ltr_style))
                processed_headers.append(Paragraph("Arabic", header_rtl_style))

            table_data.append(processed_headers)

            # Arapça metin stili
            arabic_style = styles['Normal'].clone('ArabicStyle') # Clone the style
            arabic_style.fontName = AMIRI_FONT_NAME # Arapça fontunu kullan
            arabic_style.alignment = TA_CENTER # Changed to TA_CENTER
            arabic_style.rightToLeft = 1 # Explicitly set right-to-left direction
            arabic_style.fontSize = 10
            arabic_style.allowSplitting = 0 # Prevent splitting of Arabic text
            arabic_style.leading = 12 # Add leading for better line spacing

            # Latin (Türkçe/İngilizce) metin stili
            ltr_style = styles['Normal'].clone('LTRStyle') # Clone the style
            ltr_style.fontName = 'Helvetica' # veya 'Times-Roman'
            ltr_style.alignment = TA_CENTER # Changed to TA_CENTER
            ltr_style.fontSize = 10

            for row in range(self.table.rowCount()):
                word_item = self.table.item(row, 0)
                meaning_item = self.table.item(row, 1)

                if word_item and meaning_item:
                    word = word_item.text().strip()
                    meaning = meaning_item.text().strip()

                    if word or meaning:
                        processed_meaning_paragraph = None
                        # Check if the meaning contains Arabic characters
                        if self.is_arabic_text(meaning):
                            processed_meaning = self.prepare_arabic_text(meaning)
                            
                            # --- Diagnostic: Save reshaped Arabic text for verification ---
                            # Bu bölüm hata ayıklama amaçlıdır ve doğrulandıktan sonra kaldırılabilir.
                            # try:
                            #     debug_file_path = os.path.join(os.path.dirname(file_path), "debug_arabic_text.txt")
                            #     with open(debug_file_path, 'a', encoding='utf-8') as df:
                            #         df.write(f"Original: {meaning}\n")
                            #         df.write(f"Reshaped: {processed_meaning}\n\n")
                            #     print(f"DEBUG: Reshaped Arabic text appended to {debug_file_path}")
                            # except Exception as debug_e:
                            #     print(f"DEBUG: Failed to write debug Arabic text: {debug_e}")
                            # ----------------------------------------------------------------

                            processed_meaning_paragraph = Paragraph(processed_meaning, arabic_style)
                        else:
                            processed_meaning_paragraph = Paragraph(meaning, ltr_style)

                        processed_word_paragraph = Paragraph(word, ltr_style)

                        table_data.append([processed_word_paragraph, processed_meaning_paragraph])

            if len(table_data) <= 1:
                QMessageBox.information(self, "Bilgi", "Tabloda PDF'e aktarılacak veri yok!")
                return

            table = Table(table_data, colWidths=[3*inch, 3*inch])

            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('LINEBELOW', (0, 0), (-1, 0), 2, colors.black),
                ('LEFTPADDING', (0, 0), (-1, -1), 6),
                ('RIGHTPADDING', (0, 0), (-1, -1), 6),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                # Alignment for cells is handled by the Paragraph styles themselves
            ]))

            elements.append(table)
            doc.build(elements)

        except Exception as e:
            QMessageBox.critical(self, "Hata", f"PDF kaydetme hatası: {str(e)}")

    def is_arabic_text(self, text):
        # A more concise check for Arabic characters
        for char in text:
            if '\u0600' <= char <= '\u06FF' or \
               '\u0750' <= char <= '\u077F' or \
               '\u08A0' <= char <= '\u08FF' or \
               '\uFB50' <= char <= '\uFDFF' or \
               '\uFE70' <= char <= '\uFEFF':
                return True
        return False

    def prepare_arabic_text(self, text):
        reshaper = ArabicReshaper(
            configuration={
                'delete_harakat': False,
                'delete_tatweel': False,
                'support_ligatures': True,
                'arabic_reshaper_join_by_shadda': True,
                'delete_unnecessary_dots': False,
                'shift_harakat_position': False,
                'support_vocalized_arabic': True,
            }
        )
        reshaped_text = reshaper.reshape(text)
        bidi_text = get_display(reshaped_text)
        return bidi_text

    def closeEvent(self, event):
        self.save_data()
        event.accept()


class DictionaryApp(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Dictionary")
        self.setGeometry(1210, 100, 200, 20)
        self.title_bar_visible = True
        self.always_on_top = False
        self.table_window = None
	
        self.setWindowIcon(QIcon(r"C:\Users\hp\AppData\Roaming\dictionary_app_by_Anas_Moneer\dictionary1.ico"))

        # --- 1. Katman: Şeffaf pencere ---
        outer_layout = QVBoxLayout(self)
        outer_layout.setSizeConstraint(QVBoxLayout.SetFixedSize)
        outer_layout.setContentsMargins(0, 0, 0, 0)

        # --- 2. Katman: Radius'lu içerik ---
        self.content_widget = QWidget(self)
        self.content_widget.setStyleSheet("""
            background-color: #2E2E2E;
            border-radius: 7px;
        """)
        outer_layout.addWidget(self.content_widget)

        # --- Layoutlar ---
        main_layout = QVBoxLayout(self.content_widget)
        
        input_layout = QVBoxLayout()

        # --- Giriş kutusu (kelime) ---
        self.english_entry = QLineEdit(self.content_widget)
        self.english_entry.setPlaceholderText("Enter Word")
        self.english_entry.setStyleSheet("""
            font-size: 12pt;
            padding: 5px;
            border-radius: 5px;
            border: 1px solid #FD7B01;
            width: 120px;
        """)
        self.english_entry.textChanged.connect(self.reset_timer)

        # --- Çeviri kutusu ---
        self.translation_entry = QLineEdit(self.content_widget)
        self.translation_entry.setReadOnly(True)
        self.translation_entry.setPlaceholderText("Meaning")
        self.translation_entry.setStyleSheet("""
            font-size: 12pt;
            padding: 5px;
            border-radius: 5px;
            border: 1px solid #FF4031;
            width: 120px;
        """)

        # --- Save Butonu ---
        self.save_button = QPushButton("Save", self.content_widget)
        self.save_button.setStyleSheet("""
            font-size: 12pt;
            padding: 5px;
            border-radius: 5px;
            background-color: #FF3510;
            color: white;
            width: 80px;
            height: 24px;
        """)
        self.save_button.clicked.connect(self.save_to_json)

        # --- Mod Değiştirici Buton ---
        self.mode_button = QToolButton(self.content_widget)
        self.mode_button.setText("EN")
        self.mode_button.setStyleSheet("""
            background-color: #FB9901;
            border-radius: 5px;
            font-size: 12pt;
            padding: 5px;
            width: 30px;
            height: 21px;
        """)
        self.mode_button.clicked.connect(self.toggle_language_mode)
        self.language = "en"

        # --- Pin Butonu ---
        self.pin_button = QToolButton(self.content_widget)
        self.pin_button.setText("⚲")
        self.pin_button.setStyleSheet("""
            background-color: #FF4031;
            border-radius: 5px;
            font-size: 12pt;
            padding: 5px;
            width: 23px;
            height: 22px;
        """)
        self.pin_button.clicked.connect(self.toggle_title_bar)

        # --- Tablo Editör Butonu ---
        self.table_button = QToolButton(self.content_widget)
        self.table_button.setText("📄")
        self.table_button.setStyleSheet("""
            background-color: #4CAF50;
            border-radius: 5px;
            font-size: 12pt;
            padding: 5px;
            width: 23px;
            height: 22px;
        """)
        self.table_button.clicked.connect(self.open_table_editor)

        # --- Layoutlara yerleştir ---
        input_layout.addWidget(self.english_entry)
        input_layout.addWidget(self.translation_entry)
        
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.mode_button)
        button_layout.addWidget(self.pin_button)
        button_layout.addWidget(self.table_button)

        main_layout.addLayout(input_layout)
        main_layout.addLayout(button_layout)

        # Timer for debouncing
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)  # Only run once after the timeout
        self.timer.timeout.connect(self.translate_word)

    def reset_timer(self):
        """Reset the timer every time the user types a new character"""
        self.timer.start(500)  # Start the timer again with a 500ms delay

    def translate_word(self):
        """Kelimeyi çevirmek için bu fonksiyonu kullan"""
        if self.english_entry.text().strip() == "":
            self.translation_entry.clear()
            return

        english_word = self.english_entry.text().strip().capitalize()
        arabic_word = translator.translate(english_word, src=self.language, dest='ar').text.strip()

        self.translation_entry.setText(arabic_word)

    def toggle_language_mode(self):
        """Dil modunu değiştir ve buton görünümünü güncelle"""
        if self.language == "en":
            self.language = "tr"
            self.mode_button.setText("TR")
            self.mode_button.setStyleSheet("""
                background-color: #B74135;
                border-radius: 5px;
                font-size: 12pt;
                padding: 5px;
                width: 30px;
                height: 21px;
            """)
        else:
            self.language = "en"
            self.mode_button.setText("EN")
            self.mode_button.setStyleSheet("""
                background-color: #FB9901;
                border-radius: 5px;
                font-size: 12pt;
                padding: 5px;
                width: 30px;
                height: 21px;
            """)
        self.translate_word()

    def toggle_title_bar(self):
        if self.always_on_top:
            self.setWindowFlags(Qt.Window)
            self.setAttribute(Qt.WA_TranslucentBackground, False)
            self.setMask(QRegion())
            self.always_on_top = False
            self.content_widget.setStyleSheet("""
            background-color: #2E2E2E;  /* Koyu gri */
            border-radius: 7px;
        """)
        else:
            self.move(self.x(), self.y() + 30)
            self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
            self.setAttribute(Qt.WA_TranslucentBackground, True)
            self.always_on_top = True
            self.apply_rounded_mask()  # Şekli kırparak uygula

        self.setGeometry(self.x(), self.y(), self.width(), self.height())
        self.show()

    def apply_rounded_mask(self):
        radius = 8
        rect = self.rect()

        path = QPainterPath()
        path.addRoundedRect(rect, radius, radius)

        region = QRegion(path.toFillPolygon().toPolygon())
        self.setMask(region)

    def save_to_json(self):
        """Çevirilen kelimeyi JSON dosyasına kaydet"""
        if self.english_entry.text() == "":
            return
        
        english_word = self.english_entry.text().strip().capitalize()
        arabic_word = self.translation_entry.text().strip()
        
        json_file = rf"C:\Users\hp\AppData\Roaming\dictionary_app_by_Anas_Moneer\main\dict_{self.language}.json"
        
        try:
            # Mevcut verileri yükle
            data = []
            if os.path.exists(json_file):
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            
            # Yeni veriyi ekle
            new_entry = {
                'word': english_word,
                'meaning': arabic_word
            }
            
            # Aynı kelime var mı kontrol et
            word_exists = False
            for i, entry in enumerate(data):
                if entry['word'].lower() == english_word.lower():
                    data[i] = new_entry  # Güncelle
                    word_exists = True
                    break
            
            if not word_exists:
                data.append(new_entry)  # Yeni ekle
            
            # Dosyaya kaydet
            os.makedirs(os.path.dirname(json_file), exist_ok=True)
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
        except Exception as e:
            print(f"JSON kaydetme hatası: {e}")

        # Girişleri temizle
        self.english_entry.clear()
        self.english_entry.setFocus()
        self.translation_entry.clear()

    def open_table_editor(self):
        """Tablo editör penceresini aç"""
        if self.table_window is None or not self.table_window.isVisible():
            self.table_window = TableEditorWindow(self, self.language)
            self.table_window.show()
        else:
            self.table_window.raise_()
            self.table_window.activateWindow()

    def closeEvent(self, event):
        """Override the close event to hide the window instead of quitting the application"""
        event.accept()  # Do not let the window close
        self.hide()  # Hide the window

# Uygulama başlatma
app = QApplication(sys.argv)
window = DictionaryApp()

# Start the application
window.show()
sys.exit(app.exec())
