import sys
import os
import re
import json
import shutil
import base64
import traceback
from pathlib import Path
from typing import List, Dict, Optional, Any, Tuple
from collections import defaultdict

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QListWidget, QListWidgetItem, QGraphicsView, QGraphicsScene,
    QGraphicsTextItem, QFileDialog, QLabel,
    QLineEdit, QMenu, QMessageBox, QPushButton, QFrame,
    QScrollArea, QDialog, QSplitter, QTreeWidget, QTreeWidgetItem,
    QTableWidget, QTableWidgetItem, QColorDialog, QComboBox,
    QSizePolicy, QSpacerItem
)
from PySide6.QtGui import (
    QColor, QPen, QPixmap, QPainter, QFont, QBrush, QKeySequence
)
from PySide6.QtCore import (
    Qt, QRectF, QPointF, QSize, QDir, Signal, QPoint, QSizeF,
)
from PySide6.QtWidgets import QGraphicsObject

class AppConstants:
    WIDGET_TYPE_COLORS = {
        "UILabel": QColor(60, 60, 70, 220), "UIButton": QColor(80, 40, 80, 220),
        "UIImage": QColor(60, 60, 60, 180), "UIWindow": QColor(40, 40, 70, 220),
        "UIWidget": QColor(50, 50, 50, 220), "OptionCheckBox": QColor(60, 80, 70, 220),
        "OptionScrollbar": QColor(80, 60, 70, 220), "ComboBox": QColor(70, 70, 80, 220),
        "UICreature": QColor(60, 80, 80, 220), "UIItem": QColor(80, 60, 80, 220),
        "UIScrollBar": QColor(200, 200, 100, 220), "ScrollablePanel": QColor(70, 80, 70, 220),
        "UITextEdit": QColor(65, 65, 80, 220), "DialogText": QColor(60, 70, 80, 220),
        "Label": QColor(60, 60, 70, 220), "TextEdit": QColor(65, 65, 80, 220), "Panel": QColor(50, 50, 50, 220),
        "Item": QColor(80, 60, 80, 220), "Button": QColor(80, 40, 80, 220),
        "HorizontalScrollBar": QColor(255, 255, 127), "VerticalScrollBar": QColor(255, 255, 127),
        "PageButton": QColor(255, 0, 255), "LockerContainerWindow": QColor(0, 255, 255),
        "ContainerWindow": QColor(0, 255, 255),
    }

    WIDGET_NEON_COLORS = {
        "UILabel": QColor(0, 170, 255), "UIButton": QColor(255, 0, 255),
        "UIImage": QColor(0, 255, 127), "UIWindow": QColor(0, 255, 255),
        "UIWidget": QColor(150, 150, 150, 255), "OptionCheckBox": QColor(127, 255, 127),
        "OptionScrollbar": QColor(255, 127, 127), "ComboBox": QColor(255, 255, 0),
        "UICreature": QColor(127, 255, 255), "UIItem": QColor(255, 127, 255),
        "UIScrollBar": QColor(255, 255, 127), "ScrollablePanel": QColor(127, 255, 127),
        "UITextEdit": QColor(200, 200, 255),
        "Label": QColor(0, 170, 255), "TextEdit": QColor(200, 200, 255), "Panel": QColor(150, 150, 150, 255),
        "Item": QColor(255, 127, 255), "Button": QColor(255, 0, 255),
        "HorizontalScrollBar": QColor(255, 255, 127), "VerticalScrollBar": QColor(255, 255, 127),
        "PageButton": QColor(255, 0, 255), "LockerContainerWindow": QColor(0, 255, 255),
        "ContainerWindow": QColor(0, 255, 255),
    }

    KNOWN_PROPERTIES = {
        "id": "", "pos": "0 0", "size": "100 50", "anchors.fill": "parent",
        "anchors.horizontalCenter": "parent", "anchors.verticalCenter": "parent",
        "anchors.top": "parent.top", "anchors.bottom": "parent.bottom",
        "anchors.left": "parent.left", "anchors.right": "parent.right",
        "margin-top": "0", "margin-bottom": "0", "margin-left": "0", "margin-right": "0",
        "padding": "0", "layout": "vertical", "layout-spacing": "5", "layout-align": "center",
        "visible": "true", "opacity": "1.0", "rotation": "0", "background-color": "#FFFFFF00",
        "enabled": "true", "focusable": "true", "draggable": "false", "phantom": "false",
        "!tooltip": "Dica...", "image-source": "", "image-color": "#FFFFFFFF", "image-clip": "0 0 32 32",
        "image-offset": "0 0", "image-border": "0", "image-auto-resize": "false",
        "image-fixed-ratio": "false", "image-smooth": "true", "image-repeated": "false",
        "icon-source": "", "icon-clip": "0 0 16 16", "icon-offset": "0 0", "icon-color": "#FFFFFFFF",
        "text": "Texto", "color": "#FFFFFF", "font": "verdana-11px-rounded",
        "text-auto-resize": "false", "text-align": "center", "text-offset": "0 0", "text-wrap": "false",
        "selection-color": "#3399FF88", "cursor-image": "",
    }
    
    HANDLE_SIZE = 8
    HEADER_HEIGHT = 18
    (P_TOP_LEFT, P_TOP, P_TOP_RIGHT, P_LEFT, P_RIGHT,
     P_BOTTOM_LEFT, P_BOTTOM, P_BOTTOM_RIGHT, P_NONE) = range(9)


def read_text_with_fallback(path: Path) -> str:
    try:
        return path.read_text(encoding='utf-8')
    except UnicodeDecodeError:
        return path.read_text(encoding='latin-1', errors='ignore')

def to_int(val: Any, default: int = 0) -> int:
    if val is None:
        return default
    try:
        return int(float(str(val)))
    except (ValueError, TypeError):
        return default

def is_valid_otui_file(path: Path) -> bool:
    return path.suffix.lower() in ('.otui', '.otmd')

def parse_padding(padding_str: str) -> List[int]:
    p_parts = [to_int(p) for p in padding_str.split()]
    padding = [0, 0, 0, 0]
    if len(p_parts) == 1: padding = p_parts * 4
    elif len(p_parts) == 2: padding = [p_parts[0], p_parts[1], p_parts[0], p_parts[1]]
    elif len(p_parts) == 4: padding = p_parts
    return padding

class ResourceResolver:
    def __init__(self, data_roots: List[Path], search_paths: List[Path]):
        self.data_roots = [p.resolve() for p in data_roots if p]
        self.search_paths = [p.resolve() for p in search_paths if p]
        self._cache: Dict[str, Optional[str]] = {}

    def resolve(self, path_str: str, hint_dir: Optional[Path] = None) -> Optional[str]:
        if not path_str or path_str.lower() == 'none' or path_str.startswith('base64:'):
            return path_str
        
        if path_str in self._cache:
            return self._cache[path_str]

        path_str = path_str.strip().replace('\\', '/')
        candidates = []

        if Path(path_str).is_absolute():
            candidates.append(Path(path_str))
        elif path_str.startswith('/'):
            candidates.extend([root / path_str[1:] for root in self.data_roots])
        else:
            if hint_dir:
                candidates.append(hint_dir.resolve() / path_str)
            candidates.extend([sp / path_str for sp in self.search_paths])
            candidates.extend([root / path_str for root in self.data_roots])

        for c in candidates:
            try:
                if c.exists():
                    resolved = str(c.resolve())
                    self._cache[path_str] = resolved
                    return resolved
            except (OSError, ValueError):
                continue
        
        self._cache[path_str] = None
        return None

class ModuleProject:
    STATE_FILE = ".otui_editor_state.json"

    def __init__(self, folder: str):
        self.root = Path(folder).resolve()
        self.mod_data: Dict[str, Any] = {}
        self.otmod_file: Optional[Path] = None
        self._parse_otmod()

        self.data_roots: List[Path] = [self.root]
        if (self.root / 'data').is_dir():
            self.data_roots.append(self.root / 'data')

        self.otui_files: List[Path] = []
        self.lua_files: List[Path] = []
        self.image_dirs: List[Path] = []
        self.extra_search_paths: List[Path] = []
        self.index_structure()

        all_search_paths = list(set(self.image_dirs + self.extra_search_paths + list(self.root.glob('**/images'))))
        
        self.resolver = ResourceResolver(self.data_roots, all_search_paths)
        self.state_path = self.root / self.STATE_FILE
        self.last_state: Dict = self._load_state()
        self.initial_otui: Optional[Path] = self._guess_initial_otui()
        self.is_changed = False

    def _parse_otmod(self):
        try:
            otmod_files = list(self.root.glob('*.otmod'))
            if not otmod_files:
                return
            self.otmod_file = otmod_files[0]
            
            lines = read_text_with_fallback(self.otmod_file).splitlines()
            in_onload = False
            for line in lines:
                stripped = line.strip()
                if not stripped or stripped.startswith('#'):
                    continue
                if stripped == '@onLoad':
                    in_onload = True
                    continue
                elif not line.startswith((' ', '\t')):
                    in_onload = False

                key_val_match = re.match(r'^\s*([^:]+):\s*(.*)', stripped)
                if not key_val_match:
                    continue

                key, value = key_val_match.groups()
                if in_onload:
                    if key == 'images-dir':
                        paths = [p.strip().strip("'\"") for p in re.split(r',\s*(?![^\[]*\])', value.strip('[] '))]
                        self.mod_data.setdefault('images-dir', []).extend(paths)
                else:
                    self.mod_data[key] = value
        except Exception:
            pass 

    def index_structure(self):
        otui_files_set = set()
        lua_files_set = set()
        image_dirs_set = set(self.image_dirs)
        extra_search_paths_set = set()
        walk_roots = list(set([self.root] + self.data_roots))

        for base in walk_roots:
            for p in base.rglob('*'):
                if p.is_file():
                    if p.suffix.lower() in ('.otui', '.otmd'):
                        otui_files_set.add(p)
                    elif p.suffix.lower() == '.lua':
                        lua_files_set.add(p)
                elif p.is_dir():
                    if p.name.lower() in ('images', 'imgs', 'icons', 'textures'):
                        image_dirs_set.add(p)
                    if p.name.lower() in ('styles', 'layouts', 'ui', 'modules'):
                        extra_search_paths_set.add(p)

        self.otui_files = sorted(list(otui_files_set))
        self.lua_files = sorted(list(lua_files_set))
        self.image_dirs = sorted(list(image_dirs_set))
        self.extra_search_paths = sorted(list(extra_search_paths_set))

    def _guess_initial_otui(self) -> Optional[Path]:
        if self.last_state and self.last_state.get('current_otui'):
            p = Path(self.last_state['current_otui'])
            if p.exists():
                return p

        pattern = re.compile(r"g_ui\.(?:loadUI|displayUI)\s*\(\s*['\"]([^'\"]+)['\"]", re.IGNORECASE)
        names: List[str] = []
        for lua in self.lua_files:
            try:
                txt = read_text_with_fallback(lua)
                for m in pattern.finditer(txt):
                    ui_name = m.group(1).strip()
                    if ui_name and ui_name not in names:
                        names.append(ui_name)
            except Exception:
                continue

        for nm in names:
            base = nm if nm.lower().endswith(('.otui', '.otmd')) else f"{nm}.otui"
            for f in self.otui_files:
                if f.name.lower() == base.lower():
                    return f
        
        return self.otui_files[0] if self.otui_files else None

    def _load_state(self) -> Dict:
        if self.state_path.exists():
            try:
                return json.loads(self.state_path.read_text(encoding='utf-8'))
            except Exception:
                return {}
        return {}

    def save_state(self, data: Dict):
        try:
            cur = self._load_state() or {}
            cur.update(data)
            self.state_path.write_text(json.dumps(cur, ensure_ascii=False, indent=2), encoding='utf-8')
            self.last_state = cur
        except Exception:
            pass

