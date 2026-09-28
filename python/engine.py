import math
import copy

class LabelElement:
    def __init__(self, id, type, x, y):
        self.id = id
        self.type = type
        self.x = x  # mm
        self.y = y  # mm

    def to_dict(self):
        return self.__dict__.copy()

    @staticmethod
    def from_dict(data):
        element_type = data.get('type')
        if element_type == 'text':
            el = TextElement(data['id'], data['x'], data['y'])
        elif element_type == 'barcode':
            el = BarcodeElement(data['id'], data['x'], data['y'])
        elif element_type == 'box':
            el = BoxElement(data['id'], data['x'], data['y'])
        elif element_type == 'line':
            el = LineElement(data['id'], data['x'], data['y'])
        elif element_type == 'circle':
            el = CircleElement(data['id'], data['x'], data['y'])
        elif element_type == 'qrcode':
            el = QRCodeElement(data['id'], data['x'], data['y'])
        elif element_type == 'image':
            el = ImageElement(data['id'], data['x'], data['y'], data.get('image_path', ''))
        else:
            return None
        
        for k, v in data.items():
            setattr(el, k, v)
        return el

class TextElement(LabelElement):
    def __init__(self, id, x, y, text="Hello World", font_type="2", font_size=1):
        super().__init__(id, 'text', x, y)
        self.text = text
        self.font_type = font_type
        self.font_size = font_size

class BarcodeElement(LabelElement):
    def __init__(self, id, x, y):
        super().__init__(id, 'barcode', x, y)
        self.data = "12345678"
        self.height = 60   # height in dots (TSPL units)
        self.width_mm = 30  # display width on canvas in mm

class QRCodeElement(LabelElement):
    def __init__(self, id, x, y):
        super().__init__(id, 'qrcode', x, y)
        self.data = "https://digilog.pk"
        self.cell_width = 4

class BoxElement(LabelElement):
    def __init__(self, id, x, y):
        super().__init__(id, 'box', x, y)
        self.width_mm = 20
        self.height_mm = 20
        self.thickness = 1

class LineElement(LabelElement):
    def __init__(self, id, x, y):
        super().__init__(id, 'line', x, y)
        self.width_mm = 40
        self.height_mm = 1  # 1mm thickness

class CircleElement(LabelElement):
    def __init__(self, id, x, y):
        super().__init__(id, 'circle', x, y)
        self.diameter_mm = 20
        self.thickness = 1

class ImageElement(LabelElement):
    def __init__(self, id, x, y, image_path):
        super().__init__(id, 'image', x, y)
        self.image_path = image_path
        self.width_mm = 30
        self.height_mm = 30

