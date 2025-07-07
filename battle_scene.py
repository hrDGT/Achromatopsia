from PySide6.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsPixmapItem, QGraphicsTextItem
from PySide6.QtCore import Qt, QRectF, QPointF, QSize
from PySide6.QtGui import QPixmap, QKeyEvent, QPainter, QColor, QMovie, QTransform, QFont


class BattleScene(QGraphicsView):
    def __init__(self):
        super().__init__()

        # Настройки окна
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.showFullScreen()
        self.fullscreen = True

        # Настройки сцены
        self.setScene(QGraphicsScene(self))
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setWindowTitle("Battle Scene")
        self.setRenderHint(QPainter.Antialiasing)
        self.setRenderHint(QPainter.SmoothPixmapTransform)

        # Параметры нашего персонажа
        self.character_x = 0
        self.character_y = 20
        self.character_width = 700
        self.character_height = 700

        # Параметры противника
        self.enemy_x = 800
        self.enemy_y = 20
        self.enemy_width = 700
        self.enemy_height = 700

        # Параметры заклинания персонажа
        self.character_spell_x = 170
        self.character_spell_y = 300
        self.character_spell_width = 1400
        self.character_spell_height = 200

        # Параметры заклинания противника
        self.enemy_spell_x = 70
        self.enemy_spell_y = 300
        self.enemy_spell_width = 1230
        self.enemy_spell_height = 200

        # Параметры health bar'ов
        self.health_bar_width = 336  # 42*2 увеличенный размер
        self.health_bar_height = 56  # 7*2

        # Параметры mana bar'ов
        self.mana_bar_width = 336  # Такая же ширина как у health bar
        self.mana_bar_height = 28   # Половина высоты health bar

        # Загрузка фона
        self.background_pixmap = QPixmap("assets/backgrounds/battle.png")
        if self.background_pixmap.isNull():
            self.background_pixmap = QPixmap(self.size())
            self.background_pixmap.fill(Qt.darkGray)

        # Создаем элементы сцены
        self.background = QGraphicsPixmapItem()
        self.scene().addItem(self.background)

        self.character_item = QGraphicsPixmapItem()
        self.scene().addItem(self.character_item)

        self.enemy_item = QGraphicsPixmapItem()
        self.scene().addItem(self.enemy_item)

        # Health bars
        self.character_health_bar = QGraphicsPixmapItem()
        self.scene().addItem(self.character_health_bar)
        self.character_health_bar.setZValue(20)

        self.enemy_health_bar = QGraphicsPixmapItem()
        self.scene().addItem(self.enemy_health_bar)
        self.enemy_health_bar.setZValue(20)

        # Mana bars
        self.character_mana_bar = QGraphicsPixmapItem()
        self.scene().addItem(self.character_mana_bar)
        self.character_mana_bar.setZValue(20)

        self.enemy_mana_bar = QGraphicsPixmapItem()
        self.scene().addItem(self.enemy_mana_bar)
        self.enemy_mana_bar.setZValue(20)

        # Анимации
        self.spell_item = QGraphicsPixmapItem()
        self.scene().addItem(self.spell_item)
        self.spell_item.setVisible(False)

        self.enemy_spell_item = QGraphicsPixmapItem()
        self.scene().addItem(self.enemy_spell_item)
        self.enemy_spell_item.setVisible(False)

        self.enemy_damage_item = QGraphicsPixmapItem()
        self.scene().addItem(self.enemy_damage_item)
        self.enemy_damage_item.setVisible(False)
        self.enemy_damage_item.setZValue(10)

        self.character_damage_item = QGraphicsPixmapItem()
        self.scene().addItem(self.character_damage_item)
        self.character_damage_item.setVisible(False)
        self.character_damage_item.setZValue(10)

        # Состояния
        self.is_attacking = False
        self.is_casting = False
        self.is_enemy_attacking = False
        self.is_enemy_casting = False
        self.is_enemy_taking_damage = False
        self.is_character_taking_damage = False

        # Здоровье и мана
        self.character_health = 20
        self.enemy_health = 20
        self.character_mana = 20
        self.enemy_mana = 20

        # Текстовые элементы для отображения значений
        self.character_health_text = QGraphicsTextItem()
        self.scene().addItem(self.character_health_text)
        self.character_health_text.setZValue(30)

        self.character_mana_text = QGraphicsTextItem()
        self.scene().addItem(self.character_mana_text)
        self.character_mana_text.setZValue(30)

        self.enemy_health_text = QGraphicsTextItem()
        self.scene().addItem(self.enemy_health_text)
        self.enemy_health_text.setZValue(30)

        self.enemy_mana_text = QGraphicsTextItem()
        self.scene().addItem(self.enemy_mana_text)
        self.enemy_mana_text.setZValue(30)

        # Настройка шрифта
        self.text_font = QFont("Arial", 16, QFont.Bold)
        self.text_font.setBold(True)

        # Цвета текста
        self.health_color = QColor(255, 50, 50)  # Красный для здоровья
        self.mana_color = QColor(50, 150, 255)    # Синий для маны

        self.character_health_text.setFont(self.text_font)
        self.character_mana_text.setFont(self.text_font)
        self.enemy_health_text.setFont(self.text_font)
        self.enemy_mana_text.setFont(self.text_font)

        self.character_health_text.setDefaultTextColor(self.health_color)
        self.character_mana_text.setDefaultTextColor(self.mana_color)
        self.enemy_health_text.setDefaultTextColor(self.health_color)
        self.enemy_mana_text.setDefaultTextColor(self.mana_color)

        self.spell_icons = []  # Инициализация списка иконок заклинаний

        self.setup_animations()
        self.setup_health_bars()
        self.setup_mana_bars()
        self.create_spell_panel()
        self.fit_background()
        self.update_text_values()  # Инициализация текстовых значений

    def setup_health_bars(self):
        """Инициализация health bar'ов"""
        # Загрузка изображений
        health_bar_img = QPixmap("assets/gui/hp_bar1.png")

        # Если изображение не загрузилось, создаем цветные прямоугольники
        if health_bar_img.isNull():
            # Зеленый для персонажа
            char_health = QPixmap(self.health_bar_width, self.health_bar_height)
            char_health.fill(QColor(0, 255, 0))  # Зеленый
            # Красный для противника
            enemy_health = QPixmap(self.health_bar_width, self.health_bar_height)
            enemy_health.fill(QColor(255, 0, 0))  # Красный
        else:
            # Используем одно изображение для обоих
            char_health = health_bar_img.copy()
            enemy_health = health_bar_img.copy()

        # Масштабирование
        char_health = char_health.scaled(
            self.health_bar_width, self.health_bar_height,
            Qt.IgnoreAspectRatio, Qt.SmoothTransformation
        )
        enemy_health = enemy_health.scaled(
            self.health_bar_width, self.health_bar_height,
            Qt.IgnoreAspectRatio, Qt.SmoothTransformation
        )

        # Установка health bar'ов
        self.character_health_bar.setPixmap(char_health)
        self.enemy_health_bar.setPixmap(enemy_health)

        # Позиционирование
        self.update_health_bars_positions()

    def setup_mana_bars(self):
        """Инициализация mana bar'ов"""
        # Загрузка изображений
        mana_bar_img = QPixmap("assets/gui/mana_bar1.png")

        # Если изображение не загрузилось, создаем цветные прямоугольники
        if mana_bar_img.isNull():
            # Синий для персонажа
            char_mana = QPixmap(self.mana_bar_width, self.mana_bar_height)
            char_mana.fill(QColor(0, 0, 255))  # Синий
            # Фиолетовый для противника
            enemy_mana = QPixmap(self.mana_bar_width, self.mana_bar_height)
            enemy_mana.fill(QColor(128, 0, 255))  # Фиолетовый
        else:
            # Используем одно изображение для обоих
            char_mana = mana_bar_img.copy()
            enemy_mana = mana_bar_img.copy()

        # Масштабирование
        char_mana = char_mana.scaled(
            self.mana_bar_width, self.mana_bar_height,
            Qt.IgnoreAspectRatio, Qt.SmoothTransformation
        )
        enemy_mana = enemy_mana.scaled(
            self.mana_bar_width, self.mana_bar_height,
            Qt.IgnoreAspectRatio, Qt.SmoothTransformation
        )

        # Установка mana bar'ов
        self.character_mana_bar.setPixmap(char_mana)
        self.enemy_mana_bar.setPixmap(enemy_mana)

        # Позиционирование
        self.update_mana_bars_positions()

    def update_health_bars_positions(self):
        """Обновление позиций health bar'ов и текста относительно панели заклинаний"""
        if not hasattr(self, 'spell_panel'):
            return

        # Получаем позицию и размеры панели заклинаний
        panel_pos = self.spell_panel.pos()
        panel_width = self.spell_panel.pixmap().width()
        panel_height = self.spell_panel.pixmap().height()

        # Отступ от панели заклинаний
        offset = 20

        # Персонаж (левый бар)
        char_bar_x = panel_pos.x() - self.health_bar_width - offset + 410
        char_bar_y = panel_pos.y() + (panel_height - self.health_bar_height - self.mana_bar_height - 5) / 2
        self.character_health_bar.setPos(char_bar_x, char_bar_y)

        # Текст здоровья персонажа (справа от бара)
        health_text_rect = self.character_health_text.boundingRect()
        self.character_health_text.setPos(
            char_bar_x + self.health_bar_width + 5,
            char_bar_y + (self.health_bar_height - health_text_rect.height()) / 2
        )

        # Противник (правый бар)
        enemy_bar_x = panel_pos.x() + panel_width + offset - 410
        enemy_bar_y = panel_pos.y() + (panel_height - self.health_bar_height - self.mana_bar_height - 5) / 2
        self.enemy_health_bar.setPos(enemy_bar_x, enemy_bar_y)

        # Текст здоровья противника (слева от бара)
        health_text_rect = self.enemy_health_text.boundingRect()
        self.enemy_health_text.setPos(
            enemy_bar_x - health_text_rect.width() - 5,
            enemy_bar_y + (self.health_bar_height - health_text_rect.height()) / 2
        )

    def update_mana_bars_positions(self):
        """Обновление позиций mana bar'ов и текста относительно панели заклинаний"""
        if not hasattr(self, 'spell_panel'):
            return

        # Получаем позицию health bar'ов
        char_health_pos = self.character_health_bar.pos()
        enemy_health_pos = self.enemy_health_bar.pos()

        # Персонаж (под health bar)
        char_bar_x = char_health_pos.x()
        char_bar_y = char_health_pos.y() + self.health_bar_height + 5
        self.character_mana_bar.setPos(char_bar_x, char_bar_y)

        # Текст маны персонажа (справа от бара)
        mana_text_rect = self.character_mana_text.boundingRect()
        self.character_mana_text.setPos(
            char_bar_x + self.mana_bar_width + 5,
            char_bar_y + (self.mana_bar_height - mana_text_rect.height()) / 2
        )

        # Противник (под health bar)
        enemy_bar_x = enemy_health_pos.x()
        enemy_bar_y = enemy_health_pos.y() + self.health_bar_height + 5
        self.enemy_mana_bar.setPos(enemy_bar_x, enemy_bar_y)

        # Текст маны противника (слева от бара)
        mana_text_rect = self.enemy_mana_text.boundingRect()
        self.enemy_mana_text.setPos(
            enemy_bar_x - mana_text_rect.width() - 5,
            enemy_bar_y + (self.mana_bar_height - mana_text_rect.height()) / 2
        )

    def update_text_values(self):
        """Обновление текстовых значений здоровья и маны"""
        self.character_health_text.setPlainText(f"{self.character_health}")
        self.character_mana_text.setPlainText(f"{self.character_mana}")
        self.enemy_health_text.setPlainText(f"{self.enemy_health}")
        self.enemy_mana_text.setPlainText(f"{self.enemy_mana}")

        # Обновляем позиции текста после изменения значений
        self.update_health_bars_positions()
        self.update_mana_bars_positions()

    def setup_animations(self):
        """Настройка анимаций"""
        # Наш персонаж (idle)
        self.idle_movie = QMovie("assets/animations/idle.gif")
        self.idle_movie.setScaledSize(QSize(self.character_width, self.character_height))
        self.idle_movie.frameChanged.connect(self.update_idle_frame)
        self.idle_movie.start()

        # Наш персонаж (атака)
        self.attack_movie = QMovie("assets/animations/attack.gif")
        self.attack_movie.setScaledSize(QSize(self.character_width, self.character_height))
        self.attack_movie.frameChanged.connect(self.update_attack_frame)

        # Противник (idle)
        self.enemy_movie = QMovie("assets/animations/enemy_idle.gif")
        self.enemy_movie.setScaledSize(QSize(self.enemy_width, self.enemy_height))
        self.enemy_movie.frameChanged.connect(self.update_enemy_frame)
        self.enemy_movie.start()

        # Противник (атака)
        self.enemy_attack_movie = QMovie("assets/animations/enemy_attack.gif")
        self.enemy_attack_movie.setScaledSize(QSize(self.enemy_width, self.enemy_height))
        self.enemy_attack_movie.frameChanged.connect(self.update_enemy_attack_frame)

        # Заклинания персонажа
        self.spell_movie = QMovie("assets/animations/tornado.gif")
        self.spell_movie.setScaledSize(QSize(self.character_spell_width, self.character_spell_height))
        self.spell_movie.frameChanged.connect(self.update_spell_frame)

        # Заклинания противника
        self.enemy_spell_movie = QMovie("assets/animations/fireball_2.gif")
        self.enemy_spell_movie.setScaledSize(QSize(self.enemy_spell_width, self.enemy_spell_height))
        self.enemy_spell_movie.frameChanged.connect(self.update_enemy_spell_frame)

        # Урон
        self.enemy_damage_movie = QMovie("assets/animations/hurt.gif")
        self.enemy_damage_movie.setScaledSize(QSize(self.enemy_width, self.enemy_height))
        self.enemy_damage_movie.frameChanged.connect(self.update_enemy_damage_frame)

        self.character_damage_movie = QMovie("assets/animations/hurt.gif")
        self.character_damage_movie.setScaledSize(QSize(self.character_width, self.character_height))
        self.character_damage_movie.frameChanged.connect(self.update_character_damage_frame)

        # Установка позиций
        self.character_item.setPos(self.character_x, self.character_y)
        self.character_damage_item.setPos(self.character_x, self.character_y)
        self.enemy_item.setPos(self.enemy_x, self.enemy_y)
        self.enemy_damage_item.setPos(self.enemy_x, self.enemy_y)
        # Заклинания
        self.spell_item.setPos(self.character_spell_x, self.character_spell_y)
        self.enemy_spell_item.setPos(self.enemy_spell_x, self.enemy_spell_y)
        self.update_health_bars_positions()
        self.update_mana_bars_positions()

    def update_idle_frame(self, frame_number):
        self.character_item.setPixmap(self.idle_movie.currentPixmap())

    def update_attack_frame(self, frame_number):
        self.character_item.setPixmap(self.attack_movie.currentPixmap())
        if frame_number == self.attack_movie.frameCount() - 1:
            self.stop_attack_animation()

    def update_enemy_frame(self, frame_number):
        self.enemy_item.setPixmap(self.enemy_movie.currentPixmap())

    def update_enemy_attack_frame(self, frame_number):
        self.enemy_item.setPixmap(self.enemy_attack_movie.currentPixmap())
        if frame_number == self.enemy_attack_movie.frameCount() - 1:
            self.stop_enemy_attack_animation()

    def update_spell_frame(self, frame_number):
        self.spell_item.setPixmap(self.spell_movie.currentPixmap())
        if frame_number == self.spell_movie.frameCount() - 1:
            self.stop_spell_animation()

    def update_enemy_spell_frame(self, frame_number):
        self.enemy_spell_item.setPixmap(self.enemy_spell_movie.currentPixmap())
        if frame_number == self.enemy_spell_movie.frameCount() - 1:
            self.stop_enemy_spell_animation()

    def update_enemy_damage_frame(self, frame_number):
        self.enemy_damage_item.setPixmap(self.enemy_damage_movie.currentPixmap())
        if frame_number == self.enemy_damage_movie.frameCount() - 1:
            self.stop_enemy_damage_animation()

    def update_character_damage_frame(self, frame_number):
        self.character_damage_item.setPixmap(self.character_damage_movie.currentPixmap())
        if frame_number == self.character_damage_movie.frameCount() - 1:
            self.stop_character_damage_animation()

    def play_attack_animation(self):
        if self.is_attacking:
            return
        self.idle_movie.stop()
        self.attack_movie.start()
        self.attack_movie.jumpToFrame(0)
        self.is_attacking = True

    def play_spell_animation(self):
        if self.is_casting:
            return
        self.spell_item.setVisible(True)
        self.spell_movie.start()
        self.spell_movie.jumpToFrame(0)
        self.is_casting = True

    def stop_attack_animation(self):
        self.attack_movie.stop()
        self.is_attacking = False
        self.idle_movie.start()
        self.play_spell_animation()

    def stop_spell_animation(self):
        self.spell_movie.stop()
        self.spell_item.setVisible(False)
        self.is_casting = False
        self.play_enemy_damage_animation()

    def play_enemy_damage_animation(self):
        if self.is_enemy_taking_damage:
            return
        self.enemy_item.setVisible(False)
        self.enemy_damage_item.setVisible(True)
        self.enemy_damage_movie.start()
        self.enemy_damage_movie.jumpToFrame(0)
        self.is_enemy_taking_damage = True

    def stop_enemy_damage_animation(self):
        self.enemy_damage_movie.stop()
        self.enemy_damage_item.setVisible(False)
        self.enemy_item.setVisible(True)
        self.is_enemy_taking_damage = False

    def play_character_damage_animation(self):
        if self.is_character_taking_damage:
            return
        self.character_item.setVisible(False)
        self.character_damage_item.setVisible(True)
        self.character_damage_movie.start()
        self.character_damage_movie.jumpToFrame(0)
        self.is_character_taking_damage = True

    def stop_character_damage_animation(self):
        self.character_damage_movie.stop()
        self.character_damage_item.setVisible(False)
        self.character_item.setVisible(True)
        self.is_character_taking_damage = False

    def play_enemy_attack_animation(self):
        if self.is_enemy_attacking:
            return
        self.enemy_movie.stop()
        self.enemy_attack_movie.start()
        self.enemy_attack_movie.jumpToFrame(0)
        self.is_enemy_attacking = True

    def stop_enemy_attack_animation(self):
        self.enemy_attack_movie.stop()
        self.is_enemy_attacking = False
        self.enemy_movie.start()
        self.play_enemy_spell_animation()

    def play_enemy_spell_animation(self):
        if self.is_enemy_casting:
            return
        self.enemy_spell_item.setVisible(True)
        self.enemy_spell_movie.start()
        self.enemy_spell_movie.jumpToFrame(0)
        self.is_enemy_casting = True

    def stop_enemy_spell_animation(self):
        self.enemy_spell_movie.stop()
        self.enemy_spell_item.setVisible(False)
        self.is_enemy_casting = False
        self.play_character_damage_animation()

    def create_spell_panel(self):
        icon_size = 96
        margin = 500
        spacing = 15
        panel_width = margin * 2 + icon_size * 5 + spacing * 4
        panel_height = icon_size + 30

        panel_pixmap = QPixmap("assets/gui/spell_panel.png")
        if panel_pixmap.isNull():
            panel_pixmap = QPixmap(panel_width, panel_height)
            panel_pixmap.fill(Qt.darkGray)

        self.spell_panel = QGraphicsPixmapItem(panel_pixmap.scaled(
            panel_width, panel_height,
            Qt.IgnoreAspectRatio, Qt.SmoothTransformation
        ))
        self.scene().addItem(self.spell_panel)

        for i in range(5):
            try:
                icon_pixmap = QPixmap(f"assets/spells/spell_icon{i+1}.jpg")
                if icon_pixmap.isNull():
                    icon_pixmap = QPixmap(icon_size, icon_size)
                    icon_pixmap.fill(Qt.red if i % 2 else Qt.blue)

                icon = SpellIconItem(icon_pixmap.scaled(
                    icon_size, icon_size,
                    Qt.IgnoreAspectRatio, Qt.SmoothTransformation
                ), i+1, self.spell_panel)

                x_pos = margin + i * (icon_size + spacing)
                icon.setPos(x_pos, 15)
                icon.setAcceptHoverEvents(True)
                self.spell_icons.append(icon)
            except:
                print(f"Failed to load spell icon {i+1}")

    def fit_background(self):
        if not hasattr(self, 'background_pixmap') or self.background_pixmap.isNull():
            return

        view_size = self.viewport().size()
        scaled_pixmap = self.background_pixmap.scaled(
            view_size,
            Qt.KeepAspectRatioByExpanding,
            Qt.SmoothTransformation
        )

        self.background.setPixmap(scaled_pixmap)
        self.setSceneRect(QRectF(scaled_pixmap.rect()))

        # Сначала обновляем позицию панели
        self.update_panel_position()
        # Затем обновляем позиции баров относительно панели
        self.update_health_bars_positions()
        self.update_mana_bars_positions()

    def update_panel_position(self):
        if not hasattr(self, 'spell_panel'):
            return

        view_rect = self.viewport().rect()
        panel_width = self.spell_panel.pixmap().width()
        panel_height = self.spell_panel.pixmap().height()

        panel_x = (view_rect.width() - panel_width) / 2
        panel_y = view_rect.height() - panel_height - 10

        self.spell_panel.setPos(panel_x, panel_y)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.fit_background()

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key_Escape:
            self.close()
        elif event.key() == Qt.Key_F11:
            self.toggle_fullscreen()
        elif event.key() == Qt.Key_A:
            self.play_attack_animation()
        elif event.key() == Qt.Key_S:
            self.play_enemy_attack_animation()
        # Управление здоровьем и маной
        elif event.key() == Qt.Key_1:  # Увеличить здоровье персонажа
            self.character_health += 1
            self.update_text_values()
        elif event.key() == Qt.Key_2:  # Уменьшить здоровье персонажа
            self.character_health = max(0, self.character_health - 1)
            self.update_text_values()
        elif event.key() == Qt.Key_3:  # Увеличить ману персонажа
            self.character_mana += 1
            self.update_text_values()
        elif event.key() == Qt.Key_4:  # Уменьшить ману персонажа
            self.character_mana = max(0, self.character_mana - 1)
            self.update_text_values()
        elif event.key() == Qt.Key_5:  # Увеличить здоровье врага
            self.enemy_health += 1
            self.update_text_values()
        elif event.key() == Qt.Key_6:  # Уменьшить здоровье врага
            self.enemy_health = max(0, self.enemy_health - 1)
            self.update_text_values()
        elif event.key() == Qt.Key_7:  # Увеличить ману врага
            self.enemy_mana += 1
            self.update_text_values()
        elif event.key() == Qt.Key_8:  # Уменьшить ману врага
            self.enemy_mana = max(0, self.enemy_mana - 1)
            self.update_text_values()
        else:
            super().keyPressEvent(event)

    def toggle_fullscreen(self):
        if self.fullscreen:
            self.setCursor(Qt.ArrowCursor)
        else:
            self.setCursor(Qt.BlankCursor)
        self.fullscreen = not self.fullscreen


class SpellIconItem(QGraphicsPixmapItem):
    def __init__(self, pixmap, spell_id, parent=None):
        super().__init__(pixmap, parent)
        self.spell_id = spell_id
        self.normal_opacity = 1.0
        self.pressed_opacity = 0.7
        self.hover_opacity = 0.9
        self.setOpacity(self.normal_opacity)

    def mousePressEvent(self, event):
        self.setOpacity(self.pressed_opacity)
        print(f"Spell {self.spell_id} pressed!")
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        self.setOpacity(self.normal_opacity)
        print(f"Spell {self.spell_id} activated!")
        super().mouseReleaseEvent(event)

    def hoverEnterEvent(self, event):
        self.setOpacity(self.hover_opacity)
        self.setCursor(Qt.PointingHandCursor)
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        self.setOpacity(self.normal_opacity)
        self.setCursor(Qt.ArrowCursor)
        super().hoverLeaveEvent(event)
