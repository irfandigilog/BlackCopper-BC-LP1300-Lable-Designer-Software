import sys
import traceback

try:
    from main_window import MainWindow
    from PyQt6.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    window = MainWindow()
    print("MainWindow initialized successfully")
    # window.show()
except Exception:
    print("Caught Exception:")
    traceback.print_exc()
    sys.exit(1)
