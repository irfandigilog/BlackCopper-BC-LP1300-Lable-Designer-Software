import sys
import copy
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QPushButton, QLabel, QLineEdit,
                             QComboBox, QFrame, QScrollArea, QPlainTextEdit,
                             QFileDialog, QCheckBox, QSpinBox, QSplitter,
                             QDialog, QTextEdit)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QUndoStack, QUndoCommand, QKeySequence, QShortcut
from canvas import LabelCanvas
from engine import TSPLGenerator, TextElement, BarcodeElement, QRCodeElement, BoxElement, LineElement, CircleElement, ImageElement




# ---------------------------------------------------------------------------
# Calibration & Diagnostics Dialog
# ---------------------------------------------------------------------------

class CalibrationDialog(QDialog):
    """Dedicated Printer Calibration, Alignment & Diagnostics Dialog."""
    def __init__(self, main_window):
        super().__init__(main_window)
        self.mw = main_window
        self.setWindowTitle("🖨️ Printer Calibration & Diagnostics")
        self.setFixedSize(540, 580)
        self.setModal(True)
        
        self.setStyleSheet("""
            QDialog { background-color: #0d1117; }
            QLabel { color: #f0f6fc; font-size: 13px; }
            #card { background-color: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 12px; }
            #card-title { color: #58a6ff; font-weight: bold; font-size: 14px; margin-bottom: 4px; }
            QPushButton {
                background-color: #21262d; border: 1px solid #363b42; color: #c9d1d9;
                padding: 10px 16px; border-radius: 6px; font-weight: bold; font-size: 12px;
            }
            QPushButton:hover { background-color: #30363d; border-color: #58a6ff; color: #ffffff; }
            #btn-action-primary { background-color: #1f6feb; border: 1px solid #58a6ff; color: #ffffff; }
            #btn-action-primary:hover { background-color: #388bfd; }
            #btn-action-success { background-color: #238636; border: 1px solid #2ea043; color: #ffffff; }
            #btn-action-success:hover { background-color: #2ea043; }
            QTextEdit {
                background-color: #090d13; border: 1px solid #30363d; color: #7ee787;
                font-family: Consolas, monospace; font-size: 12px; border-radius: 6px; padding: 6px;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(18, 18, 18, 18)

        # Header Info
        header_lbl = QLabel("🖨️ Black Copper BC-LP1300 Calibration")
        header_lbl.setStyleSheet("color: #58a6ff; font-size: 17px; font-weight: bold;")
        layout.addWidget(header_lbl)

        # Label Configuration Card
        card = QFrame()
        card.setObjectName("card")
        card_layout = QVBoxLayout(card)
        card_layout.setSpacing(6)
        
        lbl_card_title = QLabel("Current Roll Configuration:")
        lbl_card_title.setObjectName("card-title")
        card_layout.addWidget(lbl_card_title)

        w = float(self.mw.input_width.text() or 50)
        h = float(self.mw.input_height.text() or 15)
        cols = int(self.mw.combo_columns.currentData() or 1) if hasattr(self.mw, 'combo_columns') else 1
        h_gap = float(self.mw.input_gap_h.text() or 2) if hasattr(self.mw, 'input_gap_h') else 2.0
        v_gap = float(self.mw.input_gap_v.text() or 2) if hasattr(self.mw, 'input_gap_v') else 2.0
        total_w = (cols * w) + ((cols - 1) * h_gap)

        self.info_lbl = QLabel(
            f"• Label Size: <b>{w} mm</b> × <b>{h} mm</b>  |  <b>{cols} Column{'s' if cols>1 else ''}</b>\n"
            f"• Total Roll Width: <span style='color:#58a6ff; font-weight:bold;'>{total_w} mm</span>  |  Gap: <b>{h_gap} mm</b> (H) × <b>{v_gap} mm</b> (V)"
        )
        self.info_lbl.setTextFormat(Qt.TextFormat.RichText)
        card_layout.addWidget(self.info_lbl)
        layout.addWidget(card)

        # Action Buttons Grid
        btn_layout = QVBoxLayout()
        btn_layout.setSpacing(8)

        # 1. GAPDETECT Auto Calibration
        self.btn_auto_cal = QPushButton("⚙️  Run Auto-Calibration (GAPDETECT)")
        self.btn_auto_cal.setObjectName("btn-action-primary")
        self.btn_auto_cal.setToolTip("Feeds labels to detect the optical gap sensor threshold and saves in printer EEPROM.")
        self.btn_auto_cal.clicked.connect(self.run_gapdetect)
        btn_layout.addWidget(self.btn_auto_cal)

        # Row with Feed 1 Label, Test Print & Beep
        row2 = QHBoxLayout()
        self.btn_feed = QPushButton("📄  Feed 1 Label")
        self.btn_feed.setToolTip("Feeds exactly 1 label pitch to test sensor alignment.")
        self.btn_feed.clicked.connect(self.run_feed_label)
        row2.addWidget(self.btn_feed)

        self.btn_test = QPushButton("🧪  Print Test Alignment")
        self.btn_test.setObjectName("btn-action-success")
        self.btn_test.setToolTip("Prints test boxes & barcodes on all columns to verify alignment.")
        self.btn_test.clicked.connect(self.run_test_print)
        row2.addWidget(self.btn_test)

        self.btn_beep = QPushButton("🔊  Beep")
        self.btn_beep.setToolTip("Sends a 2-tone beep to verify printer connection.")
        self.btn_beep.clicked.connect(self.run_beep)
        row2.addWidget(self.btn_beep)
        btn_layout.addLayout(row2)

        layout.addLayout(btn_layout)

        # Log Text Box
        layout.addWidget(QLabel("Diagnostics Log:"))
        self.log_edit = QTextEdit()
        self.log_edit.setReadOnly(True)
        self.log_edit.setFixedHeight(140)
        layout.addWidget(self.log_edit)

        # Close Button
        btn_close = QPushButton("Close")
        btn_close.clicked.connect(self.accept)
        layout.addWidget(btn_close, alignment=Qt.AlignmentFlag.AlignRight)

        self.log("Ready. Connect Black Copper BC-LP1300 and click an action.")

    def log(self, msg, status="info"):
        import datetime
        t = datetime.datetime.now().strftime("%H:%M:%S")
        if status == "ok":
            color = "#7ee787"
        elif status == "err":
            color = "#ff7b72"
        else:
            color = "#79c0ff"
        self.log_edit.append(f"<span style='color:#8b949e;'>[{t}]</span> <span style='color:{color};'>{msg}</span>")
        self.log_edit.moveCursor(self.log_edit.textCursor().MoveOperation.End)

    def _get_params(self):
        w = float(self.mw.input_width.text() or 50)
        h = float(self.mw.input_height.text() or 15)
        cols = int(self.mw.combo_columns.currentData() or 1) if hasattr(self.mw, 'combo_columns') else 1
        h_gap = float(self.mw.input_gap_h.text() or 2) if hasattr(self.mw, 'input_gap_h') else 2.0
        v_gap = float(self.mw.input_gap_v.text() or 2) if hasattr(self.mw, 'input_gap_v') else 2.0
        total_w = (cols * w) + ((cols - 1) * h_gap)
        return w, h, cols, h_gap, v_gap, total_w

    def run_gapdetect(self):
        self.log("Sending GAPDETECT calibration commands...", "info")
        from printer import WindowsPrinter
        printer = WindowsPrinter("BlackCopper BC-LP1300")
        w, h, cols, h_gap, v_gap, total_w = self._get_params()
        cmd = f"SIZE {total_w} mm, {h} mm\r\nGAP {v_gap} mm, 0 mm\r\nGAPDETECT\r\nBEEP 2,200\r\n".encode('ascii')
        if printer.send_data(cmd):
            self.log(f"✅ GAPDETECT sent! (Roll: {total_w}x{h}mm, Gap: {v_gap}mm). Printer will feed labels & beep.", "ok")
        else:
            self.log("❌ Failed to send command. Ensure printer is connected and turned on.", "err")

    def run_feed_label(self):
        self.log("Feeding 1 label...", "info")
        from printer import WindowsPrinter
        printer = WindowsPrinter("BlackCopper BC-LP1300")
        w, h, cols, h_gap, v_gap, total_w = self._get_params()
        cmd = f"SIZE {total_w} mm, {h} mm\r\nGAP {v_gap} mm, 0 mm\r\nCLS\r\nPRINT 1,1\r\n".encode('ascii')
        if printer.send_data(cmd):
            self.log("✅ Fed 1 label pitch. Check if label stops exactly at tear line.", "ok")
        else:
            self.log("❌ Failed to feed label. Check printer connection.", "err")

    def run_test_print(self):
        self.log("Sending multi-column test alignment pattern...", "info")
        from printer import WindowsPrinter
        printer = WindowsPrinter("BlackCopper BC-LP1300")
        w, h, cols, h_gap, v_gap, total_w = self._get_params()
        dpi = self.mw.dpi_combo.currentData() or 8
        direction = getattr(self.mw, 'print_direction', 0)

        tspl = bytearray()
        tspl.extend(f"SIZE {total_w} mm, {h} mm\r\n".encode('ascii'))
        tspl.extend(f"GAP {v_gap} mm, 0 mm\r\n".encode('ascii'))
        tspl.extend(f"DIRECTION {direction},0\r\n".encode('ascii'))
        tspl.extend(b"CLS\r\n")

        for col in range(cols):
            col_x_mm = col * (w + h_gap)
            x_dots = round(col_x_mm * dpi)
            w_dots = round(w * dpi)
            h_dots = round(h * dpi)

            # Outer boundary box
            tspl.extend(f"BOX {x_dots + 4},{4},{x_dots + w_dots - 4},{h_dots - 4},1\r\n".encode('ascii'))
            # Col title & size
            tspl.extend(f'TEXT {x_dots + 8},8,"2",0,1,1,"Col {col + 1}: {int(w)}x{int(h)}mm"\r\n'.encode('ascii'))
            if h >= 14:
                bc_h = max(20, min(50, h_dots - 50))
                tspl.extend(f'BARCODE {x_dots + 8},32,"128",{bc_h},1,0,2,2,"TEST1234"\r\n'.encode('ascii'))

        tspl.extend(b"PRINT 1,1\r\n")

        if printer.send_data(tspl):
            self.log("✅ Test alignment pattern printed successfully across all columns!", "ok")
        else:
            self.log("❌ Failed to print test pattern. Check printer connection.", "err")

    def run_beep(self):
        self.log("Sending beep test...", "info")
        from printer import WindowsPrinter
        printer = WindowsPrinter("BlackCopper BC-LP1300")
        if printer.send_data(b"BEEP 2,200\r\n"):
            self.log("✅ Beep signal sent successfully!", "ok")
        else:
            self.log("❌ Failed to send beep signal.", "err")


# ---------------------------------------------------------------------------
# Undo/Redo Command Classes
# ---------------------------------------------------------------------------

class AddElementCommand(QUndoCommand):
    """Undo command for adding a new element to the canvas."""
    def __init__(self, window, el, description="Add Element"):
        super().__init__(description)
        self.window = window
        self.el = el

    def redo(self):
        self.window.elements.append(self.el)
        self.window._draw_element(self.el)

    def undo(self):
        self.window.elements = [e for e in self.window.elements if e.id != self.el.id]
        self.window.canvas.remove_item(self.el.id)
        if self.window.selected_id == self.el.id:
            self.window.on_element_selected(None)


class DeleteElementCommand(QUndoCommand):
    """Undo command for deleting an element."""
    def __init__(self, window, el, description="Delete Element"):
        super().__init__(description)
        self.window = window
        self.el = copy.deepcopy(el)

    def redo(self):
        self.window.elements = [e for e in self.window.elements if e.id != self.el.id]
        self.window.canvas.remove_item(self.el.id)
        if self.window.selected_id == self.el.id:
            self.window.on_element_selected(None)

    def undo(self):
        self.window.elements.append(self.el)
        self.window._draw_element(self.el)


class MoveElementCommand(QUndoCommand):
    """Undo command for moving an element."""
    def __init__(self, window, el_id, old_x, old_y, new_x, new_y, description="Move Element"):
        super().__init__(description)
        self.window = window
        self.el_id = el_id
        self.old_x, self.old_y = old_x, old_y
        self.new_x, self.new_y = new_x, new_y

    def redo(self):
        self._apply(self.new_x, self.new_y)

    def undo(self):
        self._apply(self.old_x, self.old_y)

    def _apply(self, x, y):
        el = next((e for e in self.window.elements if e.id == self.el_id), None)
        if el:
            el.x, el.y = x, y
            self.window.canvas.update_item_data(self.el_id, el)
            if self.window.selected_id == self.el_id:
                self.window.on_element_selected(self.el_id)


class PropertyChangeCommand(QUndoCommand):
    """Undo command for a property change on an element."""
    def __init__(self, window, el_id, old_props, new_props, description="Change Property"):
        super().__init__(description)
        self.window = window
        self.el_id = el_id
        self.old_props = old_props
        self.new_props = new_props

    def redo(self):
        self._apply(self.new_props)

    def undo(self):
        self._apply(self.old_props)
        if self.window.selected_id == self.el_id:
            self.window.on_element_selected(self.el_id)

    def _apply(self, props):
        el = next((e for e in self.window.elements if e.id == self.el_id), None)
        if el:
            for k, v in props.items():
                setattr(el, k, v)
            self.window.canvas.update_item_data(self.el_id, el)


# ---------------------------------------------------------------------------
# Main Window
# ---------------------------------------------------------------------------

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Black Copper 03124002221")
        self.resize(1100, 700)
        
        self.elements = []
        self.selected_id = None
        self.csv_data = None
        self.clipboard_el = None     # deep copy of the last copied element
        self.paste_count = 0         # cascades repeated pastes so copies don't stack
        
        # Alignment & Setup state
        self.ref_x = 0.0
        self.ref_y = 0.0
        self.print_direction = 0  # DIRECTION 0 required for BC-LP1300
        self.is_portrait = False  # False=landscape, True=portrait

        # Undo/Redo stack
        self.undo_stack = QUndoStack(self)

        self.init_ui()
        self.apply_styles()
        self._install_shortcuts()

    # -----------------------------------------------------------------------
    # UI Initialization
    # -----------------------------------------------------------------------

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # --- Top Bar ---
        self.top_bar = QFrame()
        self.top_bar.setObjectName("top-bar")
        self.top_bar.setFixedHeight(60)
        top_layout = QHBoxLayout(self.top_bar)

        title_lbl = QLabel("Black Copper 03124002221")
        title_lbl.setObjectName("app-title")
        top_layout.addWidget(title_lbl)
        top_layout.addStretch()

        btn_load = QPushButton("Load Project")
        btn_load.clicked.connect(self.on_load_project)
        top_layout.addWidget(btn_load)

        btn_save = QPushButton("Save Project")
        btn_save.clicked.connect(self.on_save_project)
        top_layout.addWidget(btn_save)

        btn_calibrate = QPushButton("Calibrate Printer")
        btn_calibrate.clicked.connect(self.on_calibrate_clicked)
        top_layout.addWidget(btn_calibrate)

        # --- Undo / Redo buttons ---
        self.btn_undo = QPushButton("↩ Undo")
        self.btn_undo.setToolTip("Undo (Ctrl+Z)")
        self.btn_undo.setEnabled(False)
        self.btn_undo.clicked.connect(self.undo_stack.undo)
        top_layout.addWidget(self.btn_undo)

        self.btn_redo = QPushButton("↪ Redo")
        self.btn_redo.setToolTip("Redo (Ctrl+Y)")
        self.btn_redo.setEnabled(False)
        self.btn_redo.clicked.connect(self.undo_stack.redo)
        top_layout.addWidget(self.btn_redo)

        # Connect undo stack to button enabled states
        self.undo_stack.canUndoChanged.connect(self.btn_undo.setEnabled)
        self.undo_stack.canRedoChanged.connect(self.btn_redo.setEnabled)

        top_layout.addWidget(QLabel("Copies:"))
        self.spin_copies = QSpinBox()
        self.spin_copies.setMinimum(1)
        self.spin_copies.setMaximum(9999)
        self.spin_copies.setValue(1)
        self.spin_copies.setFixedWidth(65)
        top_layout.addWidget(self.spin_copies)

        btn_print = QPushButton("Print Label")
        btn_print.clicked.connect(self.on_print_clicked)
        top_layout.addWidget(btn_print)

        btn_connect = QPushButton("Connect Printer")
        btn_connect.setObjectName("btn-primary")
        top_layout.addWidget(btn_connect)

        # --- Content Area: use a QSplitter for resizable panes ---
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(2)
        splitter.setChildrenCollapsible(False)

        # Sidebar content widget (wrapped in scroll area below)
        sidebar_content = QWidget()
        sidebar_content.setObjectName("sidebar")
        sidebar_layout = QVBoxLayout(sidebar_content)
        sidebar_layout.setContentsMargins(12, 12, 12, 12)
        sidebar_layout.setSpacing(4)

        lbl_setup = QLabel("LABEL SETUP")
        lbl_setup.setObjectName("section-header")
        sidebar_layout.addWidget(lbl_setup)

        sidebar_layout.addWidget(QLabel("Label Width (mm)"))
        self.input_width = QLineEdit("50")
        self.input_width.textChanged.connect(self.on_label_size_changed)
        sidebar_layout.addWidget(self.input_width)

        sidebar_layout.addWidget(QLabel("Label Height (mm)"))
        self.input_height = QLineEdit("15")
        self.input_height.textChanged.connect(self.on_label_size_changed)
        sidebar_layout.addWidget(self.input_height)

        sidebar_layout.addWidget(QLabel("Labels Across (Columns / Rows)"))
        self.combo_columns = QComboBox()
        self.combo_columns.addItem("1 Label Across (Single)", 1)
        self.combo_columns.addItem("2 Labels Across (Dual Row)", 2)
        self.combo_columns.addItem("3 Labels Across (3 Row)", 3)
        self.combo_columns.addItem("4 Labels Across (4 Row)", 4)
        self.combo_columns.currentIndexChanged.connect(self.on_label_size_changed)
        sidebar_layout.addWidget(self.combo_columns)

        # Gaps configuration
        gaps_layout = QHBoxLayout()
        gap_h_layout = QVBoxLayout()
        gap_h_layout.addWidget(QLabel("Col Gap (mm)"))
        self.input_gap_h = QLineEdit("2")
        self.input_gap_h.setToolTip("Horizontal gap between labels side-by-side on the roll")
        self.input_gap_h.textChanged.connect(self.on_label_size_changed)
        gap_h_layout.addWidget(self.input_gap_h)
        gaps_layout.addLayout(gap_h_layout)

        gap_v_layout = QVBoxLayout()
        gap_v_layout.addWidget(QLabel("Row Gap (mm)"))
        self.input_gap_v = QLineEdit("2")
        self.input_gap_v.setToolTip("Vertical gap between label rows along the feed direction")
        self.input_gap_v.textChanged.connect(self.on_label_size_changed)
        gap_v_layout.addWidget(self.input_gap_v)
        gaps_layout.addLayout(gap_v_layout)
        sidebar_layout.addLayout(gaps_layout)

        self.chk_auto_duplicate = QCheckBox("Duplicate design to all columns")
        self.chk_auto_duplicate.setChecked(True)
        self.chk_auto_duplicate.setToolTip("Automatically prints identical copies on all label columns across the row")
        self.chk_auto_duplicate.toggled.connect(self.on_label_size_changed)
        sidebar_layout.addWidget(self.chk_auto_duplicate)

        # Portrait / Landscape toggle (checkable radio-style buttons)
        orient_layout = QHBoxLayout()
        self.btn_portrait = QPushButton("Portrait")
        self.btn_portrait.setObjectName("orient-btn")
        self.btn_portrait.setCheckable(True)
        self.btn_portrait.setToolTip("Portrait: Height > Width")
        self.btn_portrait.clicked.connect(self.set_portrait)
        orient_layout.addWidget(self.btn_portrait)
        self.btn_landscape = QPushButton("Landscape")
        self.btn_landscape.setObjectName("orient-btn")
        self.btn_landscape.setCheckable(True)
        self.btn_landscape.setChecked(True)  # default = landscape (W > H)
        self.btn_landscape.setToolTip("Landscape: Width > Height")
        self.btn_landscape.clicked.connect(self.set_landscape)
        orient_layout.addWidget(self.btn_landscape)
        sidebar_layout.addLayout(orient_layout)

        sidebar_layout.addWidget(QLabel("Printer DPI"))
        self.dpi_combo = QComboBox()
        self.dpi_combo.addItem("203 DPI (8 d/mm)", 8)
        self.dpi_combo.addItem("300 DPI (12 d/mm)", 12)
        sidebar_layout.addWidget(self.dpi_combo)

        self.chk_snap = QCheckBox("Snap to Grid (1mm)")
        self.chk_snap.setChecked(True)
        self.chk_snap.toggled.connect(lambda v: setattr(self.canvas, 'snap_to_grid', v))
        sidebar_layout.addWidget(self.chk_snap)

        sidebar_layout.addSpacing(15)

        lbl_offset = QLabel("PRINT OFFSET")
        lbl_offset.setObjectName("section-header")
        sidebar_layout.addWidget(lbl_offset)

        sidebar_layout.addWidget(QLabel("Offset X (mm)  [shift right +]"))
        self.input_offset_x = QLineEdit("0")
        self.input_offset_x.setToolTip("Shifts the entire print left/right on the physical label.\nIncrease if content prints too far left.")
        self.input_offset_x.textChanged.connect(self.on_offset_x_changed)
        sidebar_layout.addWidget(self.input_offset_x)

        sidebar_layout.addWidget(QLabel("Offset Y (mm)  [shift down +]"))
        self.input_offset_y = QLineEdit("0")
        self.input_offset_y.setToolTip("Shifts the entire print up/down on the physical label.\nIncrease if content prints too far up.")
        self.input_offset_y.textChanged.connect(self.on_offset_y_changed)
        sidebar_layout.addWidget(self.input_offset_y)

        sidebar_layout.addSpacing(6)
        sidebar_layout.addWidget(QLabel("Print Direction"))
        self.dir_combo = QComboBox()
        self.dir_combo.addItem("0 - Standard / Top-Down (Normal)", 0)
        self.dir_combo.addItem("1 - Inverted 180° (Alternate)", 1)
        self.dir_combo.setToolTip("DIRECTION 0 is standard for BC-LP1300.\nSwitch to 1 (Inverted) if your text prints upside down.")
        self.dir_combo.currentIndexChanged.connect(
            lambda: setattr(self, 'print_direction', self.dir_combo.currentData())
        )
        sidebar_layout.addWidget(self.dir_combo)

        sidebar_layout.addSpacing(10)

        lbl_elements = QLabel("ADD ELEMENTS")
        lbl_elements.setObjectName("section-header")
        sidebar_layout.addWidget(lbl_elements)

        tools_layout = QHBoxLayout()
        btn_text = QPushButton("T\nText")
        btn_text.setObjectName("tool-btn")
        btn_text.clicked.connect(lambda: self.add_element('text'))
        tools_layout.addWidget(btn_text)

        btn_barcode = QPushButton("||||\nBarcode")
        btn_barcode.setObjectName("tool-btn")
        btn_barcode.clicked.connect(lambda: self.add_element('barcode'))
        tools_layout.addWidget(btn_barcode)
        sidebar_layout.addLayout(tools_layout)

        tools_layout2 = QHBoxLayout()
        btn_box = QPushButton("[ ]\nBox")
        btn_box.setObjectName("tool-btn")
        btn_box.clicked.connect(lambda: self.add_element('box'))
        tools_layout2.addWidget(btn_box)

        btn_line = QPushButton("---\nLine")
        btn_line.setObjectName("tool-btn")
        btn_line.clicked.connect(lambda: self.add_element('line'))
        tools_layout2.addWidget(btn_line)

        btn_image = QPushButton("IMG\nImage")
        btn_image.setObjectName("tool-btn")
        btn_image.clicked.connect(lambda: self.add_element('image'))
        tools_layout2.addWidget(btn_image)
        sidebar_layout.addLayout(tools_layout2)

        tools_layout3 = QHBoxLayout()
        btn_qr = QPushButton("QR\nCode")
        btn_qr.setObjectName("tool-btn")
        btn_qr.clicked.connect(lambda: self.add_element('qrcode'))
        tools_layout3.addWidget(btn_qr)

        btn_import_pdf = QPushButton("PDF\nImport")
        btn_import_pdf.setObjectName("tool-btn")
        btn_import_pdf.clicked.connect(self.on_import_pdf_clicked)
        tools_layout3.addWidget(btn_import_pdf)

        btn_import_csv = QPushButton("CSV\nBatch")
        btn_import_csv.setObjectName("tool-btn")
        btn_import_csv.clicked.connect(self.on_import_csv_clicked)
        tools_layout3.addWidget(btn_import_csv)
        sidebar_layout.addLayout(tools_layout3)

        sidebar_layout.addStretch()

        # Wrap sidebar in a QScrollArea so it doesn't overflow on small windows
        self.sidebar = QScrollArea()
        self.sidebar.setObjectName("sidebar-scroll")
        self.sidebar.setWidget(sidebar_content)
        self.sidebar.setWidgetResizable(True)
        self.sidebar.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.sidebar.setMinimumWidth(190)
        self.sidebar.setMaximumWidth(230)

        # Canvas
        self.canvas_container = QWidget()
        self.canvas_container.setObjectName("canvas-container")
        canvas_layout = QVBoxLayout(self.canvas_container)
        self.canvas = LabelCanvas()
        self.on_label_size_changed()
        self.canvas.elementSelected.connect(self.on_element_selected)
        self.canvas.elementMoved.connect(self.on_element_moved)
        self.canvas.elementResized.connect(self.on_element_resized)
        canvas_layout.addWidget(self.canvas, alignment=Qt.AlignmentFlag.AlignCenter)

        # Properties Panel
        self.props_panel = QFrame()
        self.props_panel.setMinimumWidth(200)
        self.props_panel.setObjectName("props-panel")
        self.props_layout = QVBoxLayout(self.props_panel)
        self.props_layout.addWidget(QLabel("<b>Properties</b>"))

        self.props_widget = QWidget()
        self.props_inner_layout = QVBoxLayout(self.props_widget)
        self.props_inner_layout.setContentsMargins(0, 0, 0, 0)
        self.props_layout.addWidget(self.props_widget)

        self.empty_label = QLabel("Select an element")
        self.props_layout.addWidget(self.empty_label)

        self.btn_delete = QPushButton("Delete Selected")
        self.btn_delete.setObjectName("btn-danger")
        self.btn_delete.setStyleSheet("background-color: #dc3545; color: white; font-weight: bold;")
        self.btn_delete.clicked.connect(self.on_delete_clicked)
        self.btn_delete.hide()

        self.btn_duplicate = QPushButton("⧉ Duplicate (Ctrl+D)")
        self.btn_duplicate.setToolTip("Duplicate selected element — or Ctrl+C then Ctrl+V")
        self.btn_duplicate.clicked.connect(self.on_duplicate_clicked)
        self.btn_duplicate.hide()
        self.props_layout.addWidget(self.btn_duplicate)
        self.props_layout.addWidget(self.btn_delete)

        self.props_layout.addStretch()

        # Assemble splitter
        splitter.addWidget(self.sidebar)
        splitter.addWidget(self.canvas_container)
        splitter.addWidget(self.props_panel)
        splitter.setStretchFactor(0, 0)  # sidebar: fixed
        splitter.setStretchFactor(1, 1)  # canvas: stretches
        splitter.setStretchFactor(2, 0)  # props: fixed
        splitter.setSizes([220, 600, 240])

        main_layout.setDirection(QVBoxLayout.Direction.TopToBottom)
        main_layout.addWidget(self.top_bar)
        main_layout.addWidget(splitter, 1)

    def _install_shortcuts(self):
        QShortcut(QKeySequence("Ctrl+Z"), self).activated.connect(self.undo_stack.undo)
        QShortcut(QKeySequence("Ctrl+Y"), self).activated.connect(self.undo_stack.redo)
        QShortcut(QKeySequence("Delete"), self).activated.connect(self.on_delete_clicked)
        QShortcut(QKeySequence("Ctrl+C"), self).activated.connect(self.on_copy_clicked)
        QShortcut(QKeySequence("Ctrl+V"), self).activated.connect(self.on_paste_clicked)
        QShortcut(QKeySequence("Ctrl+D"), self).activated.connect(self.on_duplicate_clicked)

    # -----------------------------------------------------------------------
    # Label Size
    # -----------------------------------------------------------------------

    def on_label_size_changed(self):
        try:
            w = float(self.input_width.text() or 50)
            h = float(self.input_height.text() or 15)
            cols = int(self.combo_columns.currentData() or 1) if hasattr(self, 'combo_columns') else 1
            h_gap = float(self.input_gap_h.text() or 2) if hasattr(self, 'input_gap_h') else 2.0
            v_gap = float(self.input_gap_v.text() or 2) if hasattr(self, 'input_gap_v') else 2.0
            dup = self.chk_auto_duplicate.isChecked() if hasattr(self, 'chk_auto_duplicate') else True
            self.canvas.set_label_layout(w, h, cols, h_gap, v_gap, dup)
        except ValueError:
            pass

    # -----------------------------------------------------------------------
    # Element Selection / Properties
    # -----------------------------------------------------------------------

    @staticmethod
    def _clear_layout(layout):
        """Recursively remove all widgets and child layouts from a layout."""
        if layout is None:
            return
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget:
                # IMPORTANT: never call setParent(None) — that turns the widget
                # into a top-level window (ghost popup). Just hide + schedule delete.
                widget.hide()
                widget.deleteLater()
            elif item.layout():
                MainWindow._clear_layout(item.layout())
                item.layout().deleteLater()

    def on_element_selected(self, el_id):
        self.selected_id = el_id
        self._clear_layout(self.props_inner_layout)

        if not el_id:
            self.empty_label.show()
            self.btn_delete.hide()
            self.btn_duplicate.hide()
            return

        self.empty_label.hide()
        self.btn_delete.show()
        self.btn_duplicate.show()
        el = next((e for e in self.elements if e.id == el_id), None)
        if not el:
            return

        self.add_prop_control("X (mm)", str(el.x), lambda v: self._prop_change(el_id, 'x', float(v or 0)))
        self.add_prop_control("Y (mm)", str(el.y), lambda v: self._prop_change(el_id, 'y', float(v or 0)))

        if type(el) == TextElement:
            self.add_multiline_prop_control("Text Content", el.text, lambda v: self._prop_change(el_id, 'text', v))
            font_styles = [
                ("1 - Small (8x12 dots)", "1"),
                ("2 - Standard (12x20 dots)", "2"),
                ("3 - Medium (16x24 dots)", "3"),
                ("4 - Large (24x32 dots)", "4"),
                ("5 - Extra Large (32x48 dots)", "5"),
                ("6 - OCR-B (14x19 dots)", "6"),
                ("7 - OCR-A (14x19 dots)", "7"),
                ("8 - Bold (21x27 dots)", "8"),
                ("TST24.BF2 - Smooth Vector / TTF", "TST24.BF2"),
                ("TSS24.BF2 - Asian / Chinese Font", "TSS24.BF2"),
            ]
            self.add_combo_prop_control("Font Style", font_styles, el.font_type, lambda v: self._prop_change(el_id, 'font_type', v))
            font_scales = [(f"{i}x Scale", i) for i in range(1, 11)]
            self.add_combo_prop_control("Font Size Multiplier", font_scales, el.font_size, lambda v: self._prop_change_int(el_id, 'font_size', v, 1))
        elif type(el) == BarcodeElement:
            self.add_prop_control("Barcode Data", el.data, lambda v: self._prop_change(el_id, 'data', v))
            self.add_prop_control("Height (dots)", str(el.height), lambda v: self._prop_change_int(el_id, 'height', v, 20))
        elif type(el) == QRCodeElement:
            self.add_prop_control("QR Data", el.data, lambda v: self._prop_change(el_id, 'data', v))
            self.add_prop_control("Cell Width (1-10)", str(el.cell_width), lambda v: self._prop_change_int(el_id, 'cell_width', v, 4))
        elif type(el) == BoxElement:
            self.add_prop_control("Width (mm)", str(el.width_mm), lambda v: self._prop_change_int(el_id, 'width_mm', v, 20))
            self.add_prop_control("Height (mm)", str(el.height_mm), lambda v: self._prop_change_int(el_id, 'height_mm', v, 20))
            self.add_prop_control("Thickness (dots)", str(el.thickness), lambda v: self._prop_change_int(el_id, 'thickness', v, 1))
        elif type(el) == LineElement:
            self.add_prop_control("Width (mm)", str(el.width_mm), lambda v: self._prop_change_int(el_id, 'width_mm', v, 40))
            self.add_prop_control("Height/Thickness (mm)", str(el.height_mm), lambda v: self._prop_change_int(el_id, 'height_mm', v, 1))
        elif type(el) == CircleElement:
            self.add_prop_control("Diameter (mm)", str(el.diameter_mm), lambda v: self._prop_change_int(el_id, 'diameter_mm', v, 20))
            self.add_prop_control("Thickness (dots)", str(el.thickness), lambda v: self._prop_change_int(el_id, 'thickness', v, 1))
        elif type(el) == ImageElement:
            file_name_only = str(el.image_path).split('/')[-1] if '/' in el.image_path else str(el.image_path).split('\\')[-1]
            self.add_prop_control("File", file_name_only, lambda v: None)
            self.add_prop_control("Width (mm)", str(round(el.width_mm, 2)), lambda v: self._prop_change_int(el_id, 'width_mm', v, 30))
            self.add_prop_control("Height (mm)", str(round(el.height_mm, 2)), lambda v: self._prop_change_int(el_id, 'height_mm', v, 30))

        self.add_button_row(
            "Center Horiz", lambda: self.center_element(el_id, 'h', el),
            "Center Vert",  lambda: self.center_element(el_id, 'v', el)
        )

    # -----------------------------------------------------------------------
    # Property Change Helpers (with Undo support)
    # -----------------------------------------------------------------------

    def _prop_change(self, el_id, prop, new_value):
        el = next((e for e in self.elements if e.id == el_id), None)
        if not el:
            return
        old_value = getattr(el, prop, None)
        if old_value == new_value:
            return
        cmd = PropertyChangeCommand(
            self, el_id,
            old_props={prop: old_value},
            new_props={prop: new_value},
            description=f"Change {prop}"
        )
        self.undo_stack.push(cmd)

    def _prop_change_int(self, el_id, prop, str_val, fallback):
        try:
            val = int(str_val)
        except ValueError:
            val = fallback
        self._prop_change(el_id, prop, val)

    # -----------------------------------------------------------------------
    # Other Property Panel Helpers
    # -----------------------------------------------------------------------

    def _update_xy_fields(self, new_x, new_y):
        """Update only the X and Y coordinate QLineEdits in the properties panel.
        
        Avoids rebuilding the entire panel (which causes ghost popup windows).
        The first two QLineEdit widgets in props_inner_layout are always X and Y.
        """
        line_edits_found = 0
        for i in range(self.props_inner_layout.count()):
            item = self.props_inner_layout.itemAt(i)
            if item and item.widget() and isinstance(item.widget(), QLineEdit):
                line_edits_found += 1
                field = item.widget()
                if line_edits_found == 1:
                    field.blockSignals(True)
                    field.setText(str(round(new_x, 1)))
                    field.blockSignals(False)
                elif line_edits_found == 2:
                    field.blockSignals(True)
                    field.setText(str(round(new_y, 1)))
                    field.blockSignals(False)
                    break  # X and Y are always the first two — done

    def add_button_row(self, label1, callback1, label2, callback2):
        """Add two full-width stacked buttons (avoids text clipping in narrow panels)."""
        btn1 = QPushButton(label1)
        btn1.clicked.connect(callback1)
        self.props_inner_layout.addWidget(btn1)
        btn2 = QPushButton(label2)
        btn2.clicked.connect(callback2)
        self.props_inner_layout.addWidget(btn2)

    def center_element(self, el_id, direction, el):
        canvas_w = float(self.input_width.text() or 40)
        canvas_h = float(self.input_height.text() or 30)

        item = next((i for i in self.canvas.scene.items() if getattr(i, 'element_id', None) == el_id), None)
        if not item:
            return

        rect = item.sceneBoundingRect()
        item_w_mm = rect.width() / self.canvas.dpi_scale
        item_h_mm = rect.height() / self.canvas.dpi_scale

        if direction == 'h':
            new_x = (canvas_w - item_w_mm) / 2
            self._prop_change(el_id, 'x', max(0.0, new_x))
        elif direction == 'v':
            new_y = (canvas_h - item_h_mm) / 2
            self._prop_change(el_id, 'y', max(0.0, new_y))

        self.on_element_selected(el_id)

    def on_delete_clicked(self):
        if not self.selected_id:
            return
        el = next((e for e in self.elements if e.id == self.selected_id), None)
        if not el:
            return
        cmd = DeleteElementCommand(self, el, description="Delete Element")
        self.undo_stack.push(cmd)

    # -----------------------------------------------------------------------
    # Copy / Paste / Duplicate
    # -----------------------------------------------------------------------

    def _text_field_has_focus(self):
        """True when the user is typing in a field, so Ctrl+C/V must stay plain text copy/paste."""
        return isinstance(QApplication.focusWidget(), (QLineEdit, QPlainTextEdit, QTextEdit))

    def on_copy_clicked(self):
        if self._text_field_has_focus() or not self.selected_id:
            return
        el = next((e for e in self.elements if e.id == self.selected_id), None)
        if el:
            # Snapshot now, so later edits to the original don't change what gets pasted
            self.clipboard_el = copy.deepcopy(el)
            self.paste_count = 0

    def on_paste_clicked(self):
        if self._text_field_has_focus() or self.clipboard_el is None:
            return
        self.paste_count += 1
        self._insert_copy(self.clipboard_el, 2.0 * self.paste_count)

    def on_duplicate_clicked(self):
        if not self.selected_id:
            return
        el = next((e for e in self.elements if e.id == self.selected_id), None)
        if el:
            self._insert_copy(el, 2.0)

    def _insert_copy(self, source_el, shift_mm):
        import random
        new_el = copy.deepcopy(source_el)
        new_el.id = f"el_{len(self.elements)}_{random.randint(0, 99999)}"

        try:
            cur_w = float(self.input_width.text() or 40)
            cur_h = float(self.input_height.text() or 30)
        except ValueError:
            cur_w, cur_h = 40.0, 30.0

        # Shift down-right so the copy is visible, but keep it on the label
        new_el.x = max(0.0, min(source_el.x + shift_mm, cur_w - 2.0))
        new_el.y = max(0.0, min(source_el.y + shift_mm, cur_h - 2.0))

        cmd = AddElementCommand(self, new_el, description="Duplicate Element")
        self.undo_stack.push(cmd)
        self.canvas.select_item(new_el.id)
        self.on_element_selected(new_el.id)

    def add_multiline_prop_control(self, label, value, callback):
        self.props_inner_layout.addWidget(QLabel(label))
        edit = QPlainTextEdit(value)
        edit.setFixedHeight(75)
        edit.textChanged.connect(lambda: callback(edit.toPlainText()))
        self.props_inner_layout.addWidget(edit)

    def add_prop_control(self, label, value, callback):
        self.props_inner_layout.addWidget(QLabel(label))
        edit = QLineEdit(value)
        edit.textChanged.connect(callback)
        self.props_inner_layout.addWidget(edit)

    def add_combo_prop_control(self, label, items, current_value, callback):
        self.props_inner_layout.addWidget(QLabel(label))
        combo = QComboBox()
        for text, val in items:
            combo.addItem(text, val)
        idx = combo.findData(current_value)
        if idx >= 0:
            combo.setCurrentIndex(idx)
        combo.currentIndexChanged.connect(lambda: callback(combo.currentData()))
        self.props_inner_layout.addWidget(combo)

    # -----------------------------------------------------------------------
    # Element Movement / Resize (from canvas signals)
    # -----------------------------------------------------------------------

    def on_element_moved(self, el_id, new_x, new_y):
        el = next((e for e in self.elements if e.id == el_id), None)
        if not el:
            return
        old_x, old_y = el.x, el.y
        if old_x == new_x and old_y == new_y:
            return
        # Apply immediately (canvas already snapped visually); push undo command
        el.x, el.y = new_x, new_y
        cmd = MoveElementCommand(self, el_id, old_x, old_y, new_x, new_y)
        self.undo_stack.push(cmd)
        if self.selected_id == el_id:
            # Update only the X/Y fields in place — do NOT rebuild the whole panel
            # (rebuilding causes ghost popup windows during dragging)
            self._update_xy_fields(new_x, new_y)

    def on_element_resized(self, el_id, w, h):
        el = next((e for e in self.elements if e.id == el_id), None)
        if el:
            el.width_mm = w
            el.height_mm = h
            if self.selected_id == el_id:
                self.on_element_selected(el_id)

    def on_offset_x_changed(self, val):
        try:
            self.ref_x = float(val)
        except ValueError:
            self.ref_x = 0

    def on_rotate_orientation(self):
        """Swap label width/height (portrait <-> landscape) and rotate element positions 90 deg."""
        try:
            w = float(self.input_width.text() or 40)
            h = float(self.input_height.text() or 30)
        except ValueError:
            return

        # Rotate each element's position: (x, y) -> (old_h - y - elem_h_approx, x)
        for el in self.elements:
            old_x, old_y = el.x, el.y
            # Simple 90-deg rotation mapping into new dimensions (h x w)
            new_x = old_y
            new_y = w - old_x
            el.x = max(0.0, round(new_x, 1))
            el.y = max(0.0, round(new_y, 1))

        # Swap width and height in the UI (triggers canvas resize via textChanged)
        self.input_width.setText(str(h))
        self.input_height.setText(str(w))

        # Redraw all elements at new positions
        for el in self.elements:
            self.canvas.remove_item(el.id)
            self._draw_element(el)

        # Refresh property panel if something is selected
        if self.selected_id:
            self.on_element_selected(self.selected_id)

    def set_portrait(self):
        """Portrait: Height is the larger dimension + rotate TSPL 90° on print."""
        try:
            w = float(self.input_width.text() or 40)
            h = float(self.input_height.text() or 30)
        except ValueError:
            return
        long_side = max(w, h)
        short_side = min(w, h)
        # Block signals temporarily to avoid double-update, then set both fields
        self.input_width.blockSignals(True)
        self.input_height.blockSignals(True)
        self.input_width.setText(str(short_side))
        self.input_height.setText(str(long_side))
        self.input_width.blockSignals(False)
        self.input_height.blockSignals(False)
        self.is_portrait = True
        self.btn_portrait.setChecked(True)
        self.btn_landscape.setChecked(False)
        # Force canvas to update to portrait shape
        self.canvas.set_label_size(short_side, long_side)

    def set_landscape(self):
        """Landscape: Width is the larger dimension + normal TSPL output."""
        try:
            w = float(self.input_width.text() or 40)
            h = float(self.input_height.text() or 30)
        except ValueError:
            return
        long_side = max(w, h)
        short_side = min(w, h)
        # Block signals temporarily to avoid double-update, then set both fields
        self.input_width.blockSignals(True)
        self.input_height.blockSignals(True)
        self.input_width.setText(str(long_side))
        self.input_height.setText(str(short_side))
        self.input_width.blockSignals(False)
        self.input_height.blockSignals(False)
        self.is_portrait = False
        self.btn_landscape.setChecked(True)
        self.btn_portrait.setChecked(False)
        # Force canvas to update to landscape shape
        self.canvas.set_label_size(long_side, short_side)

    def on_offset_y_changed(self, val):
        try:
            self.ref_y = float(val)
        except ValueError:
            self.ref_y = 0

    # -----------------------------------------------------------------------
    # Drawing helper called by Add/Undo commands
    # -----------------------------------------------------------------------

    def _draw_element(self, el):
        """(Re)draws an element on the canvas based on its type."""
        if type(el) == TextElement:
            self.canvas.add_text(el.id, el.text, el.x, el.y, el.font_size)
        elif type(el) == BarcodeElement:
            self.canvas.add_barcode(el.id, el.data, el.x, el.y, el.height)
        elif type(el) == QRCodeElement:
            self.canvas.add_qrcode(el.id, el.data, el.x, el.y)
        elif type(el) == BoxElement:
            self.canvas.add_box(el.id, el.width_mm, el.height_mm, el.x, el.y)
        elif type(el) == LineElement:
            self.canvas.add_line(el.id, el.width_mm, el.height_mm, el.x, el.y)
        elif type(el) == CircleElement:
            self.canvas.add_circle(el.id, el.diameter_mm, el.x, el.y)
        elif type(el) == ImageElement:
            self.canvas.add_image(el.id, getattr(el, 'image_path', ''), el.width_mm, el.height_mm, el.x, el.y)
        self.canvas.update_item_data(el.id, el)
        # Force immediate repaint so element is always visible right away
        self.canvas.scene.update()
        self.canvas.viewport().update()

    def add_element(self, el_type):
        import random
        el_id = f"el_{len(self.elements)}_{random.randint(0, 99999)}"

        try:
            cur_w = float(self.input_width.text() or 40)
            cur_h = float(self.input_height.text() or 30)
        except ValueError:
            cur_w, cur_h = 40.0, 30.0

        # Offset each new element so they don't stack directly on top of each other
        offset = len(self.elements) * 1.5
        spawn_x = min(2.0 + offset, max(0.0, cur_w - 8.0))
        spawn_y = min(2.0 + offset, max(0.0, cur_h - 8.0))

        if el_type == 'text':
            el = TextElement(el_id, spawn_x, spawn_y)
        elif el_type == 'barcode':
            el = BarcodeElement(el_id, spawn_x, spawn_y)
        elif el_type == 'qrcode':
            el = QRCodeElement(el_id, spawn_x, spawn_y)
        elif el_type == 'box':
            el = BoxElement(el_id, spawn_x, spawn_y)
        elif el_type == 'line':
            el = LineElement(el_id, spawn_x, spawn_y)
        elif el_type == 'circle':
            el = CircleElement(el_id, spawn_x, spawn_y)
        elif el_type == 'image':
            file_name, _ = QFileDialog.getOpenFileName(self, "Open Image", "", "Image Files (*.png *.jpg *.jpeg *.bmp)")
            if file_name:
                el = ImageElement(el_id, spawn_x, spawn_y, file_name)
                from PyQt6.QtGui import QPixmap
                pix = QPixmap(file_name)
                if not pix.isNull():
                    el.width_mm = min(30.0, max(5.0, cur_w - 4.0))
                    el.height_mm = el.width_mm * (pix.height() / pix.width())
            else:
                return
        else:
            return

        cmd = AddElementCommand(self, el, description=f"Add {el_type.capitalize()}")
        self.undo_stack.push(cmd)
        self.on_element_selected(el.id)

    # -----------------------------------------------------------------------
    # Save / Load Project
    # -----------------------------------------------------------------------

    def on_save_project(self):
        file_name, _ = QFileDialog.getSaveFileName(self, "Save Project", "", "JSON Files (*.json)")
        if not file_name:
            return
        import json
        data = {
            "label_width": float(self.input_width.text() or 50),
            "label_height": float(self.input_height.text() or 15),
            "columns": int(self.combo_columns.currentData() or 1) if hasattr(self, 'combo_columns') else 1,
            "gap_h": float(self.input_gap_h.text() or 2) if hasattr(self, 'input_gap_h') else 2.0,
            "gap_v": float(self.input_gap_v.text() or 2) if hasattr(self, 'input_gap_v') else 2.0,
            "auto_duplicate": self.chk_auto_duplicate.isChecked() if hasattr(self, 'chk_auto_duplicate') else True,
            "dpi_multiplier": self.dpi_combo.currentData(),
            "elements": [el.to_dict() for el in self.elements]
        }
        with open(file_name, 'w') as f:
            json.dump(data, f, indent=4)
        print(f"Project saved to {file_name}")

    def on_load_project(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Load Project", "", "JSON Files (*.json)")
        if not file_name:
            return
        import json
        from engine import LabelElement

        try:
            with open(file_name, 'r') as f:
                data = json.load(f)

            self.input_width.setText(str(data.get("label_width", 50)))
            self.input_height.setText(str(data.get("label_height", 15)))

            if hasattr(self, 'combo_columns'):
                col_idx = self.combo_columns.findData(data.get("columns", 1))
                if col_idx >= 0:
                    self.combo_columns.setCurrentIndex(col_idx)

            if hasattr(self, 'input_gap_h'):
                self.input_gap_h.setText(str(data.get("gap_h", 2)))
            if hasattr(self, 'input_gap_v'):
                self.input_gap_v.setText(str(data.get("gap_v", 2)))
            if hasattr(self, 'chk_auto_duplicate'):
                self.chk_auto_duplicate.setChecked(bool(data.get("auto_duplicate", True)))

            dpi_idx = self.dpi_combo.findData(data.get("dpi_multiplier", 8))
            if dpi_idx >= 0:
                self.dpi_combo.setCurrentIndex(dpi_idx)

            # Clear canvas
            for el in self.elements:
                self.canvas.remove_item(el.id)
            self.elements.clear()
            self.undo_stack.clear()
            self.on_element_selected(None)

            for el_data in data.get("elements", []):
                el = LabelElement.from_dict(el_data)
                if not el:
                    continue
                self.elements.append(el)
                self._draw_element(el)

            self.on_label_size_changed()
            print(f"Project loaded from {file_name}")
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"Failed to load project: {e}")

    # -----------------------------------------------------------------------
    # Print
    # -----------------------------------------------------------------------

    def on_calibrate_clicked(self):
        dlg = CalibrationDialog(self)
        dlg.exec()

    def on_print_clicked(self):
        dpi_multiplier = self.dpi_combo.currentData()
        width_mm = float(self.input_width.text() or 50)
        height_mm = float(self.input_height.text() or 15)
        columns = int(self.combo_columns.currentData() or 1) if hasattr(self, 'combo_columns') else 1
        h_gap = float(self.input_gap_h.text() or 2) if hasattr(self, 'input_gap_h') else 2.0
        v_gap = float(self.input_gap_v.text() or 2) if hasattr(self, 'input_gap_v') else 2.0
        duplicate_cols = self.chk_auto_duplicate.isChecked() if hasattr(self, 'chk_auto_duplicate') else True
        copies = self.spin_copies.value()

        full_tspl = bytearray()

        if getattr(self, 'csv_data', None):
            # Batch CSV multi-column printing
            csv_rows = self.csv_data
            step = columns if duplicate_cols else 1
            for i in range(0, len(csv_rows), step):
                chunk = csv_rows[i : i + step]
                batch_elements = []
                for col_idx, row in enumerate(chunk):
                    col_shift = col_idx * (width_mm + h_gap)
                    for el in self.elements:
                        cloned = copy.deepcopy(el)
                        if hasattr(cloned, 'text') and isinstance(cloned.text, str):
                            for k, v in row.items():
                                if k:
                                    cloned.text = cloned.text.replace(f"{{{k}}}", str(v))
                        if hasattr(cloned, 'data') and isinstance(cloned.data, str):
                            for k, v in row.items():
                                if k:
                                    cloned.data = cloned.data.replace(f"{{{k}}}", str(v))
                        cloned.x = cloned.x + col_shift
                        batch_elements.append(cloned)
                tspl = TSPLGenerator.generate(width_mm, height_mm, batch_elements, self.ref_x, self.ref_y, 
                                             dpi_multiplier, copies, direction=self.print_direction, 
                                             portrait=self.is_portrait, columns=columns, h_gap=h_gap, 
                                             v_gap=v_gap, duplicate_cols=False)
                full_tspl.extend(tspl)
        else:
            full_tspl = TSPLGenerator.generate(width_mm, height_mm, self.elements, self.ref_x, self.ref_y, 
                                               dpi_multiplier, copies, direction=self.print_direction, 
                                               portrait=self.is_portrait, columns=columns, h_gap=h_gap, 
                                               v_gap=v_gap, duplicate_cols=duplicate_cols)

        from printer import WindowsPrinter
        printer = WindowsPrinter("BlackCopper BC-LP1300")
        if printer.connect() and printer.send_data(full_tspl):
            print("Printed successfully to BlackCopper BC-LP1300.")
        else:
            print("Failed to print to BlackCopper BC-LP1300.")

    # -----------------------------------------------------------------------
    # CSV / PDF Import
    # -----------------------------------------------------------------------

    def on_import_csv_clicked(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Import CSV Data", "", "CSV Files (*.csv)")
        if not file_name:
            return
        import csv
        try:
            with open(file_name, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                self.csv_data = list(reader)
            print(f"Loaded {len(self.csv_data)} rows from CSV. Headers: {reader.fieldnames}")
            self.setWindowTitle(f"Black Copper 03124002221 - [Batch Mode: {len(self.csv_data)} rows]")
        except Exception as e:
            print(f"Failed to load CSV: {e}")

    def on_import_pdf_clicked(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Import PDF", "", "PDF Files (*.pdf)")
        if not file_name:
            return

        try:
            import fitz
            import os, tempfile, uuid

            doc = fitz.open(file_name)
            if doc.page_count == 0:
                print("PDF is empty.")
                return

            page = doc.load_page(0)
            pix = page.get_pixmap(dpi=300, alpha=False)

            temp_dir = tempfile.gettempdir()
            unique_filename = f"imported_label_{uuid.uuid4().hex}.png"
            temp_img_path = os.path.join(temp_dir, unique_filename)
            pix.save(temp_img_path)

            width_mm = float(self.input_width.text() or 40)
            height_mm = float(self.input_height.text() or 30)

            import random
            el_id = f"el_{len(self.elements)}_pdf_{random.randint(0, 99999)}"
            el = ImageElement(el_id, 0, 0, temp_img_path)
            el.width_mm = width_mm
            el.height_mm = height_mm

            cmd = AddElementCommand(self, el, description="Import PDF")
            self.undo_stack.push(cmd)

            print(f"Imported PDF {file_name} as image.")
        except Exception as e:
            print(f"Failed to import PDF: {e}")

    # -----------------------------------------------------------------------
    # Styles
    # -----------------------------------------------------------------------

    def apply_styles(self):
        self.setStyleSheet("""
            QMainWindow { background-color: #0d1117; }
            #top-bar { background-color: #161b22; border-bottom: 1px solid #30363d; padding: 0 20px; }
            #app-title { color: #f0f6fc; font-size: 18px; font-weight: bold; }

            #sidebar-scroll { background-color: #161b22; border-right: 1px solid #30363d; }
            #sidebar-scroll QScrollBar:vertical { background: #161b22; width: 6px; margin: 0; }
            #sidebar-scroll QScrollBar::handle:vertical { background: #30363d; border-radius: 3px; min-height: 20px; }
            #sidebar-scroll QScrollBar::add-line:vertical, #sidebar-scroll QScrollBar::sub-line:vertical { height: 0; }
            #sidebar { background-color: #161b22; }

            #props-panel { background-color: #161b22; border-left: 1px solid #30363d; padding: 20px; }
            #canvas-container { background-color: #0d1117; }
            #section-header { color: #8b949e; font-size: 11px; font-weight: bold; letter-spacing: 1px; margin-bottom: 6px; margin-top: 8px;}

            QLabel { color: #c9d1d9; }
            QLineEdit, QPlainTextEdit {
                background-color: #0d1117; border: 1px solid #30363d; color: #c9d1d9;
                padding: 6px; border-radius: 6px; margin-bottom: 4px;
            }
            QLineEdit:focus, QPlainTextEdit:focus { border: 1px solid #58a6ff; }

            QPushButton {
                background-color: #21262d; border: 1px solid #363b42; color: #c9d1d9;
                padding: 8px 16px; border-radius: 6px; font-weight: 500;
            }
            QPushButton:hover { background-color: #30363d; border-color: #8b949e; }
            QPushButton:disabled { color: #484f58; border-color: #21262d; }

            QPushButton#orient-btn {
                background-color: #21262d; border: 1px solid #30363d;
                color: #c9d1d9; padding: 5px; border-radius: 6px; font-size: 12px;
            }
            QPushButton#orient-btn:checked {
                background-color: #1f6feb; border: 1px solid #58a6ff;
                color: #ffffff; font-weight: bold;
            }
            QPushButton#orient-btn:hover { background-color: #30363d; }
            QPushButton#orient-btn:checked:hover { background-color: #388bfd; }

            #btn-primary { background-color: #58a6ff; color: #ffffff; border: none; }
            #btn-primary:hover { background-color: #318bf8; }

            #btn-danger { background-color: #da3633; color: #ffffff; border: none; }
            #btn-danger:hover { background-color: #b32d2a; }

            #tool-btn {
                background-color: #0d1117; border: 1px solid #30363d;
                padding: 6px 4px; border-radius: 8px; font-size: 11px;
                font-weight: bold; min-height: 46px;
            }
            #tool-btn:hover { border-color: #58a6ff; color: #58a6ff; }

            QSpinBox {
                background-color: #0d1117; border: 1px solid #30363d; color: #c9d1d9;
                padding: 6px; border-radius: 6px;
            }
            QCheckBox { color: #c9d1d9; }
            QComboBox {
                background-color: #0d1117; border: 1px solid #30363d; color: #c9d1d9;
                padding: 6px; border-radius: 6px; margin-bottom: 4px;
            }
            QComboBox QAbstractItemView { background-color: #161b22; color: #c9d1d9; }
        """)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
