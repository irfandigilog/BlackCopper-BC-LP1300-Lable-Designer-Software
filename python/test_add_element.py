import sys
import traceback

try:
    from PyQt6.QtWidgets import QApplication
    from main_window import MainWindow

    app = QApplication(sys.argv)
    window = MainWindow()
    window.add_element('text')
    window.add_element('barcode')
    print("SUCCESS: Added text and barcode without crashing.")
except Exception:
    print("Caught Exception:")
    traceback.print_exc()
    sys.exit(1)
