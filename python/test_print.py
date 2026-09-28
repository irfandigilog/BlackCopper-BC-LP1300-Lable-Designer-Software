import ctypes
import ctypes.wintypes

def send_raw_print(printer_name, data):
    winspool = ctypes.WinDLL('winspool.drv')

    class DOC_INFO_1(ctypes.Structure):
        _fields_ = [
            ("pDocName", ctypes.c_char_p),
            ("pOutputFile", ctypes.c_char_p),
            ("pDatatype", ctypes.c_char_p)
        ]

    # Function signatures
    OpenPrinter = winspool.OpenPrinterA
    OpenPrinter.argtypes = [ctypes.c_char_p, ctypes.POINTER(ctypes.c_void_p), ctypes.c_void_p]
    OpenPrinter.restype = ctypes.wintypes.BOOL

    StartDocPrinter = winspool.StartDocPrinterA
    StartPagePrinter = winspool.StartPagePrinter
    WritePrinter = winspool.WritePrinter
    EndPagePrinter = winspool.EndPagePrinter
    EndDocPrinter = winspool.EndDocPrinter
    ClosePrinter = winspool.ClosePrinter

    hPrinter = ctypes.c_void_p()
    # Try opening printer
    res = OpenPrinter(printer_name.encode('utf-8'), ctypes.byref(hPrinter), None)
    if not res:
        print(f"Failed to open {printer_name}")
        return False

    doc_info = DOC_INFO_1(b"Python Raw Print", None, b"RAW")
    
    if StartDocPrinter(hPrinter, 1, ctypes.byref(doc_info)) <= 0:
        ClosePrinter(hPrinter)
        print("Failed to start doc.")
        return False

    StartPagePrinter(hPrinter)
    
    pcWritten = ctypes.wintypes.DWORD()
    WritePrinter(hPrinter, data, len(data), ctypes.byref(pcWritten))
    
    EndPagePrinter(hPrinter)
    EndDocPrinter(hPrinter)
    ClosePrinter(hPrinter)
    
    print("Sent TSPL to printer.")
    return True

if __name__ == "__main__":
    printer_name = "BlackCopper BC-LP1300"
    tspl_data = b'SIZE 40 mm,30 mm\r\nGAP 2 mm, 0 mm\r\nCLS\r\nTEXT 10,10,"2",0,1,1,"Hello Label Studio"\r\nPRINT 1,1\r\n'
    send_raw_print(printer_name, tspl_data)
