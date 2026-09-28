import ctypes
import ctypes.wintypes

class PrinterInterface:
    def connect(self):
        raise NotImplementedError
    def send_data(self, data):
        raise NotImplementedError

class WindowsPrinter(PrinterInterface):
    def __init__(self, printer_name):
        self.printer_name = printer_name
        self.winspool = ctypes.WinDLL('winspool.drv')

    def connect(self):
        # We don't maintain an open connection like Serial. We'll open per job.
        return True

    def send_data(self, data):
        class DOC_INFO_1(ctypes.Structure):
            _fields_ = [
                ("pDocName", ctypes.c_char_p),
                ("pOutputFile", ctypes.c_char_p),
                ("pDatatype", ctypes.c_char_p)
            ]

        OpenPrinter = self.winspool.OpenPrinterA
        OpenPrinter.argtypes = [ctypes.c_char_p, ctypes.POINTER(ctypes.c_void_p), ctypes.c_void_p]
        OpenPrinter.restype = ctypes.wintypes.BOOL

        StartDocPrinter = self.winspool.StartDocPrinterA
        StartPagePrinter = self.winspool.StartPagePrinter
        WritePrinter = self.winspool.WritePrinter
        EndPagePrinter = self.winspool.EndPagePrinter
        EndDocPrinter = self.winspool.EndDocPrinter
        ClosePrinter = self.winspool.ClosePrinter

        hPrinter = ctypes.c_void_p()
        
        encoded_name = self.printer_name.encode('utf-8')
        if not OpenPrinter(encoded_name, ctypes.byref(hPrinter), None):
            print(f"Failed to open {self.printer_name}")
            return False

        doc_info = DOC_INFO_1(b"Label Studio Print", None, b"RAW")
        
        if StartDocPrinter(hPrinter, 1, ctypes.byref(doc_info)) <= 0:
            ClosePrinter(hPrinter)
            print("Failed to start doc.")
            return False

        StartPagePrinter(hPrinter)
        
        pcWritten = ctypes.wintypes.DWORD()
        # Ensure data is bytes-like before writing
        if isinstance(data, str):
            raw_bytes = data.encode('utf-8')
        else:
            raw_bytes = bytes(data) if not isinstance(data, bytes) else data
        WritePrinter(hPrinter, raw_bytes, len(raw_bytes), ctypes.byref(pcWritten))
        
        EndPagePrinter(hPrinter)
        EndDocPrinter(hPrinter)
        ClosePrinter(hPrinter)
        
        return True