class TSPLGenerator:
    @staticmethod
    def generate(label_width, label_height, elements, ref_x=0, ref_y=0, dpi=8, copies=1, 
                 direction=0, portrait=False, columns=1, h_gap=2.0, v_gap=2.0, duplicate_cols=True):
        tspl = bytearray()
        
        # Calculate total physical roll width across all columns
        columns = max(1, int(columns))
        total_roll_width = (columns * label_width) + ((columns - 1) * h_gap)

        if portrait:
            phys_width_mm = label_height
            phys_height_mm = total_roll_width
        else:
            phys_width_mm = total_roll_width
            phys_height_mm = label_height
            
        tspl.extend(f"SIZE {phys_width_mm} mm, {phys_height_mm} mm\r\n".encode('ascii'))
        tspl.extend(f"GAP {v_gap} mm, 0 mm\r\n".encode('ascii'))
        tspl.extend(f"DIRECTION {direction},0\r\n".encode('ascii'))
        
        # Map UI Offsets to Physical Offsets
        if portrait:
            phys_ref_x_dots = round(ref_y * dpi)
            phys_ref_y_dots = round(ref_x * dpi)
        else:
            phys_ref_x_dots = round(ref_x * dpi)
            phys_ref_y_dots = round(ref_y * dpi)
            
        tspl.extend(f"REFERENCE {phys_ref_x_dots},{phys_ref_y_dots}\r\n".encode('ascii'))
        tspl.extend(b"CLS\r\n")

        label_h_dots = round(label_height * dpi)

        # Prepare active elements list (replicate across columns if requested)
        if columns > 1 and duplicate_cols:
            active_elements = []
            for col in range(columns):
                col_shift = col * (label_width + h_gap)
                for el in elements:
                    cloned = copy.deepcopy(el)
                    cloned.x = el.x + col_shift
                    active_elements.append(cloned)
        else:
            active_elements = elements

        for el in active_elements:
            x_dots = round(el.x * dpi)
            y_dots = round(el.y * dpi)

            # Portrait mode: rotate content 90° clockwise so text reads correctly
            # when the label is held vertically.
            # Canvas (x,y) -> Physical (px, py)
            if portrait:
                px = label_h_dots - y_dots
                py = x_dots
                rot = 90
            else:
                px, py, rot = x_dots, y_dots, 0

            if el.type == 'text':
                lines = str(el.text).split('\n')
                line_spacing = max(24, el.font_size * 30)
                # In portrait mode, moving down the canvas = decreasing physical X.
                # In landscape mode, moving down the canvas = increasing physical Y.
                curr_px = px   # portrait: starts at label_h_dots - y_dots, decrements per line
                curr_py = py   # portrait: stays fixed (= x_dots); landscape: increments per line
                for line in lines:
                    font_to_use = el.font_type
                    is_chinese = False
                    if any('\u4e00' <= char <= '\u9fff' for char in line) and font_to_use in ['1', '2', '3', '4', '5', '6', '7', '8']:
                        font_to_use = "TSS24.BF2"
                        is_chinese = True
                    cmd_prefix = f'TEXT {curr_px},{curr_py},"{font_to_use}",{rot},{el.font_size},{el.font_size},"'
                    tspl.extend(cmd_prefix.encode('ascii'))
                    if is_chinese or font_to_use == "TSS24.BF2":
                        try:
                            tspl.extend(line.encode('gbk'))
                        except UnicodeEncodeError:
                            tspl.extend(line.encode('utf-8', errors='replace'))
                    else:
                        tspl.extend(line.encode('ascii', errors='replace'))
                    tspl.extend(b'"\r\n')
                    if portrait:
                        curr_px -= line_spacing   # step DOWN the portrait canvas (decreasing physical X)
                    else:
                        curr_py += line_spacing   # step DOWN the landscape canvas (increasing physical Y)
            elif el.type == 'barcode':
                tspl.extend(f'BARCODE {px},{py},"128",{el.height},1,{rot},2,4,"{el.data}"\r\n'.encode('ascii'))
            elif el.type == 'qrcode':
                cell_w = getattr(el, 'cell_width', 4)
                tspl.extend(f'QRCODE {px},{py},H,{cell_w},A,{rot},M2,S3,"{el.data}"\r\n'.encode('utf-8', errors='replace'))
            elif el.type == 'box':
                x2_dots = x_dots + round(el.width_mm * dpi)
                y2_dots = y_dots + round(el.height_mm * dpi)
                if portrait:
                    px1 = label_h_dots - y_dots
                    py1 = x_dots
                    px2 = label_h_dots - y2_dots
                    py2 = x2_dots
                    start_x = min(px1, px2)
                    end_x = max(px1, px2)
                    start_y = min(py1, py2)
                    end_y = max(py1, py2)
                else:
                    start_x = x_dots
                    start_y = y_dots
                    end_x = x2_dots
                    end_y = y2_dots
                t_dots = round(el.thickness * dpi)
                tspl.extend(f'BOX {start_x},{start_y},{end_x},{end_y},{t_dots}\r\n'.encode('ascii'))
            elif el.type == 'line':
                w_dots = round(el.width_mm * dpi)
                h_dots = round(el.height_mm * dpi)
                if portrait:
                    start_x = label_h_dots - y_dots - h_dots
                    start_y = x_dots
                    phys_w = h_dots
                    phys_h = w_dots
                else:
                    start_x = x_dots
                    start_y = y_dots
                    phys_w = w_dots
                    phys_h = h_dots
                tspl.extend(f'BAR {start_x},{start_y},{phys_w},{phys_h}\r\n'.encode('ascii'))
            elif el.type == 'circle':
                dia_dots = round(el.diameter_mm * dpi)
                t_dots = round(el.thickness * dpi)
                if portrait:
                    start_x = label_h_dots - y_dots - dia_dots
                    start_y = x_dots
                else:
                    start_x = x_dots
                    start_y = y_dots
                tspl.extend(f'CIRCLE {start_x},{start_y},{dia_dots},{t_dots}\r\n'.encode('ascii'))
            elif el.type == 'image':
                try:
                    from PIL import Image
                    img = Image.open(el.image_path)
                    
                    target_w_dots = int(el.width_mm * dpi)
                    target_h_dots = int(el.height_mm * dpi)
                    img = img.resize((target_w_dots, target_h_dots))
                    
                    if portrait:
                        img = img.rotate(-90, expand=True)
                        new_x_dots = label_h_dots - y_dots - target_h_dots
                        new_y_dots = x_dots
                        x_dots = new_x_dots
                        y_dots = new_y_dots
                        target_w_dots, target_h_dots = target_h_dots, target_w_dots
                    
                    # Handle negative coordinates by cropping the image
                    crop_left = 0
                    crop_top = 0
                    if x_dots < 0:
                        crop_left = -x_dots
                        x_dots = 0
                    if y_dots < 0:
                        crop_top = -y_dots
                        y_dots = 0
                        
                    if crop_left > 0 or crop_top > 0:
                        if crop_left >= target_w_dots or crop_top >= target_h_dots:
                            continue # Image is entirely off-screen
                        img = img.crop((crop_left, crop_top, target_w_dots, target_h_dots))
                        target_w_dots = img.width
                        target_h_dots = img.height

                    
                    # Handle transparency by creating a white background
                    if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
                        alpha = img.convert('RGBA').split()[-1]
                        bg = Image.new("RGBA", img.size, (255, 255, 255, 255))
                        bg.paste(img, mask=alpha)
                        img = bg.convert('RGB')
                    else:
                        img = img.convert('RGB')
                    
                    # Convert to grayscale
                    img = img.convert('L')
                    
                    width_bytes = (target_w_dots + 7) // 8
                    
                    raw_bytes = bytearray()
                    for cy in range(target_h_dots):
                        for x_byte in range(width_bytes):
                            b = int(0)
                            for bit in range(8):
                                cx = x_byte * 8 + bit
                                if cx < target_w_dots:
                                    pixel = img.getpixel((cx, cy))
                                    # We previously tested dark=1 and it printed inverted.
                                    # Therefore, this printer's firmware expects 1 for White (Off) and 0 for Black (On).
                                    # Or the image transparency alpha was originally inverted. Let's invert the check.
                                    if pixel > 128:
                                        b |= (1 << (7 - bit))
                            raw_bytes.append(b)
                    
                    tspl.extend(f'BITMAP {x_dots},{y_dots},{width_bytes},{target_h_dots},0,'.encode('ascii'))
                    tspl.extend(raw_bytes)
                    tspl.extend(b'\r\n')
                except Exception as e:
                    print(f"Error processing image {el.image_path}: {e}")

        tspl.extend(f"PRINT {copies},1\r\n".encode('ascii'))
        return tspl
