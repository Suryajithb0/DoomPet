
import sys
import math
import random

from PySide6.QtCore import Qt, QTimer, QPointF
from PySide6.QtGui import QColor, QPainter, QPen, QPolygonF
from PySide6.QtWidgets import QApplication, QWidget, QMenu


class DoomPet(QWidget):
    def __init__(self):
        super().__init__()

        self.W = 112
        self.H = 128

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(
            Qt.WidgetAttribute.WA_TranslucentBackground
        )
        self.resize(self.W, self.H)

        # Behavior
        self.state = "walk"
        self.direction = 1
        self.speed = 2.0
        self.paused = False
        self.frame = 0
        self.idle_ticks = 0

        # Movement targets
        self.target_x = 100
        self.target_y = 100
        self.move_speed = 2.0

        # Attack animation
        self.attack_ticks = 0
        self.particles = []

        # Dragging
        self.dragging = False
        self.press_pos = None
        self.drag_offset = QPointF()
        self.did_drag = False

        # Screen boundaries
        screen = QApplication.primaryScreen().availableGeometry()
        self.screen_rect = screen

        start_x = screen.left() + 100
        start_y = screen.top() + screen.height() - self.H - 20

        self.move(start_x, start_y)
        self.choose_destination()

        # Update at roughly 33 frames per second
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_pet)
        self.timer.start(30)

    def choose_destination(self):
        screen = QApplication.primaryScreen().availableGeometry()

        self.target_x = random.randint(
            screen.left(),
            max(screen.left(), screen.right() - self.W + 1)
        )
        self.target_y = random.randint(
            screen.top(),
            max(screen.top(), screen.bottom() - self.H + 1)
        )

    def update_pet(self):
        self.frame += 1

        if self.state == "attack":
            self.attack_ticks -= 1
            self.update_particles()

            if self.attack_ticks <= 0:
                self.state = "walk"
                self.idle_ticks = random.randint(40, 100)
                self.choose_destination()

        elif not self.paused and not self.dragging:
            if self.idle_ticks > 0:
                self.idle_ticks -= 1

                if self.idle_ticks == 0:
                    self.state = "walk"
                    self.choose_destination()

            elif self.state == "walk":
                dx = self.target_x - self.x()
                dy = self.target_y - self.y()
                distance = math.hypot(dx, dy)

                if distance <= self.move_speed:
                    self.move(
                        int(self.target_x),
                        int(self.target_y)
                    )

                    self.state = random.choice(["idle", "sit"])
                    self.idle_ticks = random.randint(60, 180)

                elif distance > 0:
                    step_x = dx / distance * self.move_speed
                    step_y = dy / distance * self.move_speed

                    new_x = round(self.x() + step_x)
                    new_y = round(self.y() + step_y)

                    self.move(new_x, new_y)

                    if abs(dx) > 1:
                        self.direction = 1 if dx > 0 else -1

        self.update()

    def start_attack(self):
        if self.state == "attack":
            return

        self.state = "attack"
        self.attack_ticks = 42
        self.idle_ticks = 0
        self.particles.clear()

        # Green magical fire bursts from Doom's hand.
        for _ in range(75):
            angle = random.uniform(-1.2, 1.2)
            velocity = random.uniform(1.2, 4.5)

            self.particles.append({
                "x": 79,
                "y": 54,
                "vx": math.cos(angle) * velocity * self.direction,
                "vy": math.sin(angle) * velocity - 1.2,
                "life": random.randint(15, 36),
                "size": random.uniform(3, 8),
            })

        self.update()

    def update_particles(self):
        for particle in self.particles:
            particle["x"] += particle["vx"]
            particle["y"] += particle["vy"]
            particle["vy"] -= 0.025
            particle["life"] -= 1
            particle["size"] *= 0.97

        self.particles = [
            particle for particle in self.particles
            if particle["life"] > 0
        ]

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(
            QPainter.RenderHint.Antialiasing
        )

        painter.save()

        # Face the direction Doom is travelling.
        if self.direction < 0:
            painter.translate(self.W, 0)
            painter.scale(-1, 1)

        self.draw_character(painter)
        painter.restore()

        self.draw_flames(painter)
        painter.end()

    def draw_character(self, p):
        p.setPen(Qt.PenStyle.NoPen)

        # Ground shadow
        p.setBrush(QColor(0, 0, 0, 65))
        p.drawEllipse(19, 110, 75, 10)

        # Green hood and cloak
        p.setBrush(QColor("#163b26"))
        p.drawPolygon(QPolygonF([
            QPointF(34, 27),
            QPointF(64, 27),
            QPointF(78, 77),
            QPointF(70, 105),
            QPointF(25, 105),
            QPointF(19, 76),
        ]))

        p.setBrush(QColor("#245b35"))
        p.drawPolygon(QPolygonF([
            QPointF(30, 30),
            QPointF(44, 38),
            QPointF(39, 91),
            QPointF(28, 101),
            QPointF(21, 74),
        ]))

        # Legs
        p.setBrush(QColor("#777f81"))

        if self.state == "sit":
            p.drawRoundedRect(30, 87, 25, 15, 4, 4)
            p.drawRoundedRect(51, 91, 25, 12, 4, 4)

        elif self.state == "attack":
            p.drawRoundedRect(34, 84, 14, 23, 3, 3)
            p.drawRoundedRect(54, 84, 14, 23, 3, 3)

        else:
            step = math.sin(self.frame * 0.18) * 5
            p.drawRoundedRect(
                33, 82 + int(step), 15, 26, 3, 3
            )
            p.drawRoundedRect(
                55, 82 - int(step), 15, 26, 3, 3
            )

        # Metal boots
        p.setBrush(QColor("#b0b8b8"))
        p.drawRoundedRect(29, 103, 22, 8, 2, 2)
        p.drawRoundedRect(53, 103, 22, 8, 2, 2)

        # Torso armor
        p.setBrush(QColor("#899294"))
        p.drawRoundedRect(30, 47, 42, 42, 7, 7)

        p.setBrush(QColor("#aeb7b7"))
        p.drawPolygon(QPolygonF([
            QPointF(34, 50),
            QPointF(48, 55),
            QPointF(45, 80),
            QPointF(34, 84),
        ]))

        # Belt
        p.setBrush(QColor("#323b3b"))
        p.drawRect(31, 79, 40, 6)

        p.setBrush(QColor("#b5a35e"))
        p.drawRect(47, 78, 9, 8)

        # Arms
        p.setBrush(QColor("#747f81"))
        p.drawRoundedRect(21, 49, 14, 29, 5, 5)

        if self.state == "attack":
            p.save()
            p.translate(67, 59)
            p.rotate(-38)
            p.drawRoundedRect(-5, -24, 14, 29, 5, 5)
            p.restore()
        else:
            p.drawRoundedRect(67, 49, 14, 29, 5, 5)

        # Hood
        p.setBrush(QColor("#173f28"))
        p.drawPolygon(QPolygonF([
            QPointF(29, 33),
            QPointF(34, 15),
            QPointF(49, 8),
            QPointF(66, 17),
            QPointF(72, 37),
            QPointF(63, 49),
            QPointF(35, 47),
        ]))

        # Silver mask
        p.setBrush(QColor("#aeb8b9"))
        p.drawRoundedRect(34, 23, 31, 27, 5, 5)

        p.setBrush(QColor("#d4dada"))
        p.drawPolygon(QPolygonF([
            QPointF(35, 27),
            QPointF(49, 24),
            QPointF(47, 43),
            QPointF(37, 45),
        ]))

        # Eyes
        p.setBrush(QColor("#263b30"))
        p.drawEllipse(38, 32, 7, 4)
        p.drawEllipse(53, 32, 7, 4)

        p.setBrush(QColor("#9cff70"))
        p.drawEllipse(40, 33, 3, 2)
        p.drawEllipse(55, 33, 3, 2)

        # Mouth grille
        p.setPen(QPen(QColor("#566264"), 2))
        for y in range(39, 45, 3):
            p.drawLine(42, y, 58, y)

        p.setPen(Qt.PenStyle.NoPen)

        # Hood outline
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.setPen(QPen(QColor("#39764a"), 2))
        p.drawRoundedRect(29, 18, 42, 34, 10, 10)
        p.setPen(Qt.PenStyle.NoPen)

    def draw_flames(self, p):
        p.save()
        p.setPen(Qt.PenStyle.NoPen)

        for particle in self.particles:
            alpha = max(
                0,
                min(255, int(255 * particle["life"] / 36))
            )
            size = max(1, particle["size"])

            # Outer green glow
            p.setBrush(QColor(20, 255, 65, alpha // 4))
            p.drawEllipse(
                QPointF(particle["x"], particle["y"]),
                size * 1.9,
                size * 1.9
            )

            # Green flame
            p.setBrush(QColor(35, 230, 70, alpha))
            p.drawEllipse(
                QPointF(particle["x"], particle["y"]),
                size,
                size * 1.4
            )

            # Bright core
            p.setBrush(QColor(190, 255, 130, alpha))
            p.drawEllipse(
                QPointF(particle["x"], particle["y"]),
                size * 0.38,
                size * 0.6
            )

        p.restore()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.RightButton:
            menu = QMenu(self)

            pause_action = menu.addAction(
                "Resume movement"
                if self.paused else "Pause movement"
            )
            quit_action = menu.addAction("Quit DOOM.exe")

            chosen = menu.exec(
                event.globalPosition().toPoint()
            )

            if chosen == pause_action:
                self.paused = not self.paused

            elif chosen == quit_action:
                QApplication.quit()

            return

        if event.button() == Qt.MouseButton.LeftButton:
            self.press_pos = event.globalPosition().toPoint()
            self.drag_offset = QPointF(event.position())
            self.did_drag = False
            self.dragging = True

    def mouseMoveEvent(self, event):
        if self.dragging:
            current = event.globalPosition().toPoint()

            if (
                current - self.press_pos
            ).manhattanLength() > 5:
                self.did_drag = True

            if self.did_drag:
                self.move(
                    current - self.drag_offset.toPoint()
                )

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            was_dragging = self.did_drag
            self.dragging = False

            if not was_dragging:
                self.start_attack()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setApplicationName("DOOM.exe")

    doom = DoomPet()
    doom.show()

    sys.exit(app.exec())
