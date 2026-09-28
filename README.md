# Black Copper Label Designer

A professional **TSPL thermal label designer** for Windows. Design and print labels to any TSPL-compatible thermal printer — no internet required, works offline right out of the box.

---

## 📋 System Requirements

| Requirement | Details |
|---|---|
| **Operating System** | Windows 10 / 11 (64-bit) |
| **Printer** | Any TSPL-compatible thermal printer (e.g. BlackCopper BC-LP1300) |
| **Python** | ❌ Not required — the app is fully self-contained |
| **Internet** | ❌ Not required — all resources are bundled |
| **Storage** | ~200 MB free disk space |

---

## 🚀 Installation (No Installation Required!)

The application is **portable** — no installer, no admin rights, no internet needed.

### Steps

1. **Copy** the `Black Copper 03124002221` folder to anywhere on your PC (Desktop, USB drive, D:\ , etc.)
2. **Double-click** `Black Copper 03124002221.exe` inside that folder
3. The application launches immediately ✅

> **⚠️ Important:** Do NOT move the `.exe` file out of its folder. The app needs all the files in the folder to run. Always run it from inside the `Black Copper 03124002221` folder.

---

## 🖨️ Printer Setup

1. Connect your **BlackCopper BC-LP1300** (or compatible TSPL printer) via **USB**
2. Windows will automatically install the printer driver
3. In the app, click **"Connect Printer"** in the top bar
4. Click **"Calibrate Printer"** for first-time use to detect label gap size

> For other TSPL printers, change the printer name in `python/printer.py` line 2 (only needed if running from source).

---

## 📖 How to Use

### 1. Set Label Size

In the **left sidebar**, set:

- **Width (mm)** — label width (e.g., 40)
- **Height (mm)** — label height (e.g., 30)
- **Printer DPI** — 203 DPI (standard) or 300 DPI (high quality)

### 2. Fine-tune Print Position (Offset)

If the printed content is **not centered** or is shifted on the physical label, use the **PRINT OFFSET** controls in the sidebar:

| Field | Effect |
|---|---|
| **Offset X (mm)** | Shifts entire print **right (+)** or left (−) |
| **Offset Y (mm)** | Shifts entire print **down (+)** or up (−) |

> **Tip:** Start with `Offset X = 2` or `3` and print a test. Adjust until centered. These are saved in your project file.

### 3. Add Elements

Click any tool button in the **"ADD ELEMENTS"** section:

| Button | Element | Description |
|--------|---------|-------------|
| **T Text** | Text | Add a text label with custom font |
| **\|\|\|\| Barcode** | Barcode | Code128 barcode |
| **□ Box** | Rectangle | Draw a bordered box |
| **— Line** | Line | Draw a horizontal line/bar |
| **🌄 Image** | Image | Import PNG/JPG/BMP image |
| **QR Code** | QR Code | Generate a QR code |
| **📄 PDF** | PDF Import | Import first page of a PDF as image |
| **📊 CSV** | Batch Print | Import CSV for variable data printing |

### 4. Edit Element Properties

- **Click** any element on the canvas to select it
- Edit its properties in the **right panel**
- **Drag** to reposition (snaps to 1mm grid by default)
- Use **Center Horiz / Center Vert** buttons to align element to label center

### 5. Save & Load Projects

- Click **"Save Project"** to save your design as a `.json` file
- Click **"Load Project"** to reload a saved design
- Projects save all elements, positions, sizes, and label dimensions

### 6. Print

1. Set **Copies** count in the top bar (default: 1)
2. Click **"Print Label"**
3. The TSPL command is sent directly to the printer

---

## 📊 Batch/CSV Printing

You can print variable data labels using a CSV file:

1. Create a CSV file with headers as column names, e.g.:

   ```
   Name,Barcode,Price
   Product A,123456789,PKR 150
   Product B,987654321,PKR 250
   ```

2. In your label design, use `{ColumnName}` placeholders in text/barcode fields:
   - Text element: `{Name}` → becomes `Product A` for row 1
   - Barcode element data: `{Barcode}` → becomes `123456789` for row 1
3. Click **📊 CSV** and select your CSV file
4. Click **"Print Label"** — one label is printed per row automatically

---

## ↩️ Undo / Redo

| Action | Shortcut |
|--------|----------|
| Undo | `Ctrl + Z` |
| Redo | `Ctrl + Y` |
| Delete selected element | `Delete` key |

---

## 🔧 Troubleshooting

### App won't start

- Make sure you are running the `.exe` from **inside** the `Black Copper 03124002221` folder
- Right-click the exe → **"Run as Administrator"** if it still fails

### Printer not found / print fails

- Ensure the printer is connected via USB and powered on
- Go to `Windows Settings → Printers & Scanners` and verify the printer appears
- Try **"Calibrate Printer"** first to initialize the printer connection
- Verify the printer name matches exactly: **BlackCopper BC-LP1300**

### Barcode not visible on canvas

- Make sure the barcode data field contains valid alphanumeric text
- Code128 barcodes support: numbers, uppercase A-Z, and special characters

### PDF import looks pixelated

- PDF is rasterized at 300 DPI for best quality
- Ensure the label size (Width/Height) is set correctly before importing PDF

### "Snap to Grid" is off

- The **"Snap to Grid (1mm)"** checkbox in the sidebar controls grid snapping
- Check the box to enable precise 1mm placement

### Content not centered on printed label

- Use the **PRINT OFFSET** section in the sidebar to shift the print physically
- Try **Offset X = 2–5 mm** depending on your printer's head position
- This does not move elements on the canvas — it shifts the entire printed area

---

## 📁 File Structure

```
Black Copper 03124002221/          ← Portable app folder (copy this whole folder)
├── Black Copper 03124002221.exe   ← Main executable
└── _internal/                     ← Runtime libraries (do not modify)
    ├── PyQt6/                     ← GUI Framework
    ├── PIL/                       ← Image processing
    ├── pymupdf/                   ← PDF support
    └── ...                        ← Other bundled libraries
```

---

## 📝 Project Files (.json)

Saved label projects are standard JSON files. You can share them between PCs — just open the `.json` file with **"Load Project"** on any machine that has this app installed.

---

## ℹ️ About

- **App Name:** Black Copper Label Designer
- **Version:** 1.0.0
- **Platform:** Windows 10/11 (64-bit)
- **GUI Framework:** PyQt6
- **TSPL Engine:** Custom TSPL generator
- **Printer Protocol:** TSPL (TSC Printer Language)
- **Supported Printers:** Any TSPL-compatible thermal label printer

---

*For support or customization, refer to the source code in the `python/` directory.*
