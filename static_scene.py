from __future__ import annotations

import json, sys
from pathlib import Path
from typing import Callable, List

from PySide6.QtCore import Qt, QPointF, Signal
from PySide6.QtGui import QColor, QMovie, QPainter, QPixmap
from PySide6.QtWidgets import (
    QApplication, QGraphicsItem, QGraphicsPixmapItem, QGraphicsRectItem,
    QGraphicsScene, QGraphicsSimpleTextItem, QGraphicsView, QScrollBar,
    QPushButton, QVBoxLayout, QWidget, QGraphicsProxyWidget
)

GAME_W, GAME_H = 1600, 900
ICON_SIZE = 96

PANEL_MARGIN_X, ICON_SPACING, MAX_PANEL_ICONS, PANEL_OFFSET_Y = 500, 15, 4, 30
MENU_W, MENU_MARGIN, VISIBLE_ICONS, MENU_ICON_SPACING         = 260, 20, 4, 30
MENU_BG_COLOR, MENU_TEXT_COLOR = QColor(20,20,20,200), QColor(220,220,220)
SCROLL_STEP, SCROLLBAR_W = 40, 16

def load_spells(path="assets/spells/spells.json")->dict:
    try: return json.load(Path(path).open(encoding="utf-8"))
    except Exception as e: print("load_spells:", e); return {}

class MenuIcon(QGraphicsPixmapItem):
    """Иконка в меню → добавление в панель."""
    def __init__(self,pix:QPixmap,key:str,cb:Callable[[str],bool])->None:
        super().__init__(pix); self.key=key; self._cb=cb
        self.label:QGraphicsSimpleTextItem|None=None
        self.setAcceptedMouseButtons(Qt.LeftButton); self.setCursor(Qt.PointingHandCursor)
    def mousePressEvent(self,e):                         
        if e.button()==Qt.LeftButton and self._cb(self.key):
            self.setVisible(False); self.label.setVisible(False)

class PanelIcon(QGraphicsPixmapItem):
    """Иконка в панели → возврат в меню."""
    def __init__(self,pix:QPixmap,key:str,cb:Callable[[str],None])->None:
        super().__init__(pix); self.key=key; self._cb=cb
        self.setAcceptedMouseButtons(Qt.LeftButton); self.setCursor(Qt.PointingHandCursor)
    def mousePressEvent(self,e):                            
        if e.button()==Qt.LeftButton: self._cb(self.key)