class History:
    def __init__(self):
        self.stack: List[Any] = []
        self.index = -1

    def push(self, state: Any):
        if not state:
            return
        if self.index > -1 and self.stack[self.index] == state:
            return
        
        self.stack = self.stack[:self.index + 1]
        self.stack.append(state)
        self.index = len(self.stack) - 1

    def undo(self) -> Optional[Any]:
        if self.index > 0:
            self.index -= 1
            return self.stack[self.index]
        return None

    def redo(self) -> Optional[Any]:
        if self.index + 1 < len(self.stack):
            self.index += 1
            return self.stack[self.index]
        return None

class WidgetItem(QGraphicsObject):
    geometry_changed = Signal()
    HANDLE_SIZE = AppConstants.HANDLE_SIZE
    HEADER_HEIGHT = AppConstants.HEADER_HEIGHT
    (P_TOP_LEFT, P_TOP, P_TOP_RIGHT, P_LEFT, P_RIGHT,
     P_BOTTOM_LEFT, P_BOTTOM, P_BOTTOM_RIGHT, P_NONE) = (
        AppConstants.P_TOP_LEFT, AppConstants.P_TOP, AppConstants.P_TOP_RIGHT, AppConstants.P_LEFT, AppConstants.P_RIGHT,
        AppConstants.P_BOTTOM_LEFT, AppConstants.P_BOTTOM, AppConstants.P_BOTTOM_RIGHT, AppConstants.P_NONE
    )

    def __init__(self, widget_type: str = "UILabel", name: Optional[str] = None, x: float = 0, y: float = 0, width: float = 100, height: float = 50, parent_widget: Optional['WidgetItem'] = None):
        super().__init__()

        self._rect = QRectF(0, 0, width, height)
        self.setPos(x, y)
        self.hint_dir: Optional[Path] = None

        self.widget_type = widget_type
        self.name = name if name else widget_type
        self.parent_widget: Optional['WidgetItem'] = parent_widget
        self.children_widgets: List['WidgetItem'] = []
        
        self.otui_props: Dict[str, Any] = {
            'props': defaultdict(str),
            'states': defaultdict(str),
            'events': defaultdict(str),
            'functions': defaultdict(str),
            'inherit': None
        }
        self.pixmap: Optional[QPixmap] = None
        self.icon_pixmap: Optional[QPixmap] = None
        
        self.text_item = QGraphicsTextItem(self.name, self)
        self.text_item.setDefaultTextColor(AppConstants.WIDGET_NEON_COLORS.get(widget_type, QColor(220, 220, 220)))
        font = QFont("Consolas", 10)
        font.setBold(True)
        self.text_item.setFont(font)

        self.setFlag(QGraphicsObject.ItemIsSelectable, True)
        self.setFlag(QGraphicsObject.ItemSendsGeometryChanges, True)
        self.setAcceptHoverEvents(True)
        self._check_layout_constraints()

        self.active_handle: int = self.P_NONE
        self.start_pos = QPointF()
        self.original_scene_rect = QRectF()
        self.handles: Dict[int, QRectF] = {}
        self.update_handles()
        self.update_text_position()
        self.geometry_changed.connect(self.apply_layout)
        
        self.otui_props['props']['id'] = self.name
        
        # Define a posição OTUI inicial como a posição relativa real
        relative_pos = self.pos()
        if parent_widget:
            # Converte a posição absoluta inicial do item para a posição relativa ao parent
            relative_pos = self.mapToParent(QPointF(0, 0)) # Posição do item relativa ao pai
        self.otui_props['props']['pos'] = f"{int(relative_pos.x())} {int(relative_pos.y())}"

        self.otui_props['props']['size'] = f"{int(width)} {int(height)}"

    def boundingRect(self) -> QRectF:
        return self._rect

    def rect(self) -> QRectF:
        return self.boundingRect()

    def set_rect(self, x: float, y: float, w: float, h: float):
        self.prepareGeometryChange()
        self._rect = QRectF(x, y, w, h)
        self.update_handles()
        self.update()

    def update_text_position(self):
        if not self.text_item: return
        props = self.otui_props.get('props', {})
        self.text_item.setPlainText(props.get('text', self.name))
        self.text_item.setTextWidth(self.rect().width() if props.get('text-wrap') == 'true' else -1)

        text_rect = self.text_item.boundingRect()
        widget_rect = self.rect()
        align = props.get('text-align', 'center')
        
        padding = parse_padding(props.get('padding', '0'))

        offset_x, offset_y = 0, 0
        if 'text-offset' in props:
            try:
                offset_x, offset_y = map(lambda x: to_int(x), props['text-offset'].split())
            except (ValueError, TypeError): pass

        valign = props.get('text-vertical-align', 'center')
        y = 0
        if valign == 'top': y = padding[0] + offset_y
        elif valign == 'bottom': y = widget_rect.height() - text_rect.height() - padding[2] + offset_y
        else: y = (widget_rect.height() - text_rect.height()) / 2 + offset_y

        x = 0
        if align == 'left': x = padding[3] + offset_x
        elif align == 'right': x = widget_rect.width() - text_rect.width() - padding[1] + offset_x
        else: x = (widget_rect.width() - text_rect.width()) / 2 + offset_x

        self.text_item.setPos(x, y)

    def set_image(self, source: str, is_icon: bool = False):
        pixmap_target = 'pixmap' if not is_icon else 'icon_pixmap'
        pix: Optional[QPixmap] = None
        
        if source and source.lower() != 'none':
            editor = self.scene().views()[0].owner_editor if self.scene() and self.scene().views() else None
            resolver = editor.current_project.resolver if editor and editor.current_project else None
            resolved_path = resolver.resolve(source, self.hint_dir) if resolver else source
            
            if resolved_path and resolved_path.lower() != 'none':
                try:
                    if resolved_path.startswith('base64:'):
                        img_data = base64.b64decode(resolved_path.split('base64:', 1)[1])
                        pix = QPixmap()
                        pix.loadFromData(img_data)
                    elif os.path.exists(resolved_path):
                        pix = QPixmap(resolved_path)
                    
                    if pix and pix.isNull():
                        pix = None
                except Exception:
                    pix = None
        
        setattr(self, pixmap_target, pix)
        self.update()

    def update_handles(self):
        w, h = self.rect().width(), self.rect().height()
        s = self.HANDLE_SIZE
        self.handles = {
            self.P_TOP_LEFT: QRectF(0, 0, s, s), self.P_TOP: QRectF(w/2 - s/2, 0, s, s),
            self.P_TOP_RIGHT: QRectF(w - s, 0, s, s), self.P_LEFT: QRectF(0, h/2 - s/2, s, s),
            self.P_RIGHT: QRectF(w - s, h/2 - s/2, s, s), self.P_BOTTOM_LEFT: QRectF(0, h - s, s, s),
            self.P_BOTTOM: QRectF(w/2 - s/2, h - s, s, s), self.P_BOTTOM_RIGHT: QRectF(w - s, h - s, s, s)
        }

    def paint(self, painter: QPainter, option: Any, widget: Any):
        painter.setRenderHint(QPainter.Antialiasing)
        props = self.otui_props.get('props', {})
        opacity = float(props.get('opacity', 1.0))
        painter.setOpacity(opacity)
        
        rotation = float(props.get('rotation', 0.0))
        if rotation != 0.0:
            self.setTransformOriginPoint(self.boundingRect().center())
            self.setRotation(rotation)
        else:
            self.setRotation(0)

        if props.get('phantom') == 'true':
            painter.setPen(QPen(QColor(150, 150, 200, 150), 2, Qt.DashLine))
            painter.setBrush(Qt.NoBrush)
            painter.drawRect(self.boundingRect())
        else:
            bg_color_str = props.get('background-color')
            background_color = AppConstants.WIDGET_TYPE_COLORS.get(self.widget_type, QColor(80, 80, 80, 200))
            if bg_color_str and QColor.isValidColor(bg_color_str):
                background_color = QColor(bg_color_str)
                if len(bg_color_str) == 7:
                    color_no_alpha = QColor(bg_color_str)
                    color_no_alpha.setAlpha(255)
                    background_color = color_no_alpha
                
            painter.setBrush(background_color)
            painter.setPen(QPen(Qt.black, 1))
            painter.drawRect(self.boundingRect())

        self._draw_image_base(painter, is_icon=False)
        self._draw_image_base(painter, is_icon=True)

        if self.widget_type == "UIWindow":
            header_color = AppConstants.WIDGET_NEON_COLORS.get(self.widget_type, QColor(0, 255, 255))
            painter.setBrush(QBrush(header_color, Qt.Dense6Pattern))
            painter.setPen(QPen(Qt.black, 1))
            painter.drawRect(self.boundingRect().x(), self.boundingRect().y(), self.boundingRect().width(), self.HEADER_HEIGHT)
            self.text_item.setPos(5, 1)
        
        if self.isSelected():
            pen = QPen(AppConstants.WIDGET_NEON_COLORS.get(self.widget_type, QColor(0, 255, 127)), 2, Qt.DashLine)
            painter.setPen(pen)
            painter.setBrush(Qt.NoBrush)
            painter.drawRect(self.boundingRect())
            
            if self.flags() & QGraphicsObject.ItemIsMovable:
                painter.setBrush(QColor(0, 255, 127, 80))
                for h in self.handles.values():
                    painter.drawRect(h)

        if self.widget_type != "UIWindow":
            self.update_text_position()

    def _draw_image_base(self, painter: QPainter, is_icon: bool):
        pixmap = self.icon_pixmap if is_icon else self.pixmap
        if not pixmap or pixmap.isNull():
            return
        
        props = self.otui_props.get('props', {})
        prefix = 'icon' if is_icon else 'image'
        border_str = props.get(f'{prefix}-border')

        if border_str and not is_icon:
            try:
                borders = parse_padding(border_str)
                if len(borders) == 4:
                    self._draw_nine_slice(painter, pixmap, self.rect(), borders)
                    return
            except (ValueError, TypeError): pass  

        widget_rect = self.rect()
        source_rect = QRectF(pixmap.rect())
        if f'{prefix}-clip' in props:
            try:
                x, y, w, h = map(lambda x: to_int(x), props[f'{prefix}-clip'].split())
                source_rect = QRectF(x, y, w, h)
            except (ValueError, TypeError): pass
        
        if props.get(f'{prefix}-repeated') == 'true':
            painter.drawTiledPixmap(widget_rect, pixmap, source_rect.topLeft())
        else:
            target_size = QSizeF(widget_rect.size())
            if props.get(f'{prefix}-fixed-ratio') == 'true' and source_rect.width() > 0 and source_rect.height() > 0:
                target_size = widget_rect.size().scaled(source_rect.size(), Qt.KeepAspectRatio)

            target_rect = QRectF(QPointF(0, 0), target_size)
            target_rect.moveCenter(widget_rect.center())

            if f'{prefix}-offset' in props:
                try:
                    ox, oy = map(lambda x: to_int(x), props[f'{prefix}-offset'].split())
                    target_rect.translate(ox, oy)
                except (ValueError, TypeError): pass
            
            if f'{prefix}-color' in props:
                color_str = props[f'{prefix}-color']
                if QColor.isValidColor(color_str):
                    color_tint = QColor(color_str)
                    if color_tint.alpha() < 255 or color_tint.red() != 255 or color_tint.green() != 255 or color_tint.blue() != 255:
                        temp_pix = QPixmap(pixmap.size())
                        temp_pix.fill(Qt.transparent)
                        
                        temp_painter = QPainter(temp_pix)
                        temp_painter.setOpacity(pixmap.depth() > 1)
                        temp_painter.drawPixmap(0, 0, pixmap)
                        
                        temp_painter.setCompositionMode(QPainter.CompositionMode_SourceAtop)
                        temp_painter.fillRect(temp_pix.rect(), color_tint)
                        temp_painter.end()
                        
                        painter.drawPixmap(target_rect, temp_pix, source_rect)
                        return
            
            painter.drawPixmap(target_rect, pixmap, source_rect)

    def _draw_nine_slice(self, painter: QPainter, pixmap: QPixmap, target_rect: QRectF, borders: List[int]):
        top, right, bottom, left = borders
        pm_w, pm_h = pixmap.width(), pixmap.height()
        
        if left + right > pm_w or top + bottom > pm_h:
            painter.drawPixmap(target_rect, pixmap)
            return

        src_x = [0, left, pm_w - right, pm_w]
        src_y = [0, top, pm_h - bottom, pm_h]
        tgt_x = [target_rect.left(), target_rect.left() + left, target_rect.right() - right, target_rect.right()]
        tgt_y = [target_rect.top(), target_rect.top() + top, target_rect.bottom() - bottom, target_rect.bottom()]
        
        for row in range(3):
            for col in range(3):
                src = QRectF(QPointF(src_x[col], src_y[row]), QPointF(src_x[col+1], src_y[row+1]))
                tgt = QRectF(QPointF(tgt_x[col], tgt_y[row]), QPointF(tgt_x[col+1], tgt_y[row+1]))
                
                if src.isValid() and tgt.isValid():
                    painter.drawPixmap(tgt, pixmap, src)
    
    def hoverMoveEvent(self, event: Any):
        if not self.isSelected():
            self.setCursor(Qt.ArrowCursor)
            return
            
        handle = self.get_handle_at_pos(event.pos())
        
        if self.flags() & QGraphicsObject.ItemIsMovable:
            if self.active_handle == self.P_NONE or handle != self.P_NONE:
                cursor = Qt.ArrowCursor
                if handle in (self.P_TOP_LEFT, self.P_BOTTOM_RIGHT): cursor = Qt.SizeFDiagCursor
                elif handle in (self.P_TOP_RIGHT, self.P_BOTTOM_LEFT): cursor = Qt.SizeBDiagCursor
                elif handle in (self.P_TOP, self.P_BOTTOM): cursor = Qt.SizeVerCursor
                elif handle in (self.P_LEFT, self.P_RIGHT): cursor = Qt.SizeHorCursor
                self.setCursor(cursor)
        super().hoverMoveEvent(event)

    def mousePressEvent(self, event: Any):
        if event.button() == Qt.LeftButton:
            if self.flags() & QGraphicsObject.ItemIsMovable:
                self.active_handle = self.get_handle_at_pos(event.pos())
                if self.active_handle != self.P_NONE:
                    self.start_pos = event.scenePos()
                    self.original_scene_rect = self.mapToScene(self.boundingRect()).boundingRect()
                    self.setFlag(QGraphicsObject.ItemIsMovable, False)
                    event.accept()
                    return
            
            if event.modifiers() & Qt.ControlModifier:
                self.setSelected(not self.isSelected())
                event.accept()

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: Any):
        if self.active_handle != self.P_NONE:
            self.prepareGeometryChange()
            new_scene_rect = QRectF(self.original_scene_rect)
            delta = event.scenePos() - self.start_pos
            
            # Recálculo das dimensões baseado no handle ativo
            if self.active_handle in (self.P_TOP_LEFT, self.P_LEFT, self.P_BOTTOM_LEFT):
                new_scene_rect.setLeft(self.original_scene_rect.left() + delta.x())
            if self.active_handle in (self.P_TOP_LEFT, self.P_TOP, self.P_TOP_RIGHT):
                new_scene_rect.setTop(self.original_scene_rect.top() + delta.y())
            if self.active_handle in (self.P_TOP_RIGHT, self.P_RIGHT, self.P_BOTTOM_RIGHT):
                new_scene_rect.setRight(self.original_scene_rect.right() + delta.x())
            if self.active_handle in (self.P_BOTTOM_LEFT, self.P_BOTTOM, self.P_BOTTOM_RIGHT):
                new_scene_rect.setBottom(self.original_scene_rect.bottom() + delta.y())
            
            new_scene_rect = new_scene_rect.normalized()
            if new_scene_rect.width() < self.HANDLE_SIZE * 2 or new_scene_rect.height() < self.HANDLE_SIZE * 2:
                return

            # Atualiza posição e dimensão na cena
            self.setPos(self.mapFromScene(new_scene_rect.topLeft()))
            self.set_rect(0, 0, new_scene_rect.width(), new_scene_rect.height())
            
            # Atualiza OTUI props: POS
            relative_pos = self.pos() if not self.parentItem() else self.mapToParent(QPointF(0, 0))
            self.otui_props['props']['pos'] = f"{int(relative_pos.x())} {int(relative_pos.y())}"
            
            # Atualiza OTUI props: SIZE
            self.otui_props['props']['size'] = f"{int(self.rect().width())} {int(self.rect().height())}"
            self.update_handles()
            
            if self.scene() and self.scene().views():
                self.scene().views()[0].owner_editor.props_editor.update_realtime_props()
            self.geometry_changed.emit()
        else:
            super().mouseMoveEvent(event)

    def itemChange(self, change: QGraphicsObject.GraphicsItemChange, value: Any) -> Any:
        if change == QGraphicsObject.ItemPositionHasChanged and self.scene():
            if self.scene() and self.scene().views():
                view: 'Canvas' = self.scene().views()[0]
                view.owner_editor.update_status_bar(f"Widget '{self.name}' movido para: ({int(value.x())}, {int(value.y())})")
                
                # Posição é sempre a coordenada local/relativa ao pai
                relative_pos = value
                self.otui_props['props']['pos'] = f"{int(relative_pos.x())} {int(relative_pos.y())}"
                
                if view.owner_editor.props_editor.active_widget == self:
                    view.owner_editor.props_editor.update_realtime_props()
                self.geometry_changed.emit()
        return super().itemChange(change, value)

    def mouseReleaseEvent(self, event: Any):
        if self.active_handle != self.P_NONE:
            self.active_handle = self.P_NONE
            self.setFlag(QGraphicsObject.ItemIsMovable, True)
            self._check_layout_constraints()
            if self.scene() and self.scene().views():
                self.scene().views()[0].save_state()
        
        self._check_layout_constraints()
        super().mouseReleaseEvent(event)

    def get_handle_at_pos(self, pos: QPointF) -> int:
        for handle_id, rect in self.handles.items():
            if rect.contains(pos):
                return handle_id
        return self.P_NONE

    def mouseDoubleClickEvent(self, event: Any):
        if self.widget_type in ("UIImage", "UILabel", "UIButton", "UIWindow", "UIWidget"):
            if not self.scene() or not self.scene().views(): return
            editor: 'OTUIEditor' = self.scene().views()[0].owner_editor
            if not editor.current_project:
                QMessageBox.warning(editor, "Aviso", "Abra um projeto para navegar pelas imagens.")
                return
            dialog = ImageSourceBrowser(editor.current_project, editor)
            if dialog.exec() == QDialog.Accepted and dialog.selected_path:
                editor.handle_image_update(self, 'image-source', dialog.selected_path)
        super().mouseDoubleClickEvent(event)
    
    def update_name(self, new_name: str):
        self.name = new_name
        if self.otui_props['props'].get('text') is None or self.otui_props['props'].get('text') == "":
            self.text_item.setPlainText(self.name)
        self.update_text_position()

    def contextMenuEvent(self, event: Any):
        menu = QMenu()
        view: 'Canvas' = self.scene().views()[0]

        bring_action = menu.addAction("Trazer para Frente")
        send_action = menu.addAction("Enviar para Trás")
        menu.addSeparator()
        duplicate_action = menu.addAction("Duplicar Widget")
        delete_action = menu.addAction("Excluir Widget")
        
        layout_menu = menu.addMenu("Layout")
        set_vertical_layout = layout_menu.addAction("Setar Layout Vertical")
        set_horizontal_layout = layout_menu.addAction("Setar Layout Horizontal")
        remove_layout = layout_menu.addAction("Remover Layout")
        
        action = menu.exec(event.screenPos())
        
        if action == bring_action: self.setZValue(self.zValue() + 1); view.save_state()
        elif action == send_action: self.setZValue(self.zValue() - 1); view.save_state()
        elif action == duplicate_action: view.duplicate_selected_widgets()
        elif action == delete_action: view.remove_selected_widgets()
        elif action == set_vertical_layout: self.set_otui_prop('layout', 'vertical'); self.apply_layout(); view.save_state()
        elif action == set_horizontal_layout: self.set_otui_prop('layout', 'horizontal'); self.apply_layout(); view.save_state()
        elif action == remove_layout: self.set_otui_prop('layout', ''); self.apply_layout(); self._check_layout_constraints(); view.save_state()

    def set_otui_prop(self, key: str, value: str):
        is_geom_prop = key in ['size', 'pos'] or key.startswith('anchors.') or key.startswith('margin') or key.startswith('padding')
        
        if not value and key not in ['pos', 'size']:
            self.otui_props.get('props', {}).pop(key, None)
        else:
            self.otui_props.get('props', {})[key] = value
        
        if key == 'id': self.update_name(value)

        if key in ['image-source', 'icon-source']:
            self.set_image(value, is_icon=(key == 'icon-source'))
        
        if is_geom_prop:
            self.apply_properties()
        else:
            if key == 'color' and QColor.isValidColor(value):
                self.text_item.setDefaultTextColor(QColor(value))
            elif key == 'text':
                self.text_item.setPlainText(value)
                self.update_text_position()
            self.update()

    def _check_layout_constraints(self):
        props = self.otui_props.get('props', {})
        
        has_anchors = 'anchors.fill' in props
        
        if not has_anchors:
            h_anchored = 'anchors.left' in props and 'anchors.right' in props
            v_anchored = 'anchors.top' in props and 'anchors.bottom' in props
            has_anchors = h_anchored or v_anchored

        is_in_layout = False
        if self.parent_widget and not has_anchors:
            parent_props = self.parent_widget.otui_props.get('props', {})
            if parent_props.get('layout') in ('vertical', 'horizontal'):
                if 'pos' not in props:
                    is_in_layout = True

        can_move = not has_anchors and not is_in_layout
        
        self.setFlag(QGraphicsObject.ItemIsMovable, can_move)
        self.setCursor(Qt.ArrowCursor if can_move else Qt.ForbiddenCursor)

    def apply_properties(self):
        props = self.otui_props.get('props', {})
        if 'id' in props: self.update_name(props['id'])
        
        if 'size' in props:
            try:
                w, h = map(to_int, props['size'].split())
                self.set_rect(0, 0, w, h)
            except (ValueError, TypeError): pass
            
        if 'pos' in props and not any(k.startswith('anchors.') for k in props):
            try:
                x, y = map(to_int, props['pos'].split())
                self.setPos(x, y)
            except (ValueError, TypeError): pass

        self.text_item.setPlainText(props.get('text', props.get('!text', self.name)))
        if 'color' in props and QColor.isValidColor(props['color']):
            self.text_item.setDefaultTextColor(QColor(props['color']))
        
        if 'font' in props:
            try:
                parts = props['font'].split('-')
                font_family = parts[0]
                font_size_match = re.search(r'\d+', props['font'])
                font_size = int(font_size_match.group()) if font_size_match else 11
                font = QFont(font_family, font_size)
                if 'bold' in parts: font.setBold(True)
                if 'italic' in parts: font.setItalic(True)
                self.text_item.setFont(font)
            except Exception:
                self.text_item.setFont(QFont("Verdana", 11))

        self.set_image(props.get('image-source', ''), is_icon=False)
        self.set_image(props.get('icon-source', ''), is_icon=True)
        
        self.update_geometry_from_anchors()
        self.update_text_position()
        self._check_layout_constraints()
        self.update()

    def update_geometry_from_anchors(self):
        if not self.parent_widget: return
        
        props = self.otui_props.get('props', {})
        anchors = {k: v for k, v in props.items() if k.startswith('anchors.')}
        if not anchors: return

        self.prepareGeometryChange()
        parent_rect = self.parent_widget.boundingRect()
        
        padding = parse_padding(self.parent_widget.otui_props.get('props', {}).get('padding', '0'))
        parent_inner_rect = parent_rect.adjusted(padding[3], padding[0], -padding[1], -padding[2])

        left, top = self.pos().x(), self.pos().y()
        width, height = self.rect().width(), self.rect().height()

        if 'anchors.fill' in anchors:
            left, top = parent_inner_rect.topLeft().x(), parent_inner_rect.topLeft().y()
            width, height = parent_inner_rect.width(), parent_inner_rect.height()
        else:
            if 'anchors.left' in anchors and 'anchors.right' in anchors:
                left = parent_inner_rect.left() + to_int(props.get('margin-left', 0))
                right_pos = parent_inner_rect.right() - to_int(props.get('margin-right', 0))
                width = max(0, right_pos - left)
            elif 'anchors.left' in anchors:
                left = parent_inner_rect.left() + to_int(props.get('margin-left', 0))
            elif 'anchors.right' in anchors:
                right_pos = parent_inner_rect.right() - to_int(props.get('margin-right', 0))
                left = right_pos - width
            elif 'anchors.horizontalCenter' in anchors:
                center = parent_inner_rect.center().x()
                margin = to_int(props.get('margin-left', 0)) - to_int(props.get('margin-right', 0))
                left = center - width / 2 + margin
            
            if 'anchors.top' in anchors and 'anchors.bottom' in anchors:
                top = parent_inner_rect.top() + to_int(props.get('margin-top', 0))
                bottom_pos = parent_inner_rect.bottom() - to_int(props.get('margin-bottom', 0))
                height = max(0, bottom_pos - top)
            elif 'anchors.top' in anchors:
                top = parent_inner_rect.top() + to_int(props.get('margin-top', 0))
            elif 'anchors.bottom' in anchors:
                bottom_pos = parent_inner_rect.bottom() - to_int(props.get('margin-bottom', 0))
                top = bottom_pos - height
            elif 'anchors.verticalCenter' in anchors:
                center = parent_inner_rect.center().y()
                margin = to_int(props.get('margin-top', 0)) - to_int(props.get('margin-bottom', 0))
                top = center - height / 2 + margin

        self.setPos(left, top)
        self.set_rect(0, 0, width, height)
        
        self.otui_props['props']['pos'] = f"{int(self.pos().x())} {int(self.pos().y())}"
        self.otui_props['props']['size'] = f"{int(self.rect().width())} {int(self.rect().height())}"
        self.update()


    def apply_layout(self):
        props = self.otui_props.get('props', {})
        layout_type = props.get('layout')
        if not layout_type or not self.children_widgets:
            return

        spacing = to_int(props.get('layout-spacing', 0))
        padding = parse_padding(props.get('padding', '0'))
        inner_rect = self.boundingRect().adjusted(padding[3], padding[0], -padding[1], -padding[2])

        non_anchored_children = [
            child for child in self.children_widgets
            if not any(k.startswith('anchors.') for k in child.otui_props.get('props', {}))
            and 'pos' not in child.otui_props.get('props', {})
        ]
        
        non_anchored_children.sort(key=lambda child: (child.pos().y(), child.pos().x()))

        if layout_type == 'vertical':
            current_y = inner_rect.top()
            for child in non_anchored_children:
                child_rect = child.boundingRect()
                align = props.get('layout-align', 'left')
                if align == 'right': child_x = inner_rect.right() - child_rect.width()
                elif align == 'center': child_x = inner_rect.center().x() - child_rect.width() / 2
                else: child_x = inner_rect.left()

                child.setPos(child_x, current_y)
                child.otui_props['props']['pos'] = f"{int(child.pos().x())} {int(child.pos().y())}"
                current_y += child_rect.height() + spacing
        
        elif layout_type == 'horizontal':
            current_x = inner_rect.left()
            for child in non_anchored_children:
                child_rect = child.boundingRect()
                align = props.get('layout-align', 'top')
                if align == 'bottom': child_y = inner_rect.bottom() - child_rect.height()
                elif align == 'center': child_y = inner_rect.center().y() - child_rect.height() / 2
                else: child_y = inner_rect.top()

                child.setPos(current_x, child_y)
                child.otui_props['props']['pos'] = f"{int(child.pos().x())} {int(child.pos().y())}"
                current_x += child_rect.width() + spacing
        
        self.update()


