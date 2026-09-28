from PyQt6.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsRectItem, QGraphicsTextItem, QGraphicsEllipseItem, QGraphicsItem, QGraphicsPixmapItem
from PyQt6.QtCore import Qt, QRectF, pyqtSignal
from PyQt6.QtGui import QPen, QBrush, QColor, QPixmap, QImage
import barcode
from barcode.writer import ImageWriter
import io

class CanvasText(QGraphicsTextItem):
    def __init__(self, id, text, font_size, dpi_scale):
        super().__init__(text)
        self.element_id = id
        self.dpi_scale = dpi_scale
        self.setFlags(QGraphicsItem.GraphicsItemFlag.ItemIsMovable | QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self.setDefaultTextColor(QColor(0, 0, 0))
        font = self.font()
        font.setPointSize(max(9, int(font_size * 12))) 
        self.setFont(font)

    def set_pos_mm(self, x, y):
        self.setPos(x * self.dpi_scale, y * self.dpi_scale)

class CanvasBarcode(QGraphicsPixmapItem):
    def __init__(self, id, data, width_mm, height_mm, dpi_scale):
        super().__init__()
        self.element_id = id
        self.dpi_scale = dpi_scale
        self.width_mm = width_mm
        self.height_mm = height_mm
        self.setFlags(QGraphicsItem.GraphicsItemFlag.ItemIsMovable | QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self.update_barcode(data)

    def update_barcode(self, data):
        if not data: data = " "
        try:
            rv = io.BytesIO()
            CodeClass = barcode.get_barcode_class('code128')
            code = CodeClass(str(data), writer=ImageWriter())
            code.write(rv, options={"write_text": True, "module_width": 0.2, "module_height": 5, "quiet_zone": 1})
            rv.seek(0)
            
            image = QImage()
            image.loadFromData(rv.read())
            pixmap = QPixmap.fromImage(image)
            
            target_w = int(self.width_mm * self.dpi_scale)
            target_h = int(self.height_mm * self.dpi_scale)
            self.setPixmap(pixmap.scaled(target_w, target_h, Qt.AspectRatioMode.IgnoreAspectRatio))
        except Exception as e:
            print(f"Barcode error: {e}")

    def set_pos_mm(self, x, y):
        self.setPos(x * self.dpi_scale, y * self.dpi_scale)

class CanvasBox(QGraphicsRectItem):
    def __init__(self, id, width_mm, height_mm, dpi_scale):
        super().__init__(0, 0, width_mm * dpi_scale, height_mm * dpi_scale)
        self.element_id = id
        self.dpi_scale = dpi_scale
        self.setFlags(QGraphicsItem.GraphicsItemFlag.ItemIsMovable | QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self.setPen(QPen(Qt.GlobalColor.black, 2))

    def set_pos_mm(self, x, y):
        self.setPos(x * self.dpi_scale, y * self.dpi_scale)

class CanvasQR(QGraphicsPixmapItem):
    def __init__(self, id, data, dpi_scale):
        super().__init__()
        self.element_id = id
        self.dpi_scale = dpi_scale
        self.width_mm = 20
        self.height_mm = 20
        self.setFlags(QGraphicsItem.GraphicsItemFlag.ItemIsMovable | QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self.update_qr(data)

    def update_qr(self, data):
        if not data: data = " "
        try:
            import qrcode
            import io
            qr = qrcode.QRCode(version=1, box_size=10, border=1)
            qr.add_data(str(data))
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")
            
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            buf.seek(0)
            
            image = QImage()
            image.loadFromData(buf.read())
            pixmap = QPixmap.fromImage(image)
            
            target_w = int(self.width_mm * self.dpi_scale)
            target_h = int(self.height_mm * self.dpi_scale)
            self.setPixmap(pixmap.scaled(target_w, target_h, Qt.AspectRatioMode.KeepAspectRatio))
        except Exception as e:
            print(f"QR error: {e}")

    def set_pos_mm(self, x, y):
        self.setPos(x * self.dpi_scale, y * self.dpi_scale)
        
class CanvasLine(QGraphicsRectItem):
    def __init__(self, id, width_mm, height_mm, dpi_scale):
        super().__init__(0, 0, width_mm * dpi_scale, height_mm * dpi_scale)
        self.element_id = id
        self.dpi_scale = dpi_scale
        self.setFlags(QGraphicsItem.GraphicsItemFlag.ItemIsMovable | QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self.setBrush(QBrush(QColor(0, 0, 0)))

    def set_pos_mm(self, x, y):
        self.setPos(x * self.dpi_scale, y * self.dpi_scale)
        
class CanvasCircle(QGraphicsEllipseItem):
    def __init__(self, id, diameter_mm, dpi_scale):
        super().__init__(0, 0, diameter_mm * dpi_scale, diameter_mm * dpi_scale)
        self.element_id = id
        self.dpi_scale = dpi_scale
        self.setFlags(QGraphicsItem.GraphicsItemFlag.ItemIsMovable | QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self.setPen(QPen(Qt.GlobalColor.black, 2))

    def set_pos_mm(self, x, y):
        self.setPos(x * self.dpi_scale, y * self.dpi_scale)

class CanvasImage(QGraphicsPixmapItem):
    def __init__(self, id, image_path, width_mm, height_mm, dpi_scale):
        super().__init__()
        self.element_id = id
        self.image_path = image_path
        self.dpi_scale = dpi_scale
        self.width_mm = width_mm
        self.height_mm = height_mm
        self.setFlags(QGraphicsItem.GraphicsItemFlag.ItemIsMovable | QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self._is_resizing = False
        self.update_image()
        
    def update_image(self):
        try:
            pixmap = QPixmap(self.image_path)
            target_w = int(self.width_mm * self.dpi_scale)
            target_h = int(self.height_mm * self.dpi_scale)
            self.setPixmap(pixmap.scaled(target_w, target_h, Qt.AspectRatioMode.IgnoreAspectRatio))
        except Exception as e:
            print(f"Error loading canvas image: {e}")

    def set_pos_mm(self, x, y):
        self.setPos(x * self.dpi_scale, y * self.dpi_scale)
        
    def paint(self, painter, option, widget):
        super().paint(painter, option, widget)
        if self.isSelected():
            rect = self.boundingRect()
            painter.setBrush(QBrush(QColor('#58a6ff')))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRect(QRectF(rect.width() - 10, rect.height() - 10, 10, 10))
            
    def mousePressEvent(self, event):
        rect = self.boundingRect()
        handle_rect = QRectF(rect.width() - 15, rect.height() - 15, 15, 15)
        if handle_rect.contains(event.pos()):
            self._is_resizing = True
            event.accept()
        else:
            self._is_resizing = False
            super().mousePressEvent(event)
            
    def mouseMoveEvent(self, event):
        if self._is_resizing:
            new_w = max(5.0, event.pos().x() / self.dpi_scale)
            new_h = max(5.0, event.pos().y() / self.dpi_scale)
            self.width_mm = new_w
            self.height_mm = new_h
            self.update_image()
            if self.scene() and self.scene().views():
                view = self.scene().views()[0]
                if hasattr(view, 'elementResized'):
                    view.elementResized.emit(self.element_id, float(new_w), float(new_h))
        else:
            super().mouseMoveEvent(event)
            
    def mouseReleaseEvent(self, event):
        if self._is_resizing:
            self._is_resizing = False
        else:
            super().mouseReleaseEvent(event)

class LabelCanvas(QGraphicsView):
    elementSelected = pyqtSignal(str)
    elementMoved = pyqtSignal(str, float, float)
    elementResized = pyqtSignal(str, float, float)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        self.dpi_scale = 8  # 1mm = 8px
        self.snap_to_grid = True  # Snap elements to 1mm grid on release
        
        self.single_width_mm = 50.0
        self.single_height_mm = 15.0
        self.columns = 1
        self.h_gap_mm = 2.0
        self.v_gap_mm = 2.0
        self.auto_duplicate = True

        self.setBackgroundBrush(QBrush(QColor(13, 17, 23)))
        self.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)

    def set_label_size(self, width_mm, height_mm):
        self.set_label_layout(width_mm, height_mm, self.columns, self.h_gap_mm, self.v_gap_mm, self.auto_duplicate)

    def set_label_layout(self, width_mm, height_mm, columns=1, h_gap_mm=2.0, v_gap_mm=2.0, auto_duplicate=True):
        self.single_width_mm = float(width_mm)
        self.single_height_mm = float(height_mm)
        self.columns = max(1, int(columns))
        self.h_gap_mm = float(h_gap_mm)
        self.v_gap_mm = float(v_gap_mm)
        self.auto_duplicate = bool(auto_duplicate)

        total_w = (self.columns * self.single_width_mm) + ((self.columns - 1) * self.h_gap_mm)
        total_h = self.single_height_mm

        self.scene.setSceneRect(0, 0, total_w * self.dpi_scale, total_h * self.dpi_scale)
        self.setFixedSize(int(total_w * self.dpi_scale) + 12, int(total_h * self.dpi_scale) + 12)
        self.scene.update()
        self.viewport().update()

    def drawBackground(self, painter, rect):
        painter.save()
        # Viewport background
        painter.fillRect(rect, QColor(13, 17, 23))

        total_w_px = ((self.columns * self.single_width_mm) + ((self.columns - 1) * self.h_gap_mm)) * self.dpi_scale
        total_h_px = self.single_height_mm * self.dpi_scale

        # Draw each individual label column
        for col in range(self.columns):
            col_x = col * (self.single_width_mm + self.h_gap_mm) * self.dpi_scale
            col_w = self.single_width_mm * self.dpi_scale
            col_h = self.single_height_mm * self.dpi_scale

            # White label surface
            painter.setBrush(QBrush(QColor(255, 255, 255)))
            
            if self.columns > 1:
                # Slight border outline between labels
                pen = QPen(QColor(88, 166, 255) if col == 0 else QColor(48, 54, 61), 1)
                if col > 0 and self.auto_duplicate:
                    pen.setStyle(Qt.PenStyle.DashLine)
                painter.setPen(pen)
            else:
                painter.setPen(QPen(QColor(48, 54, 61), 1))

            painter.drawRoundedRect(QRectF(col_x, 0, col_w, col_h), 2, 2)

            # Label column indicator badge if multi-column
            if self.columns > 1:
                font = painter.font()
                font.setPixelSize(10)
                font.setBold(True)
                painter.setFont(font)
                
                badge_text = f"Col {col + 1}"
                if col > 0 and self.auto_duplicate:
                    badge_text += " (Auto-Copy)"
                    painter.setPen(QColor(139, 148, 158, 180))
                else:
                    painter.setPen(QColor(31, 111, 235, 200))
                    
                painter.drawText(QRectF(col_x + 4, 4, col_w - 8, 16), Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop, badge_text)

        painter.restore()

    def add_text(self, id, text, x, y, font_size):
        item = CanvasText(id, text, font_size, self.dpi_scale)
        item.set_pos_mm(x, y)
        self.scene.addItem(item)
        return item

    def add_barcode(self, id, data, x, y, height):
        # Default mock width for barcode is 30mm
        item = CanvasBarcode(id, data, 30, height, self.dpi_scale)
        item.set_pos_mm(x, y)
        self.scene.addItem(item)
        return item

    def add_qrcode(self, id, data, x, y):
        item = CanvasQR(id, data, self.dpi_scale)
        item.set_pos_mm(x, y)
        self.scene.addItem(item)
        return item

    def add_box(self, id, width, height, x, y):
        item = CanvasBox(id, width, height, self.dpi_scale)
        item.set_pos_mm(x, y)
        self.scene.addItem(item)
        return item

    def add_line(self, id, width, height, x, y):
        item = CanvasLine(id, width, height, self.dpi_scale)
        item.set_pos_mm(x, y)
        self.scene.addItem(item)
        return item

    def add_circle(self, id, diameter, x, y):
        item = CanvasCircle(id, diameter, self.dpi_scale)
        item.set_pos_mm(x, y)
        self.scene.addItem(item)
        return item
        
    def add_image(self, id, image_path, width, height, x, y):
        item = CanvasImage(id, image_path, width, height, self.dpi_scale)
        item.set_pos_mm(x, y)
        self.scene.addItem(item)
        return item

    def mousePressEvent(self, event):
        item = self.itemAt(event.pos())
        if item and hasattr(item, 'element_id'):
            self.elementSelected.emit(item.element_id)
        else:
            self.elementSelected.emit("")
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        item = self.itemAt(event.pos())
        if item and hasattr(item, 'element_id'):
            pos = item.pos()
            x_px = pos.x()
            y_px = pos.y()
            if self.snap_to_grid:
                # Snap to nearest 1mm grid unit
                x_px = round(x_px / self.dpi_scale) * self.dpi_scale
                y_px = round(y_px / self.dpi_scale) * self.dpi_scale
                item.setPos(x_px, y_px)
            self.elementMoved.emit(item.element_id, x_px / self.dpi_scale, y_px / self.dpi_scale)

    def update_item_data(self, id, el_model):
        for item in self.scene.items():
            if hasattr(item, 'element_id') and item.element_id == id:
                if isinstance(item, CanvasText):
                    item.setPlainText(str(el_model.text))
                    item.setDefaultTextColor(QColor(0, 0, 0))
                    font = item.font()
                    # A basic TSPL font (24 dots) at 8 dots/mm is 3mm tall = 24 scene pixels.
                    font.setPixelSize(max(12, int(24 * el_model.font_size)))
                    item.setFont(font)
                elif isinstance(item, CanvasBarcode):
                    item.height_mm = el_model.height / 8.0  # dots → approx mm for canvas preview
                    item.width_mm = getattr(el_model, 'width_mm', 30)
                    item.update_barcode(str(el_model.data))
                elif isinstance(item, CanvasQR):
                    item.update_qr(str(el_model.data))
                elif isinstance(item, CanvasBox):
                    item.setRect(0, 0, el_model.width_mm * self.dpi_scale, el_model.height_mm * self.dpi_scale)
                elif isinstance(item, CanvasLine):
                    item.setRect(0, 0, el_model.width_mm * self.dpi_scale, el_model.height_mm * self.dpi_scale)
                elif isinstance(item, CanvasCircle):
                    item.setRect(0, 0, el_model.diameter_mm * self.dpi_scale, el_model.diameter_mm * self.dpi_scale)
                elif isinstance(item, CanvasImage):
                    item.width_mm = el_model.width_mm
                    item.height_mm = el_model.height_mm
                    item.update_image()
                item.set_pos_mm(el_model.x, el_model.y)
                return

    def remove_item(self, id):
        for item in self.scene.items():
            if hasattr(item, 'element_id') and item.element_id == id:
                self.scene.removeItem(item)
                return
