import win32print

print("--- Installed Windows Printers ---")
printers = win32print.EnumPrinters(win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS)

for p in printers:
    # EnumPrinters returns a tuple like:
    # (flags, description, name, comment)
    name = p[2]
    print(f"- {name}")