class Canvas(QGraphicsView):
    def __init__(self, history: History, owner_editor: 'OTUIEditor'):
        super().__init__()
        self.scene = QGraphicsScene()
        self.scene.setBackgroundBrush(QColor(40, 42, 54))
        self.setScene(self.scene)
        self.setSceneRect(-1000, -1000, 4000, 4000)
        self.selected_widget: Optional[WidgetItem] = None
        self.scene.selectionChanged.connect(self.selection_changed)
        
        self.setRenderHint(QPainter.Antialiasing)
        self.setRenderHint(QPainter.TextAntialiasing)
        self.setOptimizationFlag(QGraphicsView.DontAdjustForAntialiasing, True)

        self.history = history
        self.owner_editor = owner_editor
        
        self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
        self.grid_size = 10
        self._is_panning = False
        self._pan_start_pos = QPoint()
        
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.setDragMode(QGraphicsView.RubberBandDrag)

    def drawBackground(self, painter: QPainter, rect: QRectF):
        super().drawBackground(painter, rect)
        pen = QPen(QColor(68, 71, 90, 100), 1, Qt.DotLine)
        painter.setPen(pen)
        
        left = int(rect.left()) - (int(rect.left()) % self.grid_size)
        top = int(rect.top()) - (int(rect.top()) % self.grid_size)
        
        for x in range(left, int(rect.right()), self.grid_size):
            painter.drawLine(x, int(rect.top()), x, int(rect.bottom()))
        for y in range(top, int(rect.bottom()), self.grid_size):
            painter.drawLine(int(rect.left()), y, int(rect.right()), y)

    def mousePressEvent(self, event: Any):
        if event.button() == Qt.MiddleButton:
            self._is_panning = True
            self._pan_start_pos = event.pos()
            self.setCursor(Qt.ClosedHandCursor)
            event.accept()
            return
        
        item = self.itemAt(event.pos())
        if not item or not item.isSelected():
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event: Any):
        if self._is_panning:
            delta = event.pos() - self._pan_start_pos
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - delta.x())
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() - delta.y())
            self._pan_start_pos = event.pos()
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: Any):
        if event.button() == Qt.MiddleButton:
            self._is_panning = False
            self.setCursor(Qt.ArrowCursor)
            event.accept()
            return

        super().mouseReleaseEvent(event)
        
        moved = False
        for item in self.scene.selectedItems():
            if not isinstance(item, WidgetItem): continue
            
            # Ajuste de movimento (ItemIsMovable)
            if item.active_handle == item.P_NONE and item.flags() & QGraphicsObject.ItemIsMovable:
                pos = item.pos()
                snapped_x = round(pos.x() / self.grid_size) * self.grid_size
                snapped_y = round(pos.y() / self.grid_size) * self.grid_size
                if pos != QPointF(snapped_x, snapped_y):
                    item.setPos(snapped_x, snapped_y)
                    moved = True
            
            # Ajuste de redimensionamento (handle ativo)
            elif item.active_handle != item.P_NONE:
                
                # Snapping de posição (topLeft)
                scene_pos = item.mapToScene(item.pos())
                snapped_x = round(scene_pos.x() / self.grid_size) * self.grid_size
                snapped_y = round(scene_pos.y() / self.grid_size) * self.grid_size
                
                # Snapping de tamanho
                snapped_w = round(item.rect().width() / self.grid_size) * self.grid_size
                snapped_h = round(item.rect().height() / self.grid_size) * self.grid_size
                
                # Aplica as mudanças
                item.setPos(item.mapFromScene(QPointF(snapped_x, snapped_y)))
                item.set_rect(0, 0, snapped_w, snapped_h)
                
                # Atualiza as propriedades OTUI
                relative_pos = item.pos() if not item.parentItem() else item.mapToParent(QPointF(0, 0))
                item.otui_props['props']['pos'] = f"{int(relative_pos.x())} {int(relative_pos.y())}"
                item.otui_props['props']['size'] = f"{int(snapped_w)} {int(snapped_h)}"
                moved = True
                
        if moved:
            self.save_state()

    def wheelEvent(self, event: Any):
        if self.itemAt(event.pos()):
            super().wheelEvent(event)
            return

        delta = event.angleDelta().y()
        factor = 1.15 if delta > 0 else (1 / 1.15)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.scale(factor, factor)
        event.accept()

    def add_widget(self, widget_type: str = "UILabel", name: Optional[str] = None) -> 'WidgetItem':
        default_sizes = {"UILabel": (100, 20), "UIWindow": (400, 300), "UIImage": (100, 100), "UIButton": (120, 30), "UIWidget": (150, 100)}
        w, h = default_sizes.get(widget_type, (120, 60))
        
        center_view = self.mapToScene(self.viewport().rect().center())
        x, y = center_view.x() - w/2, center_view.y() - h/2
        
        snapped_x = round(x / self.grid_size) * self.grid_size
        snapped_y = round(y / self.grid_size) * self.grid_size

        all_names = {item.name for item in self.scene.items() if isinstance(item, WidgetItem)}
        base_name = re.sub(r'_\d+$', '', name or widget_type)
        new_name = base_name
        i = 1
        while new_name in all_names:
            new_name = f"{base_name.split('_')[0]}{i}"
            i += 1
        
        parent_widget: Optional[WidgetItem] = None
        target_pos = self.mapToScene(self.viewport().rect().center())
        
        container_candidates = [
            item for item in self.scene.items(target_pos)
            if isinstance(item, WidgetItem) and item.widget_type in ("UIWindow", "UIWidget", "Panel") and not item.isSelected()
        ]
        container_candidates.sort(key=lambda item: item.zValue(), reverse=True)
        if container_candidates:
            parent_widget = container_candidates[0]

        
        # Define a posição inicial na cena. Será convertida para posição local/relativa no WidgetItem.__init__
        initial_pos = QPointF(snapped_x, snapped_y)
        if parent_widget:
            # Posição na cena mapeada para o sistema de coordenadas do pai
            initial_pos = parent_widget.mapFromScene(initial_pos)

        widget = WidgetItem(widget_type=widget_type, name=new_name, x=initial_pos.x(), y=initial_pos.y(), width=w, height=h, parent_widget=parent_widget)
        
        if self.owner_editor.current_project:
            widget.hint_dir = self.owner_editor.current_project.root

        if parent_widget:
            widget.setParentItem(parent_widget)
            parent_widget.children_widgets.append(widget)
            parent_widget.geometry_changed.connect(widget.update_geometry_from_anchors)
            parent_widget.apply_layout()

        max_z = max([item.zValue() for item in self.scene.items() if isinstance(item, QGraphicsObject)] or [0])
        widget.setZValue(max_z + 1)
        
        self.scene.addItem(widget)
        widget.setSelected(True)
        self.save_state()
        return widget

    def selection_changed(self):
        items = self.scene.selectedItems()
        self.selected_widget = items[0] if items and isinstance(items[0], WidgetItem) else None
        self.owner_editor.props_editor.load_props()

    def serialize(self) -> List[Dict[str, Any]]:
        state = []
        for w in self.scene.items():
            if isinstance(w, WidgetItem):
                parent_name = w.parent_widget.name if w.parent_widget else None
                state.append({
                    'type': w.widget_type, 'name': w.name,
                    'x': w.mapToScene(w.rect().topLeft()).x(),
                    'y': w.mapToScene(w.rect().topLeft()).y(),
                    'width': w.rect().width(), 'height': w.rect().height(),
                    'z': w.zValue(), 'parent': parent_name,
                    'otui_props': {k: dict(v) if isinstance(v, defaultdict) else v for k, v in w.otui_props.items()}
                })
        return state

    def save_state(self):
        self.history.push(self.serialize())

    def restore_state(self, state: Optional[List[Dict[str, Any]]]):
        if state is None: return
        self.scene.clear()
        name_map: Dict[str, WidgetItem] = {}
        pending_children = []
        
        sorted_state = sorted(state, key=lambda x: x.get('z', 0))

        for w_data in sorted_state:
            otui_props_raw = w_data.get('otui_props', {})
            otui_props: Dict[str, Any] = {
                'props': defaultdict(str, otui_props_raw.get('props', {})),
                'states': defaultdict(str, otui_props_raw.get('states', {})),
                'events': defaultdict(str, otui_props_raw.get('events', {})),
                'functions': defaultdict(str, otui_props_raw.get('functions', {})),
                'inherit': otui_props_raw.get('inherit', None)
            }
            
            wi = WidgetItem(
                widget_type=w_data['type'], name=w_data['name'],
                x=w_data['x'], y=w_data['y'],
                width=w_data['width'], height=w_data['height']
            )
            wi.setZValue(w_data.get('z', 0))
            wi.otui_props = otui_props
            
            if self.owner_editor.current_project:
                wi.hint_dir = self.owner_editor.current_project.root
            
            self.scene.addItem(wi)
            name_map[wi.name] = wi
            if w_data.get('parent'):
                pending_children.append((wi, w_data['parent'], QPointF(w_data['x'], w_data['y'])))

        for wi, parent_name, global_pos in pending_children:
            parent = name_map.get(parent_name)
            if parent:
                wi.parent_widget = parent
                wi.setParentItem(parent)
                parent.children_widgets.append(wi)
                parent.geometry_changed.connect(wi.update_geometry_from_anchors)
                
                # Calcula a posição local correta no sistema de coordenadas do pai
                relative_pos = parent.mapFromScene(global_pos)
                wi.setPos(relative_pos)
                
                # Define a propriedade 'pos' OTUI correta (relativa)
                wi.otui_props['props']['pos'] = f"{int(relative_pos.x())} {int(relative_pos.y())}"
                
        for item in self.scene.items():
            if isinstance(item, WidgetItem):
                item.apply_properties()
                item.apply_layout()

        self.owner_editor.props_editor.load_props()

    def remove_selected_widgets(self):
        selected_items = [item for item in self.scene.selectedItems() if isinstance(item, WidgetItem)]
        if not selected_items: return

        reply = QMessageBox.question(self.owner_editor, "Confirmar Exclusão",
                                     f"Tem certeza que deseja excluir {len(selected_items)} widget(s)?",
                                     QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.No: return

        self.scene.clearSelection()
        QApplication.processEvents()

        for item in selected_items:
            if item.parent_widget and item in item.parent_widget.children_widgets:
                try:
                    item.parent_widget.geometry_changed.disconnect(item.update_geometry_from_anchors)
                except RuntimeError:
                    pass
                item.parent_widget.children_widgets.remove(item)
                item.parent_widget.apply_layout()
            
            self.scene.removeItem(item)
            item.deleteLater()

        self.selected_widget = None
        self.save_state()
        self.owner_editor.props_editor.load_props()

    def duplicate_selected_widgets(self):
        original_selection = [item for item in self.scene.selectedItems() if isinstance(item, WidgetItem)]
        if not original_selection: return

        all_names = {item.name for item in self.scene.items() if isinstance(item, WidgetItem)}
        self.scene.clearSelection()

        for item in original_selection:
            base_name = re.sub(r'(_\d+)?$', '', item.name)
            i = 1
            new_name = f"{base_name}_{i}"
            while new_name in all_names:
                i += 1
                new_name = f"{base_name}_{i}"
            all_names.add(new_name)
            
            # Posição inicial no sistema de coordenadas do pai (relativa)
            initial_pos = item.pos() + QPointF(self.grid_size, self.grid_size)

            new_widget = WidgetItem(
                widget_type=item.widget_type,
                name=new_name,
                x=initial_pos.x(), y=initial_pos.y(),
                parent_widget=item.parent_widget
            )
            
            new_widget.set_rect(item.rect().x(), item.rect().y(), item.rect().width(), item.rect().height())
            new_widget.setZValue(item.zValue() + 1)
            
            new_widget.otui_props = json.loads(json.dumps(dict(item.otui_props)))
            
            for k, v in new_widget.otui_props.items():
                if isinstance(v, dict):
                    new_widget.otui_props[k] = defaultdict(str, v)

            new_widget.otui_props['props']['id'] = new_name
            
            new_widget.otui_props['props']['pos'] = f"{int(new_widget.pos().x())} {int(new_widget.pos().y())}"

            new_widget.apply_properties()
            
            if item.parent_widget:
                new_widget.setParentItem(item.parent_widget) # Define o pai após aplicar a posição local
                item.parent_widget.children_widgets.append(new_widget)
                item.parent_widget.geometry_changed.connect(new_widget.update_geometry_from_anchors)
                item.parent_widget.apply_layout()
            
            self.scene.addItem(new_widget)
            new_widget.setSelected(True)

        self.save_state()

class StyledInputDialog(QDialog):
    def __init__(self, parent: Optional[QWidget] = None, title: str = "", label_text: str = ""):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setStyleSheet("""
            QDialog { background-color: #1b1a2b; border: 1px solid #2b2b4a; }
            QLabel { color: #cfe8ff; }
            QLineEdit { background-color: #2b2b4a; color: #dff6ff; border: 1px solid #3f3f7a; border-radius: 4px; padding: 4px; }
            QPushButton { background-color: #393655; color: #fff; border-radius: 4px; padding: 6px; }
            QPushButton:hover { background-color: #4c4870; }
        """)
        layout = QVBoxLayout(self)
        self.label = QLabel(label_text)
        layout.addWidget(self.label)
        self.line_edit = QLineEdit()
        layout.addWidget(self.line_edit)
        
        button_layout = QHBoxLayout()
        self.ok_button = QPushButton("OK")
        self.ok_button.clicked.connect(self.accept)
        self.cancel_button = QPushButton("Cancelar")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.ok_button)
        button_layout.addWidget(self.cancel_button)
        layout.addLayout(button_layout)
    
    def get_text_and_result(self) -> Tuple[str, bool]:
        result = self.exec()
        return self.line_edit.text(), result == QDialog.Accepted