class StaticBattleView(QGraphicsView):
    battleReady = Signal(list)

    def __init__(self, enemy_data, max_spells=4):
        super().__init__()
        self.enemy_data = enemy_data
        self.max_spells = max_spells
        self.scene = QGraphicsScene(0, 0, GAME_W, GAME_H)
        self.setScene(self.scene)
        self.setRenderHint(QPainter.Antialiasing)
        self.setRenderHint(QPainter.SmoothPixmapTransform)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setMinimumSize(400, 300)

        self.spells = load_spells()
        self.all_keys: List[str] = list(self.spells.keys())[:max_spells]  
        self.panel_keys: List[str] = []                
        self.menu_keys: List[str] = self.all_keys.copy() 
        
        self.menu_viewport: QGraphicsRectItem | None = None
        self.content_item: QGraphicsRectItem | None = None
        self.scrollbar: QScrollBar | None = None
        self.panel_item: QGraphicsPixmapItem | None = None
        self.done_btn: QPushButton | None = None
        self.done_btn_proxy: QGraphicsProxyWidget | None = None

        self._bg(enemy_data.get('background', 'battle.png'))
        self._hero()
        self._panel()
        self._build_menu()
        self._build_done_btn()

    def resizeEvent(self, event):
        """Масштабирует сцену при изменении размера окна."""
        super().resizeEvent(event)
        self.fitInView(self.sceneRect(), Qt.KeepAspectRatio)

    def wheelEvent(self,e):                              
        if self.menu_viewport and self.scrollbar:
            pos=self.mapToScene(e.position().toPoint())
            if self.menu_viewport.contains(self.menu_viewport.mapFromScene(pos)):
                d=e.angleDelta().y()
                if d: self.scrollbar.setValue(self.scrollbar.value()+(-SCROLL_STEP if d>0 else SCROLL_STEP)); e.accept(); return
        super().wheelEvent(e)

    def _bg(self, background_image):
        pm=QPixmap(f"assets/backgrounds/{background_image}")
        if pm.isNull():
            pm=QPixmap(GAME_W,GAME_H); pm.fill(Qt.darkGray)
        self.scene.addItem(QGraphicsPixmapItem(
            pm.scaled(GAME_W,GAME_H, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)))
    def _hero(self):
        m=QMovie("assets/animations/idle.gif"); m.jumpToFrame(0); pm=m.currentPixmap()
        if pm.isNull(): pm=QPixmap(700,700); pm.fill(Qt.blue)
        h=QGraphicsPixmapItem(pm.scaled(700,700,Qt.KeepAspectRatio,Qt.SmoothTransformation))
        h.setPos(0,20); h.setZValue(10); self.scene.addItem(h)

    def _panel(self):
        pm=QPixmap("assets/gui/spell_panel.png")
        if pm.isNull():
            w=PANEL_MARGIN_X*2+ICON_SIZE*MAX_PANEL_ICONS+ICON_SPACING*(MAX_PANEL_ICONS-1)
            h=ICON_SIZE+30; pm=QPixmap(w,h); pm.fill(Qt.darkGray)
        self.panel_item=QGraphicsPixmapItem(pm); self.panel_item.setZValue(20); self.scene.addItem(self.panel_item)
        self.panel_item.setPos((GAME_W-pm.width())/2, GAME_H-pm.height()-PANEL_OFFSET_Y)

    def _add_to_panel(self,key:str)->bool:
        if key in self.panel_keys or len(self.panel_keys)>=MAX_PANEL_ICONS: return False
        self.panel_keys.append(key); self.menu_keys.remove(key)
        self._rebuild_panel(); self._rebuild_menu(); self._update_done_btn(); return True

    def _remove_from_panel(self,key:str):
        if key not in self.panel_keys: return
        self.panel_keys.remove(key)
        idx=self.all_keys.index(key)
        insert_pos=0
        while insert_pos<len(self.menu_keys) and self.all_keys.index(self.menu_keys[insert_pos])<idx:
            insert_pos+=1
        self.menu_keys.insert(insert_pos,key)
        self._rebuild_panel(); self._rebuild_menu(); self._update_done_btn()

    def _rebuild_panel(self):
        for ch in list(self.panel_item.childItems()): ch.setParentItem(None)
        for i,key in enumerate(self.panel_keys):
            cfg=self.spells[key]; pix=QPixmap(f"assets/spells/{cfg['icon']}") or QPixmap(ICON_SIZE,ICON_SIZE)
            if pix.isNull(): pix.fill(Qt.green)
            icon = PanelIcon(pix.scaled(ICON_SIZE,ICON_SIZE,Qt.IgnoreAspectRatio,Qt.SmoothTransformation),
                 key,self._remove_from_panel)
            icon.setParentItem(self.panel_item)
            icon.setPos(PANEL_MARGIN_X+i*(ICON_SIZE+ICON_SPACING),15)

    def _build_menu(self):
        view_h=MENU_MARGIN*2+VISIBLE_ICONS*(ICON_SIZE+MENU_ICON_SPACING)-MENU_ICON_SPACING
        vp=QGraphicsRectItem(0,0,MENU_W,view_h); vp.setBrush(MENU_BG_COLOR); vp.setPen(Qt.NoPen)
        vp.setFlag(QGraphicsItem.ItemClipsChildrenToShape,True); vp.setZValue(15)
        self.scene.addItem(vp)
        vp.setPos(GAME_W-MENU_W-SCROLLBAR_W-MENU_MARGIN, MENU_MARGIN)
        self.menu_viewport=vp
        self.content_item=QGraphicsRectItem(0,0,0,0,vp)
        self._populate_menu()

        sb=QScrollBar(Qt.Vertical,self)
        sb.setGeometry(GAME_W-SCROLLBAR_W-MENU_MARGIN, MENU_MARGIN, SCROLLBAR_W, view_h)
        sb.valueChanged.connect(lambda v:self.content_item.setY(-v)); sb.show(); self.scrollbar=sb
        self._update_scroll()

    def _update_scroll(self):
        view_h=self.menu_viewport.rect().height(); cont_h=self.content_item.rect().height()
        self.scrollbar.setRange(0,max(0,int(cont_h-view_h))); self.scrollbar.setPageStep(int(view_h))

    def _rebuild_menu(self):
        for c in list(self.content_item.childItems()): c.setParentItem(None)
        self._populate_menu(); self._update_scroll()

    def _populate_menu(self):
        keys=self.menu_keys
        height=MENU_MARGIN*2+len(keys)*(ICON_SIZE+MENU_ICON_SPACING)-MENU_ICON_SPACING
        self.content_item.setRect(0,0,MENU_W,height)

        for i,key in enumerate(keys):
            cfg=self.spells[key]; y=MENU_MARGIN+i*(ICON_SIZE+MENU_ICON_SPACING)
            pix=QPixmap(f"assets/spells/{cfg['icon']}") or QPixmap(ICON_SIZE,ICON_SIZE)
            if pix.isNull(): pix.fill(Qt.red if i%2 else Qt.blue)
            icon = MenuIcon(pix.scaled(ICON_SIZE,ICON_SIZE,Qt.IgnoreAspectRatio,Qt.SmoothTransformation),
                key,self._add_to_panel)
            icon.setParentItem(self.content_item); icon.setPos((MENU_W-ICON_SIZE)/2, y)
            title=cfg.get("title") or cfg.get("name") or key
            lbl=QGraphicsSimpleTextItem(title,self.content_item); lbl.setBrush(MENU_TEXT_COLOR)
            lbl.setPos((MENU_W-lbl.boundingRect().width())/2, y+ICON_SIZE+4); icon.label=lbl

    def _build_done_btn(self):
        btn = QPushButton("Готово")
        btn_w, btn_h = MENU_W, 40
        x = GAME_W - MENU_W - SCROLLBAR_W - MENU_MARGIN
        view_h = MENU_MARGIN*2 + VISIBLE_ICONS*(ICON_SIZE + MENU_ICON_SPACING) - MENU_ICON_SPACING
        y = MENU_MARGIN + view_h + 10

        self.done_btn_proxy = self.scene.addWidget(btn)
        self.done_btn_proxy.setPos(x, y)
        self.done_btn_proxy.setZValue(25)

        btn.setFixedSize(btn_w, btn_h)
        btn.clicked.connect(self._on_done_clicked)
        self.done_btn = btn
        self._update_done_btn()

    def _update_done_btn(self):
        if self.done_btn:
            self.done_btn.setEnabled(len(self.panel_keys) == 4)

    def _on_done_clicked(self):
        """Обработка нажатия кнопки 'Готово'"""
        if len(self.panel_keys) == 4:
            self.battleReady.emit(self.panel_keys)
        else:
            print("Ошибка: должно быть выбрано ровно 4 заклинания")

class StaticBattleWidget(QWidget):
    battleReady = Signal(list)

    def __init__(self, enemy_data, max_spells=4, parent=None):
        super().__init__(parent)
        self.view = StaticBattleView(enemy_data, max_spells)

        self.view.battleReady.connect(self.handle_battle_ready)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.view)

    def handle_battle_ready(self, selected_spells):
        self.battleReady.emit(selected_spells)