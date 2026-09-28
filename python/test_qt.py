from PyQt6.QtWidgets import QApplication, QLabel
import sys

try:
    app = QApplication(sys.argv)
    label = QLabel("Hello World")
    label.show()
    print("PyQt6 loaded successfully")
    # app.exec() # Don't block for test
except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)