class AddPropertyDialog(QDialog):
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setWindowTitle("Adicionar Propriedades OTUI")
        self.resize(300, 400)
        self.selected_props: List[Tuple[str, str]] = []
        self.setStyleSheet("""
            QDialog { background-color: #1b1a2b; }
            QLabel { color: #cfe8ff; }
            QListWidget { background-color: #2b2b4a; color: #dff6ff; border: 1px solid #3f3f7a; }
            QListWidget::item:selected { background-color: #007ACC; }
            QPushButton { background-color: #393655; color: #fff; border-radius: 4px; padding: 6px; }
            QPushButton:hover { background-color: #4c4870; }
        """)

        layout = QVBoxLayout(self)
        label = QLabel("Selecione as propriedades:")
        layout.addWidget(label)
        self.prop_list = QListWidget()
        layout.addWidget(self.prop_list)

        buttons_layout = QHBoxLayout()
        ok_btn = QPushButton("OK")
        cancel_btn = QPushButton("Cancelar")
        buttons_layout.addWidget(ok_btn)
        buttons_layout.addWidget(cancel_btn)
        layout.addLayout(buttons_layout)
        
        ok_btn.clicked.connect(self.accept)
        cancel_btn.clicked.connect(self.reject)

        for name in sorted(AppConstants.KNOWN_PROPERTIES.keys()):
            item = QListWidgetItem(name)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Unchecked)
            self.prop_list.addItem(item)

    def accept(self):
        self.selected_props = []
        for i in range(self.prop_list.count()):
            item = self.prop_list.item(i)
            if item.checkState() == Qt.Checked:
                prop_name = item.text()
                default_value = AppConstants.KNOWN_PROPERTIES.get(prop_name, "")
                self.selected_props.append((prop_name, default_value))
        super().accept()

