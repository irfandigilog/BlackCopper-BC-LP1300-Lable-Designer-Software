import serial.tools.list_ports
import usb.core
import usb.util

print("--- Available COM Ports ---")
ports = serial.tools.list_ports.comports()
for port, desc, hwid in sorted(ports):
    print(f"{port}: {desc} [{hwid}]")

print("\n--- Available USB Devices ---")
try:
    devices = usb.core.find(find_all=True)
    if devices:
        for dev in devices:
            try:
                product = usb.util.get_string(dev, dev.iProduct) if dev.iProduct else "Unknown"
                print(f"USB: {hex(dev.idVendor)}:{hex(dev.idProduct)} - {product}")
            except Exception as e:
                 print(f"USB: {hex(dev.idVendor)}:{hex(dev.idProduct)} - Cannot read string ({e})")
    else:
        print("No USB devices found.")
except Exception as e:
    print(f"PyUSB Error: {e}")
