from PySide6.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsPixmapItem, QGraphicsTextItem
from PySide6.QtCore import Qt, QRectF, QPointF, QSize, QTimer
from PySide6.QtGui import QPixmap, QKeyEvent, QPainter, QColor, QMovie, QTransform, QFont
import random


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
        self.character_spell_x = 90
        self.character_spell_y = 300
        self.character_spell_width = 1400
        self.character_spell_height = 200

        # Параметры заклинания противника
        self.enemy_spell_x = 60
        self.enemy_spell_y = 300
        self.enemy_spell_width = 1400
        self.enemy_spell_height = 200

        # Параметры health bar'ов
        self.health_bar_width = 336
        self.health_bar_height = 56

        # Параметры mana bar'ов
        self.mana_bar_width = 336
        self.mana_bar_height = 28

        # Максимальные значения
        self.character_health_max = 20
        self.character_mana_max = 20
        self.enemy_health_max = 20
        self.enemy_mana_max = 20

        # Текущие значения
        self.character_health = 20
        self.enemy_health = 20
        self.character_mana = 20
        self.enemy_mana = 20

        # Механика ходов
        self.current_turn = None  # 'player' или 'enemy'
        self.initialize_turn_system()

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
        self.health_color = QColor(255, 50, 50)
        self.mana_color = QColor(50, 150, 255)

        self.character_health_text.setFont(self.text_font)
        self.character_mana_text.setFont(self.text_font)
        self.enemy_health_text.setFont(self.text_font)
        self.enemy_mana_text.setFont(self.text_font)

        self.character_health_text.setDefaultTextColor(self.health_color)
        self.character_mana_text.setDefaultTextColor(self.mana_color)
        self.enemy_health_text.setDefaultTextColor(self.health_color)
        self.enemy_mana_text.setDefaultTextColor(self.mana_color)

        self.spell_icons = []

        self.setup_animations()
        self.create_spell_panel()
        self.fit_background()
        self.update_text_values()

    def initialize_turn_system(self):
        """Инициализация системы ходов"""
        # Случайный выбор первого хода
        self.current_turn = 'player' if random.randint(0, 1) == 0 else 'enemy'
        print(f"First turn: {self.current_turn}")

        # Добавляем ману в начале первого хода
        if self.current_turn == 'player':
            self.character_mana = min(self.character_mana_max, self.character_mana + 2)
        else:
            self.enemy_mana = min(self.enemy_mana_max, self.enemy_mana + 2)

        # Если первый ход противника - запускаем его ход
        if self.current_turn == 'enemy':
            QTimer.singleShot(1000, self.start_enemy_turn)

    def update_bar_image(self, bar_item, current_value, max_value, bar_type, owner):
        """Обновляет изображение бара в зависимости от текущего значения"""
        # Определяем индекс изображения на основе диапазонов
        if current_value <= 0:
            index = 5
        else:
            ratio = current_value / max_value
            if ratio > 0.75:    # > 75% (15-20 при макс=20)
                index = 1
            elif ratio >= 0.55: # 55%-75% (11-15 при макс=20)
                index = 2
            elif ratio >= 0.3:  # 30%-55% (6-10 при макс=20)
                index = 3
            else:               # <30% (1-5 при макс=20)
                index = 4

        # Определяем базовое имя файла
        if owner == "enemy":
            if bar_type == "health":
                base_name = "enemy_hp_bar"
            else:  # mana
                base_name = "mana_bar"
        else:  # character
            base_name = "hp_bar" if bar_type == "health" else "mana_bar"

        image_path = f"assets/gui/{base_name}{index}.png"
        pixmap = QPixmap(image_path)

        # Если изображение не загружено, создаем цветной прямоугольник
        if pixmap.isNull():
            # Цвета для разных уровней
            colors = {
                1: QColor(0, 255, 0),    # зеленый
                2: QColor(150, 255, 0),   # светло-зеленый
                3: QColor(255, 255, 0),   # желтый
                4: QColor(255, 150, 0),   # оранжевый
                5: QColor(255, 0, 0)      # красный
            }
            color = colors.get(index, QColor(255, 255, 255))

            # Создаем pixmap нужного размера
            if bar_type == "health":
                size = QSize(self.health_bar_width, self.health_bar_height)
            else:
                size = QSize(self.mana_bar_width, self.mana_bar_height)

            pixmap = QPixmap(size)
            pixmap.fill(color)

        # Масштабируем изображение
        if bar_type == "health":
            target_size = QSize(self.health_bar_width, self.health_bar_height)
        else:
            target_size = QSize(self.mana_bar_width, self.mana_bar_height)

        pixmap = pixmap.scaled(target_size, Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
        bar_item.setPixmap(pixmap)

    def update_text_values(self):
        """Обновление текстовых значений здоровья и маны"""
        self.character_health_text.setPlainText(f"{self.character_health}")
        self.character_mana_text.setPlainText(f"{self.character_mana}")
        self.enemy_health_text.setPlainText(f"{self.enemy_health}")
        self.enemy_mana_text.setPlainText(f"{self.enemy_mana}")

        # Обновляем изображения баров
        self.update_bar_image(self.character_health_bar, self.character_health, self.character_health_max, "health", "character")
        self.update_bar_image(self.enemy_health_bar, self.enemy_health, self.enemy_health_max, "health", "enemy")
        self.update_bar_image(self.character_mana_bar, self.character_mana, self.character_mana_max, "mana", "character")
        self.update_bar_image(self.enemy_mana_bar, self.enemy_mana, self.enemy_mana_max, "mana", "enemy")

        # Обновляем позиции текста
        self.update_health_bars_positions()
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
        self.enemy_damage_movie = QMovie("assets/animations/enemy_hurt.gif")
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
        if self.is_attacking or self.current_turn != 'player':
            return
        self.idle_movie.stop()
        self.attack_movie.start()
        self.attack_movie.jumpToFrame(0)
        self.is_attacking = True

    def play_spell_animation(self):
        if self.is_casting or self.current_turn != 'player':
            return

        # Проверка и уменьшение маны персонажа
        if self.character_mana < 5:  # Требуется 5 маны для заклинания
            print("Not enough mana!")
            return

        self.character_mana -= 5  # Уменьшаем ману
        self.update_text_values()  # Обновляем отображение

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

        # Уменьшаем здоровье врага
        self.enemy_health = max(0, self.enemy_health - 1)
        self.update_text_values()

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

        # После получения урона врагом заканчивается наш ход
        self.end_player_turn()

    def play_character_damage_animation(self):
        if self.is_character_taking_damage:
            return

        # Уменьшаем здоровье персонажа
        self.character_health = max(0, self.character_health - 1)
        self.update_text_values()

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

        # После получения урона игроком заканчивается ход врага
        self.end_enemy_turn()

    def play_enemy_attack_animation(self):
        if self.is_enemy_attacking or self.current_turn != 'enemy':
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
        if self.is_enemy_casting or self.current_turn != 'enemy':
            return

        # Проверка и уменьшение маны противника
        if self.enemy_mana < 5:  # Требуется 5 маны для заклинания
            print("Enemy not enough mana!")
            return

        self.enemy_mana -= 5  # Уменьшаем ману
        self.update_text_values()  # Обновляем отображение

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

                # Добавляем обработчик клика
                icon.mousePressEvent = lambda event, idx=i: self.handle_spell_click(idx)
                self.scene().addItem(icon)
                self.spell_icons.append(icon)
            except:
                print(f"Failed to load spell icon {i+1}")

    def handle_spell_click(self, spell_index):
        if self.current_turn != 'player':
            return

        print(f"Spell {spell_index+1} clicked!")
        # Блокируем иконки сразу при касте
        self.set_spell_icons_active(False)
        # Запускаем анимацию атаки, которая затем перейдет в заклинание
        self.play_attack_animation()

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
        elif event.key() in [Qt.Key_1, Qt.Key_2, Qt.Key_3, Qt.Key_4, Qt.Key_5]:
            if self.current_turn != 'player':
                return

            # Преобразуем клавишу в индекс заклинания
            spell_index = event.key() - Qt.Key_1
            print(f"Casting spell {spell_index+1} with key")

            # Блокируем иконки сразу
            self.set_spell_icons_active(False)
            self.play_attack_animation()
        else:
            super().keyPressEvent(event)

    def toggle_fullscreen(self):
        if self.fullscreen:
            self.setCursor(Qt.ArrowCursor)
        else:
            self.setCursor(Qt.BlankCursor)
        self.fullscreen = not self.fullscreen

    # ========== ЛОГИКА ХОДОВ ==========
    def end_player_turn(self):
        """Завершение хода игрока и начало хода противника"""
        self.current_turn = 'enemy'
        print("Player turn ended. Enemy turn started.")

        # Добавляем ману противнику в начале его хода
        self.enemy_mana = min(self.enemy_mana_max, self.enemy_mana + 2)
        self.update_text_values()

        # Запускаем ход противника с задержкой
        QTimer.singleShot(1000, self.start_enemy_turn)

    def start_enemy_turn(self):
        """Начало хода противника"""
        if self.current_turn != 'enemy':
            return

        print("Enemy casting spell...")
        self.play_enemy_attack_animation()

    def end_enemy_turn(self):
        """Завершение хода противника и начало хода игрока"""
        self.current_turn = 'player'
        print("Enemy turn ended. Player turn started.")

        # Добавляем ману игроку в начале его хода
        self.character_mana = min(self.character_mana_max, self.character_mana + 2)
        self.update_text_values()

        # Разблокируем кнопки спеллов
        self.set_spell_icons_active(True)

    def set_spell_icons_active(self, active):
        """Активация/деактивация кнопок спеллов"""
        for icon in self.spell_icons:
            icon.setEnabled(active)
            icon.setOpacity(1.0 if active else 0.5)


class SpellIconItem(QGraphicsPixmapItem):
    def __init__(self, pixmap, spell_id, parent=None):
        super().__init__(pixmap, parent)
        self.spell_id = spell_id
        self.normal_opacity = 1.0
        self.pressed_opacity = 0.7
        self.hover_opacity = 0.9
        self.setOpacity(self.normal_opacity)

    def mousePressEvent(self, event):
        if not self.isEnabled():
            return
        self.setOpacity(self.pressed_opacity)
        print(f"Spell {self.spell_id} pressed!")
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if not self.isEnabled():
            return
        self.setOpacity(self.normal_opacity)
        print(f"Spell {self.spell_id} activated!")
        super().mouseReleaseEvent(event)

    def hoverEnterEvent(self, event):
        if not self.isEnabled():
            return
        self.setOpacity(self.hover_opacity)
        self.setCursor(Qt.PointingHandCursor)
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        if not self.isEnabled():
            return
        self.setOpacity(self.normal_opacity)
        self.setCursor(Qt.ArrowCursor)
        super().hoverLeaveEvent(event)