class ImageSourceBrowser(QDialog):
    def __init__(self, project: 'ModuleProject', parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.project = project
        self.selected_path: Optional[str] = None
        self.setWindowTitle("Navegador de Imagens do Projeto")
        self.resize(800, 500)
        self.setStyleSheet("""
            QDialog { background-color: #1E1E1E; }
            QTreeWidget, QTableWidget { background-color: #252526; color: #D4D4D4; border: 1px solid #444; }
            QTableWidget::item:selected, QTreeWidget::item:selected { background-color: #007ACC; }
            QLabel { color: #D4D4D4; }
            QPushButton { background-color: #3E3E42; border: 1px solid #555; border-radius: 4px; padding: 5px 10px; color: #D4D4D4; }
            QPushButton:hover { background-color: #505054; }
        """)
        
        main_layout = QVBoxLayout(self)
        
        h_splitter = QSplitter(Qt.Horizontal)
        
        self.directory_tree = QTreeWidget()
        self.directory_tree.setHeaderHidden(True)
        h_splitter.addWidget(self.directory_tree)
        
        self.images_grid = QTableWidget()
        self.images_grid.setShowGrid(False)
        self.images_grid.setColumnCount(4)
        h_splitter.addWidget(self.images_grid)
        
        h_splitter.setSizes([200, 600])
        main_layout.addWidget(h_splitter)
        
        button_layout = QHBoxLayout()
        ok_button = QPushButton("Selecionar")
        cancel_button = QPushButton("Cancelar")
        button_layout.addStretch()
        button_layout.addWidget(ok_button)
        button_layout.addWidget(cancel_button)
        main_layout.addLayout(button_layout)
        
        ok_button.clicked.connect(self.accept)
        cancel_button.clicked.connect(self.reject)

        self.load_directory_tree()
        self.directory_tree.itemClicked.connect(self.on_item_clicked)
        self.images_grid.itemDoubleClicked.connect(self.on_image_selected)

    def load_directory_tree(self):
        self.directory_tree.clear()
        
        all_roots = list(set(self.project.data_roots + self.project.image_dirs + self.project.extra_search_paths))
        
        for root_path in all_roots:
            if not root_path.exists(): continue
            try:
                display_name = root_path.relative_to(self.project.root).as_posix()
            except ValueError:
                display_name = root_path.name

            root_item = QTreeWidgetItem(self.directory_tree, [display_name])
            root_item.setData(0, Qt.UserRole, str(root_path))
            self._recursively_get_directory(str(root_path), root_item)
            root_item.setExpanded(True)

    def _recursively_get_directory(self, path: str, parent_item: QTreeWidgetItem):
        qdir = QDir(path)
        qdir.setFilter(QDir.Dirs | QDir.NoDotAndDotDot)
        qdir.setSorting(QDir.SortFlag.Name)
        for d in qdir.entryInfoList():
            if d.fileName().startswith('.'): continue
            item = QTreeWidgetItem(parent_item, [d.fileName()])
            item.setData(0, Qt.UserRole, d.absoluteFilePath())
            self._recursively_get_directory(d.absoluteFilePath(), item)

    def on_item_clicked(self, item: QTreeWidgetItem, column: int):
        self.images_grid.clear()
        self.images_grid.setRowCount(0)
        self.images_grid.setColumnCount(4)
        
        path = item.data(0, Qt.UserRole)
        if not path: return
        
        qdir = QDir(path)
        qdir.setNameFilters(['*.png', '*.jpg', '*.jpeg', '*.gif'])
        qdir.setFilter(QDir.Files | QDir.NoDotAndDotDot | QDir.Readable)
        images = qdir.entryInfoList()
        if not images: return

        num_cols = 4
        num_rows = (len(images) + num_cols - 1) // num_cols
        self.images_grid.setRowCount(num_rows)
        self.images_grid.verticalHeader().setVisible(False)
        self.images_grid.horizontalHeader().setVisible(False)
        
        thumbnail_size = QSize(128, 128)
        cell_width, cell_height = 160, 160

        for i, img_info in enumerate(images):
            image_path = img_info.absoluteFilePath()
            pixmap = QPixmap(image_path)
            if pixmap.isNull(): continue
            
            cell_widget = QWidget()
            layout = QVBoxLayout(cell_widget)
            layout.setContentsMargins(5, 5, 5, 5)
            layout.setAlignment(Qt.AlignCenter)
            
            img_label = QLabel()
            img_label.setPixmap(pixmap.scaled(thumbnail_size, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            img_label.setAlignment(Qt.AlignCenter)
            
            name_label = QLabel(img_info.fileName())
            name_label.setAlignment(Qt.AlignCenter)
            name_label.setWordWrap(True)
            name_label.setStyleSheet("color: #D4D4D4; font-size: 10px;")
            
            layout.addWidget(img_label)
            layout.addWidget(name_label)
            
            row, col = divmod(i, num_cols)
            self.images_grid.setColumnWidth(col, cell_width)
            self.images_grid.setRowHeight(row, cell_height)
            
            item = QTableWidgetItem()
            item.setData(Qt.UserRole, image_path)
            self.images_grid.setItem(row, col, item)
            self.images_grid.setCellWidget(row, col, cell_widget)
            
    def on_image_selected(self, item: QTableWidgetItem):
        if item:
            path = item.data(Qt.UserRole)
            if path and os.path.exists(path):
                self.selected_path = path
                self.accept()
            else:
                QMessageBox.warning(self, "Caminho Inválido", f"O caminho da imagem não foi encontrado:\n{path}")


class PropertiesEditor(QScrollArea):
    def __init__(self, canvas: 'Canvas'):
        super().__init__()
        self.canvas = canvas
        self.setWidgetResizable(True)
        self.setFrameShape(QFrame.NoFrame)
        self.setStyleSheet("QLabel#propSection { color: #007ACC; font-size: 14px; margin-top: 10px; margin-bottom: 5px; }")
        
        self.layout_widget = QWidget()
        self.main_layout = QVBoxLayout(self.layout_widget)
        self.main_layout.setAlignment(Qt.AlignTop)
        self.setWidget(self.layout_widget)
        self.active_widget: Optional[WidgetItem] = None
        
        self.canvas.scene.selectionChanged.connect(self.load_props)
        self._realtime_widgets: Dict[str, QLineEdit] = {}

    def clear_layout(self):
        self.active_widget = None
        self._realtime_widgets.clear()
        
        while self.main_layout.count():
            item = self.main_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                self._clear_layout_recursively(item.layout())

    def _clear_layout_recursively(self, layout: QHBoxLayout | QVBoxLayout):
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                self._clear_layout_recursively(item.layout())

    def load_props(self):
        selected_widgets = self.canvas.scene.selectedItems()
        widget = selected_widgets[0] if selected_widgets and isinstance(selected_widgets[0], WidgetItem) else None

        if widget is None:
            self.clear_layout()
            return
            
        if widget == self.active_widget and self.main_layout.count() > 0:
            self.update_realtime_props()
            return
            
        self.clear_layout()
        self.active_widget = widget

        self.add_section("Propriedades Base")
        self.add_prop_editor("id", widget.name, lambda val: self.update_prop('id', val))
        self.add_prop_editor("size", f"{int(widget.rect().width())} {int(widget.rect().height())}", lambda val: self.update_prop('size', val), realtime=True)
        pos_val = widget.otui_props['props'].get('pos', f"{int(widget.pos().x())} {int(widget.pos().y())}")
        self.add_prop_editor("pos", pos_val, lambda val: self.update_prop('pos', val), realtime=True)
        self.add_prop_editor("type", widget.widget_type, None, enabled=False)

        otui_props = widget.otui_props.get('props', {})
        self.add_section("Propriedades OTUI")

        for key in sorted(otui_props.keys()):
            if key in ["id", "size", "pos"]: continue
            
            value = otui_props[key]
            
            handler = None
            if key.endswith('-source') or key.endswith('-image'):
                handler = self.add_image_prop_editor
            elif 'color' in key:
                handler = self.add_color_prop_editor
            elif isinstance(value, str) and value.lower() in ['true', 'false']:
                handler = self.add_boolean_prop_editor
            
            if handler:
                handler(key, value, lambda val, k=key: self.update_prop(k, val))
            else:
                self.add_prop_editor(key, value, lambda val, k=key: self.update_prop(k, val))
            
        
        add_prop_btn = QPushButton("Adicionar Propriedade")
        add_prop_btn.clicked.connect(self.add_new_prop_dialog)
        self.main_layout.addWidget(add_prop_btn)
        
        self.main_layout.addItem(QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Expanding))

    def update_realtime_props(self):
        if not self.active_widget: return
        
        if 'size' in self._realtime_widgets:
            self._realtime_widgets['size'].setText(f"{int(self.active_widget.rect().width())} {int(self.active_widget.rect().height())}")
        
        if 'pos' in self._realtime_widgets and not any(k.startswith('anchors.') for k in self.active_widget.otui_props['props']):
            pos = self.active_widget.pos()
            # Pos é sempre a coordenada local/relativa ao pai
            self._realtime_widgets['pos'].setText(f"{int(pos.x())} {int(pos.y())}")

    def add_section(self, title: str):
        label = QLabel(title)
        label.setObjectName("propSection")
        self.main_layout.addWidget(label)

    def add_prop_editor(self, name: str, value: Any, callback: Optional[Any] = None, enabled: bool = True, realtime: bool = False):
        prop_layout = QHBoxLayout()
        label = QLabel(name)
        label.setFixedWidth(120)
        line_edit = QLineEdit(str(value))
        line_edit.setEnabled(enabled)
        
        if callback:
            line_edit.editingFinished.connect(lambda: callback(line_edit.text()))
        
        prop_layout.addWidget(label)
        prop_layout.addWidget(line_edit)
        self.main_layout.addLayout(prop_layout)
        
        if realtime:
            self._realtime_widgets[name] = line_edit

    def add_image_prop_editor(self, name: str, value: Any, callback: Any):
        prop_layout = QHBoxLayout()
        label = QLabel(name)
        label.setFixedWidth(120)
        line_edit = QLineEdit(str(value))
        browse_btn = QPushButton("...")
        browse_btn.setFixedSize(24, 24)
        
        prop_layout.addWidget(label)
        prop_layout.addWidget(line_edit)
        prop_layout.addWidget(browse_btn)
        self.main_layout.addLayout(prop_layout)
        
        def on_browse():
            if not self.canvas.owner_editor.current_project:
                QMessageBox.warning(self.canvas.owner_editor, "Aviso", "Nenhum projeto aberto.")
                return
            dialog = ImageSourceBrowser(self.canvas.owner_editor.current_project, self.canvas.owner_editor)
            if dialog.exec() == QDialog.Accepted and dialog.selected_path:
                self.canvas.owner_editor.handle_image_update(self.active_widget, name, dialog.selected_path)
                update_prop_value(name)

        def on_edit_finished(text):
            callback(text)
            update_prop_value(name)

        def update_prop_value(key: str):
            if self.active_widget:
                line_edit.setText(self.active_widget.otui_props['props'].get(key, ''))

        browse_btn.clicked.connect(on_browse)
        line_edit.editingFinished.connect(lambda: on_edit_finished(line_edit.text()))

    def add_boolean_prop_editor(self, name: str, value: Any, callback: Any):
        prop_layout = QHBoxLayout()
        label = QLabel(name)
        label.setFixedWidth(120)
        combo = QComboBox()
        combo.addItems(["true", "false"])
        combo.setCurrentText(str(value).lower())
        combo.currentTextChanged.connect(callback)
        
        prop_layout.addWidget(label)
        prop_layout.addWidget(combo)
        self.main_layout.addLayout(prop_layout)

    def add_color_prop_editor(self, name: str, value: Any, callback: Any):
        prop_layout = QHBoxLayout()
        label = QLabel(name)
        label.setFixedWidth(120)
        line_edit = QLineEdit(str(value))
        color_btn = QPushButton("🎨")
        color_btn.setFixedSize(24, 24)

        prop_layout.addWidget(label)
        prop_layout.addWidget(line_edit)
        prop_layout.addWidget(color_btn)
        self.main_layout.addLayout(prop_layout)

        def on_pick_color():
            initial_color = QColor(line_edit.text()) if QColor.isValidColor(line_edit.text()) else Qt.white
            color = QColorDialog.getColor(initial_color, self, "Selecione a Cor")
            if color.isValid():
                hex_color = color.name(QColor.HexArgb)
                line_edit.setText(hex_color)
                callback(hex_color)

        color_btn.clicked.connect(on_pick_color)
        line_edit.editingFinished.connect(lambda: callback(line_edit.text()))

    def add_new_prop_dialog(self):
        if not self.active_widget: return
        dialog = AddPropertyDialog(self)
        if dialog.exec() == QDialog.Accepted:
            for key, value in dialog.selected_props:
                self.update_prop(key, value)
            self.load_props()

    def update_prop(self, key: str, value: str):
        if self.active_widget:
            self.active_widget.set_otui_prop(key, value)
            self.canvas.save_state()
            self.canvas.owner_editor.project_changed.emit()

class OTUIParser:
    
    def __init__(self):
        self.widgets_data: List[Dict[str, Any]] = []
        self.name_map: Dict[str, WidgetItem] = {}
        self.parsed_files: set = set()

    def _parse_otui_content(self, content: str, hint_path: Path) -> List[Dict[str, Any]]:
        lines = content.splitlines()
        root_data: List[Dict[str, Any]] = []
        widget_stack: List[Dict[str, Any]] = []

        WIDGET_REGEX = re.compile(r'^\s*([a-zA-Z0-9]+)\s*(<.*)?\s*$')
        PROP_REGEX = re.compile(r'^\s*([a-zA-Z0-9\-\.!]+):\s*(.*)\s*$')
        STATE_REGEX = re.compile(r'^\s*\$([a-zA-Z0-9]+):\s*(.*)\s*$')
        EVENT_REGEX = re.compile(r'^\s*@([a-zA-Z0-9]+):\s*(.*)\s*$')
        
        current_indent = -1
        
        for line_num, line in enumerate(lines):
            stripped_line = line.strip()
            if not stripped_line or stripped_line.startswith('//') or stripped_line.startswith('#'): continue

            match_indent = re.match(r'^(\s*)', line)
            indent_str = match_indent.group(1) if match_indent else ""
            indent = len(indent_str.replace('\t', '    ')) // 4

            while indent <= current_indent and widget_stack:
                widget_stack.pop()
                current_indent = len(widget_stack) - 1 if widget_stack else -1
            
            widget_match = WIDGET_REGEX.match(stripped_line)
            if widget_match and stripped_line.startswith(widget_match.group(1)):
                widget_type = widget_match.group(1).strip()
                inherit_part = widget_match.group(2)
                inherit = inherit_part.strip('< ').strip() if inherit_part else None
                
                w_data = {
                    'type': widget_type, 'name': widget_type,
                    'props': defaultdict(str), 'states': defaultdict(str),
                    'events': defaultdict(str), 'functions': defaultdict(str),
                    'inherit': inherit, 'children': [], 'hint_dir': hint_path
                }

                unique_name = f"{widget_type}{line_num}"
                w_data['name'] = unique_name
                
                if widget_stack:
                    widget_stack[-1]['children'].append(w_data)
                else:
                    root_data.append(w_data)
                    
                widget_stack.append(w_data)
                current_indent = indent
                continue
            
            if not widget_stack: continue
            current_widget = widget_stack[-1]

            prop_match = PROP_REGEX.match(stripped_line)
            if prop_match:
                key, value = prop_match.groups()
                current_widget['props'][key.strip()] = value.strip()
                if key.strip() == 'id':
                    current_widget['name'] = value.strip()
                    current_widget['props']['id'] = value.strip()
                continue
            
            state_match = STATE_REGEX.match(stripped_line)
            if state_match:
                key, value = state_match.groups()
                current_widget['states'][key.strip()] = value.strip()
                continue
            
            event_match = EVENT_REGEX.match(stripped_line)
            if event_match:
                key, value = event_match.groups()
                current_widget['events'][key.strip()] = value.strip()
                continue

        return root_data

    def load_to_canvas(self, canvas: 'Canvas', file_paths: List[Path]):
        canvas.scene.clear()
        self.widgets_data = []
        self.name_map = {}
        self.parsed_files.clear()
        
        for file_path in file_paths:
            if file_path in self.parsed_files: continue
            self.parsed_files.add(file_path)
            
            content = read_text_with_fallback(file_path)
            new_data = self._parse_otui_content(content, file_path.parent)
            self.widgets_data.extend(new_data)

        def create_widget_item(w_data: Dict[str, Any], parent_item: Optional[WidgetItem] = None):
            props = w_data.get('props', {})
            pos_str = props.get('pos', '0 0')
            size_str = props.get('size', '100 50')
            
            try: x, y = map(to_int, pos_str.split())
            except: x, y = 0, 0
            
            try: w, h = map(to_int, size_str.split())
            except: w, h = 100, 50

            # X e Y aqui representam a posição LOCAL (dentro do pai ou cena para raiz)
            local_x, local_y = x, y 
            
            wi = WidgetItem(
                widget_type=w_data['type'],
                name=w_data['name'],
                x=local_x, y=local_y, # Passa a posição local
                width=w, height=h,
                parent_widget=parent_item
            )
            
            wi.otui_props['props'].update(props)
            wi.otui_props['states'].update(w_data.get('states', {}))
            wi.otui_props['events'].update(w_data.get('events', {}))
            wi.otui_props['inherit'] = w_data.get('inherit')
            wi.hint_dir = w_data.get('hint_dir')
            
            if parent_item:
                wi.setParentItem(parent_item)
                parent_item.children_widgets.append(wi)
                parent_item.geometry_changed.connect(wi.update_geometry_from_anchors)
                wi.setPos(local_x, local_y)
            else:
                canvas.scene.addItem(wi)
                wi.setPos(local_x, local_y)

            self.name_map[wi.name] = wi
            wi.apply_properties()
            
            for child_data in w_data.get('children', []):
                create_widget_item(child_data, wi)
        
        for w_data in self.widgets_data:
            create_widget_item(w_data)

        for item in canvas.scene.items():
            if isinstance(item, WidgetItem):
                item.apply_layout()

        canvas.save_state()

class OTUIEditor(QMainWindow):
    project_changed = Signal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Otui Editor - PRO")
        self.resize(1600, 900)
        
        self.history = History()
        self.parser = OTUIParser()
        self.canvas = Canvas(self.history, self)
        self.props_editor = PropertiesEditor(self.canvas)
        
        self.current_project: Optional[ModuleProject] = None
        self.current_otui_path: Optional[str] = None
        self.current_dir = Path.home()

        self.setup_ui()
        self.init_menus()
        self.load_stylesheet()
        
        self._restore_last_workspace()

    def setup_ui(self):
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        main_layout = QVBoxLayout(self.central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        widget_toolbar = QFrame()
        widget_toolbar.setObjectName("widgetToolbar")
        toolbar_layout = QHBoxLayout(widget_toolbar)
        toolbar_layout.setContentsMargins(10, 5, 10, 5)
        toolbar_layout.setSpacing(8)
        
        widget_types_map = {
            "Window": "UIWindow", "Label": "UILabel", "Image": "UIImage",
            "Button": "UIButton", "Widget": "UIWidget", "Creature": "UICreature",
            "Item": "UIItem", "TextEdit": "UITextEdit", "Panel": "Panel"
        }

        for display_name, wtype in widget_types_map.items():
            btn = QPushButton(display_name)
            btn.setToolTip(f"Adicionar {wtype}")
            btn.clicked.connect(lambda _, t=wtype: self.canvas.add_widget(t))
            toolbar_layout.addWidget(btn)
            
        toolbar_layout.addStretch()
        main_layout.addWidget(widget_toolbar)

        content_splitter = QSplitter(Qt.Horizontal)
        content_splitter.setHandleWidth(1)
        
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.addWidget(self.canvas)

        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_splitter = QSplitter(Qt.Vertical)
        right_splitter.setHandleWidth(1)

        props_container = QWidget()
        props_layout = QVBoxLayout(props_container)
        props_layout.setContentsMargins(5, 5, 5, 5)
        label_props = QLabel("Propriedades")
        label_props.setStyleSheet("font-size: 14px; color: #007ACC;")
        props_layout.addWidget(label_props)
        props_layout.addWidget(self.props_editor)
        
        files_container = QWidget()
        files_layout = QVBoxLayout(files_container)
        files_layout.setContentsMargins(5, 5, 5, 5)
        label_files = QLabel("Arquivos do Módulo")
        label_files.setStyleSheet("font-size: 14px; color: #007ACC;")
        files_layout.addWidget(label_files)
        
        self.current_path_label = QLabel(str(self.current_dir))
        self.current_path_label.setStyleSheet("font-size: 10px; color: #777777;")
        files_layout.addWidget(self.current_path_label)
        
        self.module_files_list = QListWidget()
        self.module_files_list.itemDoubleClicked.connect(self._open_from_list)
        files_layout.addWidget(self.module_files_list)
        
        right_splitter.addWidget(props_container)
        right_splitter.addWidget(files_container)
        right_splitter.setSizes([450, 350])
        right_layout.addWidget(right_splitter)
        
        content_splitter.addWidget(left_panel)
        content_splitter.addWidget(right_panel)
        content_splitter.setSizes([1000, 400])
        main_layout.addWidget(content_splitter, 1)
        
        self.statusBar = self.statusBar()
        self.statusBar.showMessage("Pronto")
        self.project_changed.connect(self.update_window_title)

    def load_stylesheet(self):
        self.setStyleSheet("""
            QMainWindow, QWidget { background-color: #1E1E1E; color: #D4D4D4; font-family: "Segoe UI"; }
            QFrame#widgetToolbar { background-color: #2D2D30; border-bottom: 1px solid #444444; }
            QMenuBar { background-color: #333333; }
            QMenuBar::item:selected { background-color: #007ACC; }
            QMenu { background-color: #252526; border: 1px solid #444444; }
            QMenu::item:selected { background-color: #007ACC; }
            QPushButton {
                background-color: #3E3E42; border: 1px solid #555; border-radius: 4px; padding: 5px 10px;
                color: #D4D4D4;
            }
            QPushButton:hover { background-color: #505054; }
            QSplitter::handle { background-color: #444444; }
            QSplitter::handle:horizontal { width: 2px; }
            QSplitter::handle:vertical { height: 2px; }
            QLabel { font-size: 11px; color: #AAAAAA; margin-top: 5px; }
            QLabel#propSection { color: #007ACC; font-size: 14px; font-weight: bold; margin-top: 10px; margin-bottom: 5px; }
            QListWidget, QLineEdit, QComboBox, QTreeWidget, QTableWidget {
                background-color: #252526; border: 1px solid #444; border-radius: 4px; padding: 4px;
                color: #D4D4D4;
            }
            QListWidget::item:selected, QTableWidget::item:selected { background-color: #007ACC; color: white; }
            QScrollBar:vertical { border: 1px solid #444; background: #2D2D30; width: 10px; margin: 0 0 0 0; }
            QScrollBar::handle:vertical { background: #555; border-radius: 5px; min-height: 20px; }
        """)

    def init_menus(self):
        menu_bar = self.menuBar()
        
        file_menu = menu_bar.addMenu("Arquivo")
        file_menu.addAction("Novo Projeto", self.new_project, QKeySequence("Ctrl+Shift+N"))
        file_menu.addAction("Abrir Projeto...", self.load_client_module, QKeySequence("Ctrl+O"))
        file_menu.addSeparator()
        file_menu.addAction("Criar OTUI", self.create_otui, QKeySequence("Ctrl+N"))
        file_menu.addAction("Abrir OTUI...", self.open_otui, QKeySequence("Ctrl+Shift+O"))
        file_menu.addAction("Salvar OTUI", self.save_current_otui, QKeySequence.Save)
        
        edit_menu = menu_bar.addMenu("Editar")
        edit_menu.addAction("Desfazer", self.undo, QKeySequence.Undo)
        edit_menu.addAction("Refazer", self.redo, QKeySequence.Redo)
        edit_menu.addSeparator()
        edit_menu.addAction("Duplicar", self.canvas.duplicate_selected_widgets, QKeySequence("Ctrl+D"))
        edit_menu.addAction("Excluir", self.canvas.remove_selected_widgets, QKeySequence.Delete)

    def undo(self):
        state = self.history.undo()
        if state:
            self.canvas.restore_state(state)
            self.update_status_bar("Ação desfeita")

    def redo(self):
        state = self.history.redo()
        if state:
            self.canvas.restore_state(state)
            self.update_status_bar("Ação refeita")

    def update_status_bar(self, message: str):
        self.statusBar.showMessage(message)

    def _workspace_file(self) -> Path:
        base = Path.home() / ".otui_editor_lehnox"
        base.mkdir(parents=True, exist_ok=True)
        return base / "workspace.json"

    def _restore_last_workspace(self):
        wf = self._workspace_file()
        if wf.exists():
            try:
                data = json.loads(wf.read_text(encoding='utf-8'))
                last_project = data.get("last_project")
                if last_project and Path(last_project).exists():
                    self.current_dir = Path(last_project)
                    self._open_project(last_project, auto_from_workspace=True)
            except Exception:
                pass

    def _save_workspace(self):
        wf = self._workspace_file()
        payload = {"last_project": str(self.current_project.root) if self.current_project else None}
        try:
            wf.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')
        except Exception:
            pass

    def save_current_otui(self):
        if not self.current_project:
            QMessageBox.warning(self, "Aviso", "Nenhum projeto aberto para salvar.")
            return

        path_str = self.current_otui_path
        if not path_str:
            default_save_dir = self.current_dir
            if self.current_project and (self.current_project.root / 'data' / 'layouts').is_dir():
                default_save_dir = self.current_project.root / 'data' / 'layouts'
            
            default_save_dir.mkdir(parents=True, exist_ok=True)
            path_str, _ = QFileDialog.getSaveFileName(self, "Salvar Arquivo OTUI", str(default_save_dir / "new_ui.otui"), "OTUI Files (*.otui)")
            if not path_str: return
        
        save_path = Path(path_str)

        try:
            widgets = [w for w in self.canvas.scene.items() if isinstance(w, WidgetItem)]
            save_otui(str(save_path), widgets, self.current_project)
            self.current_otui_path = str(save_path)
            self.current_project.is_changed = False
            self.project_changed.emit()
            self._save_project_state()
            QMessageBox.information(self, "Sucesso", f"Arquivo OTUI salvo em:\n{self.current_otui_path}")
        except Exception as e:
            QMessageBox.critical(self, "Erro ao Salvar", f"Ocorreu um erro inesperado:\n{e}")
            traceback.print_exc()

    def _open_from_list(self, item: QListWidgetItem):
        path_str = item.data(Qt.UserRole)
        if not path_str or not self.current_project: return
        
        path = Path(path_str)
        if not path.exists():
            QMessageBox.warning(self, "Erro", f"O caminho {path_str} não foi encontrado.")
            return

        if path.is_dir():
            self.current_dir = path
            self.list_current_directory()
        elif is_valid_otui_file(path):
            self.current_otui_path = str(path)
            try:
                self.parser.load_to_canvas(self.canvas, [path])
                self.update_window_title()
                self._save_project_state()
            except Exception as e:
                QMessageBox.critical(self, "Erro ao carregar OTUI", f"Ocorreu um erro: {e}")
                traceback.print_exc()
    
    def handle_image_update(self, widget: 'WidgetItem', key: str, value: str):
        relative_path = value
        if self.current_project and Path(value).is_absolute():
            try:
                root_data = self.current_project.data_roots[0] if self.current_project.data_roots else self.current_project.root
                relative_path = Path(value).relative_to(root_data).as_posix()
                if not relative_path.startswith('base64:') and not relative_path.startswith('/'):
                    relative_path = '/' + relative_path
            except ValueError:
                if self.current_otui_path:
                    try:
                        relative_path = Path(value).relative_to(Path(self.current_otui_path).parent).as_posix()
                    except ValueError:
                        relative_path = value
        
        widget.set_otui_prop(key, relative_path)
        self.props_editor.load_props()
        self.canvas.save_state()

    def list_current_directory(self):
        if not self.current_project: return
        
        self.module_files_list.clear()
        
        try:
            display_path = self.current_dir.relative_to(self.current_project.root) if self.current_dir.is_relative_to(self.current_project.root) else self.current_dir.name
            self.current_path_label.setText(str(display_path))
        except ValueError:
            self.current_path_label.setText(str(self.current_dir.name))

        if self.current_dir != self.current_project.root and self.current_dir != self.current_project.root.parent:
            back_item = QListWidgetItem(".. (Voltar)")
            back_item.setData(Qt.UserRole, str(self.current_dir.parent))
            self.module_files_list.addItem(back_item)
            
        try:
            items = sorted(list(self.current_dir.iterdir()), key=lambda p: (not p.is_dir(), p.name.lower()))
            for item_path in items:
                if item_path.name.startswith('.'): continue
                if item_path.is_dir():
                    list_item = QListWidgetItem(f"📁 {item_path.name}")
                elif item_path.suffix.lower() in (".otui", ".otmd"):
                    list_item = QListWidgetItem(f"📄 {item_path.name}")
                elif item_path.suffix.lower() == ".lua":
                    list_item = QListWidgetItem(f"📜 {item_path.name}")
                else:
                    continue
                    
                list_item.setData(Qt.UserRole, str(item_path))
                self.module_files_list.addItem(list_item)
        except Exception as e:
            QMessageBox.warning(self, "Erro de Permissão", f"Não foi possível listar arquivos em:\n{self.current_dir}\n\nErro: {e}")

    def new_project(self):
        folder = QFileDialog.getExistingDirectory(self, "Selecione a pasta raiz do novo projeto")
        if not folder: return
        
        try:
            (Path(folder) / 'data' / 'images').mkdir(parents=True, exist_ok=True)
            (Path(folder) / 'data' / 'layouts').mkdir(parents=True, exist_ok=True)
            self.canvas.scene.clear()
            self._open_project(folder)
            QMessageBox.information(self, "Sucesso", "Novo projeto criado com sucesso!")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Não foi possível criar o novo projeto:\n{e}")

    def create_otui(self):
        if not self.current_project:
            QMessageBox.warning(self, "Aviso", "Por favor, abra ou crie um projeto primeiro.")
            return

        dialog = StyledInputDialog(self, "Criar OTUI", "Nome do novo arquivo OTUI (ex: mywindow.otui):")
        name, ok = dialog.get_text_and_result()
        
        if ok and name:
            if not name.lower().endswith(('.otui', '.otmd')): name += '.otui'
            
            otui_path_base = self.current_project.root / 'data' / 'layouts'
            if not otui_path_base.is_dir():
                otui_path_base = self.current_project.root
            
            otui_path = otui_path_base / name
            
            if otui_path.exists():
                reply = QMessageBox.question(self, "Arquivo Existente", f"O arquivo {name} já existe. Deseja substituí-lo?", QMessageBox.Yes | QMessageBox.No)
                if reply == QMessageBox.No: return
            
            try:
                initial_content = "UIWindow\n  id: main\n  size: 400 300\n"
                otui_path.write_text(initial_content, encoding='utf-8')
                
                self.current_project.index_structure()
                self.current_dir = otui_path.parent
                self.list_current_directory()
                self.current_otui_path = str(otui_path)
                
                self.parser.load_to_canvas(self.canvas, [otui_path])
                self.update_window_title()
                QMessageBox.information(self, "Sucesso", f"Arquivo '{name}' criado com sucesso!")
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Não foi possível criar o arquivo:\n{e}")

    def open_otui(self):
        if not self.current_project:
            QMessageBox.warning(self, "Aviso", "Por favor, abra um projeto primeiro.")
            return
            
        path, _ = QFileDialog.getOpenFileName(self, "Abrir OTUI", str(self.current_dir), "OTUI Files (*.otui *.otmd)")
        if path:
            self.current_otui_path = path
            try:
                self.parser.load_to_canvas(self.canvas, [Path(path)])
                self._save_project_state()
                self.project_changed.emit()
            except Exception as e:
                QMessageBox.critical(self, "Erro ao carregar OTUI", f"Ocorreu um erro: {e}")
                traceback.print_exc()

    def _save_project_state(self):
        if not self.current_project: return
        payload = {"current_otui": self.current_otui_path, "canvas": self.canvas.serialize()}
        self.current_project.save_state(payload)

    def _open_project(self, folder: str, auto_from_workspace: bool = False):
        folder_path = Path(folder)
        if not folder_path.is_dir():
            QMessageBox.critical(self, "Erro", "A pasta selecionada não existe.")
            return
        
        self.current_project = ModuleProject(folder)
        self._save_workspace()
        self.current_dir = self.current_project.root
        self.list_current_directory()
        
        initial_otui_path = None
        restored = auto_from_workspace and self.current_project.last_state.get("current_otui")
        
        if restored:
            initial_otui_path = self.current_project.last_state["current_otui"]
            self.canvas.restore_state(self.current_project.last_state.get("canvas"))
        else:
            initial_otui_path = self.current_project.initial_otui
            self.canvas.scene.clear()
            
        if initial_otui_path and Path(initial_otui_path).exists():
            self.current_otui_path = str(initial_otui_path)
            if not restored:
                self.parser.load_to_canvas(self.canvas, [Path(initial_otui_path)])
        
        self.project_changed.emit()
        if not auto_from_workspace:
            QMessageBox.information(self, "Info", "Módulo carregado com sucesso!")

    def load_client_module(self):
        folder = QFileDialog.getExistingDirectory(self, "Selecione a pasta do módulo", str(self.current_dir))
        if folder:
            self._open_project(folder)

    def closeEvent(self, event: Any):
        if self.current_project:
            self._save_project_state()
        self._save_workspace()
        super().closeEvent(event)

    def update_window_title(self):
        title = "OTUI Editor - PRO"
        if self.current_project:
            title += f" - {self.current_project.root.name}"
            if self.current_otui_path:
                title += f" - [{Path(self.current_otui_path).name}]"
        self.setWindowTitle(title)

def save_otui(filepath: str, widgets: List['WidgetItem'], project: 'ModuleProject'):
    
    data_root = project.root / 'data' if (project.root / 'data').is_dir() else project.root
    
    images_dir_candidates = [project.root / p for p in project.mod_data.get('images-dir', [])]
    if not images_dir_candidates:
        images_dir_candidates.append(data_root / "images")
    
    images_dir = images_dir_candidates[0]
    images_dir.mkdir(parents=True, exist_ok=True)

    def get_relative_image_path(value: str) -> str:
        if not value or value.startswith('base64:') or value.startswith('/'):
            return value

        src_path_str = project.resolver.resolve(value, Path(filepath).parent)
        if not src_path_str:
            return value
        
        src_path = Path(src_path_str)
        target_path = images_dir / src_path.name
        
        try:
            if not target_path.exists() or not src_path.samefile(target_path):
                shutil.copy2(src_path, target_path)
            
            relative_img_path = target_path.relative_to(data_root)
            return f"/{relative_img_path.as_posix()}"
        except Exception:
            return value

    def write_widget(f, w: 'WidgetItem', indent: int = 0):
        pad = "  " * indent
        inherit_str = f" < {w.otui_props.get('inherit', '')}" if w.otui_props.get('inherit') else ""
        f.write(f"{pad}{w.widget_type}{inherit_str}\n")
        
        props_to_write = w.otui_props.get('props', {})
        
        if 'id' in props_to_write:
            f.write(f"{pad}  id: {props_to_write['id']}\n")
        if 'pos' in props_to_write:
            f.write(f"{pad}  pos: {props_to_write['pos']}\n")
        if 'size' in props_to_write:
            f.write(f"{pad}  size: {props_to_write['size']}\n")

        for key in sorted(props_to_write.keys()):
            if key in ['id', 'pos', 'size']: continue
            value = props_to_write[key]

            value_to_write = value
            if key in ['image-source', 'icon-source'] and value:
                value_to_write = get_relative_image_path(value)
            
            f.write(f"{pad}  {key}: {value_to_write}\n")
        
        for state_name, state_value in w.otui_props.get('states', {}).items():
            if state_value:
                f.write(f"{pad}  ${state_name}:\n")
                f.write(f"{pad}    {state_value}\n")

        for event_name, event_value in w.otui_props.get('events', {}).items():
            if event_value:
                f.write(f"{pad}  @{event_name}:\n")
                f.write(f"{pad}    {event_value}\n")
        
        f.write("\n")

        sorted_children = sorted(w.children_widgets, key=lambda child: (child.pos().y(), child.pos().x()))
        for child in sorted_children:
            write_widget(f, child, indent + 1)

    roots = [w for w in widgets if isinstance(w, WidgetItem) and not w.parentItem()]
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(f'// OTUI Generated by OTUI Editor {os.linesep}')
        f.write(f'// Project: {project.root.name} {os.linesep}')
        f.write(f'// Source: {Path(filepath).name} {os.linesep}{os.linesep}')
        
        sorted_roots = sorted(roots, key=lambda w: (w.pos().y(), w.pos().x()))
        for w in sorted_roots:
            write_widget(f, w)


if __name__ == "__main__":
    app = QApplication.instance() or QApplication(sys.argv)
        
    try:
        editor = OTUIEditor()
        editor.show()
        sys.exit(app.exec())
    except Exception:
        sys.exit(1)