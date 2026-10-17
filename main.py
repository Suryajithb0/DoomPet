
import os
import sys
import math
import random

from PySide6.QtCore import Qt, QTimer, QPointF
from PySide6.QtGui import QPixmap, QPainter
from PySide6.QtWidgets import QApplication, QWidget, QMenu, QMessageBox

# ---------------------------------------------------------------------------
# Resolve paths relative to main.py, not the current working directory.
# ---------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ---------------------------------------------------------------------------
# Configurable sprite size — change these two values to resize the pet.
# Sprites are scaled proportionally to fit within this bounding box.
# ---------------------------------------------------------------------------
SPRITE_WIDTH = 128
SPRITE_HEIGHT = 128


def load_frames(subfolder, count):
    """Load *count* numbered PNGs (1.png … N.png) from pet/<subfolder>.

    Returns a list of QPixmap scaled smoothly to SPRITE_WIDTH × SPRITE_HEIGHT
    while preserving aspect ratio and transparency.
    Raises SystemExit with a descriptive error if any frame is missing or
    cannot be decoded.
    """
    folder = os.path.join(BASE_DIR, "pet", subfolder)
    frames = []

    for i in range(1, count + 1):
        path = os.path.join(folder, f"{i}.png")

        if not os.path.isfile(path):
            QMessageBox.critical(
                None,
                "DOOM.exe — Missing Sprite",
                f"Required sprite not found:\n{path}\n\n"
                f"Expected {count} frames in pet/{subfolder}/",
            )
            sys.exit(1)

        pixmap = QPixmap(path)

        if pixmap.isNull():
            QMessageBox.critical(
                None,
                "DOOM.exe — Invalid Sprite",
                f"Could not load sprite image:\n{path}\n\n"
                "The file may be corrupted or in an unsupported format.",
            )
            sys.exit(1)

        # Scale proportionally with smooth filtering, keeping transparency.
        scaled = pixmap.scaled(
            SPRITE_WIDTH,
            SPRITE_HEIGHT,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        frames.append(scaled)

    return frames


class DoomPet(QWidget):
    """Sprite-based desktop pet with walk, sit, and attack animations."""

    # --- animation timing (milliseconds per frame) --------------------------
    WALK_FRAME_MS = 60        # walk cycle speed
    SIT_FRAME_MS = 150        # sitting/resting loop speed
    ATTACK_FRAME_MS = 60      # attack animation speed
    MOVE_TICK_MS = 30          # movement update interval (~33 fps)

    def __init__(self):
        super().__init__()

        # --- sprite loading --------------------------------------------------
        self.walk_frames = load_frames("walk", 8)
        self.sit_frames = load_frames("sit", 4)
        self.attack_frames = load_frames("attack", 8)

        # Window size accommodates the largest sprite.
        self.W = SPRITE_WIDTH
        self.H = SPRITE_HEIGHT

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(self.W, self.H)

        # --- state machine ---------------------------------------------------
        self.state = "walking"          # "walking" | "sitting" | "attacking"
        self.pre_attack_state = None    # state to return to after attack
        self.direction = 1              # 1 = facing right, -1 = facing left
        self.paused = False

        # --- animation frame indices -----------------------------------------
        self.anim_index = 0             # current frame within active sequence

        # --- movement (horizontal only, along the bottom) --------------------
        self.move_speed = 0.8
        self.target_x = 0
        self.bottom_y = 0               # fixed Y position at screen bottom

        # --- dragging --------------------------------------------------------
        self.dragging = False
        self.press_pos = None
        self.drag_offset = QPointF()
        self.did_drag = False

        # --- screen bounds ---------------------------------------------------
        screen = QApplication.primaryScreen().availableGeometry()
        self.screen_rect = screen

        # Pin to bottom of the screen.
        self.bottom_y = screen.bottom() - self.H
        start_x = screen.left() + 100
        self.move(start_x, self.bottom_y)
        self._choose_destination()

        # --- timers ----------------------------------------------------------
        # Movement timer — always runs at a fixed tick rate for smooth motion.
        self.move_timer = QTimer(self)
        self.move_timer.timeout.connect(self._tick_movement)
        self.move_timer.start(self.MOVE_TICK_MS)

        # Animation timer — rate changes depending on state.
        self.anim_timer = QTimer(self)
        self.anim_timer.timeout.connect(self._tick_animation)
        self._start_walk_anim()

    # ======================================================================
    #  Destination / movement helpers
    # ======================================================================

    def _choose_destination(self):
        """Pick a random horizontal position along the bottom of the screen."""
        s = QApplication.primaryScreen().availableGeometry()
        self.target_x = random.randint(s.left(), max(s.left(), s.right() - self.W))

    def _clamp_to_screen(self):
        """Ensure the pet window stays within the visible desktop."""
        s = QApplication.primaryScreen().availableGeometry()
        x = max(s.left(), min(self.x(), s.right() - self.W))
        y = max(s.top(), min(self.y(), s.bottom() - self.H))
        if x != self.x() or y != self.y():
            self.move(x, y)

    # ======================================================================
    #  State transitions
    # ======================================================================

    def _start_walk_anim(self):
        """Enter the *walking* state and start the walk animation timer."""
        self.state = "walking"
        self.anim_index = 0
        self.anim_timer.start(self.WALK_FRAME_MS)

    def _start_sit_anim(self):
        """Enter the *sitting* (resting) state and start the sit animation."""
        self.state = "sitting"
        self.anim_index = 0
        self.anim_timer.start(self.SIT_FRAME_MS)

    def _start_attack_anim(self):
        """Enter the *attacking* state and play the attack sequence once."""
        self.state = "attacking"
        self.anim_index = 0
        self.anim_timer.start(self.ATTACK_FRAME_MS)

    # ======================================================================
    #  Timer callbacks
    # ======================================================================

    def _tick_movement(self):
        """Called every MOVE_TICK_MS to update the pet's position."""
        if self.paused or self.dragging:
            self.update()
            return

        if self.state == "walking":
            dx = self.target_x - self.x()
            distance = abs(dx)

            if distance <= self.move_speed:
                # Arrived — snap to target and start sitting.
                self.move(int(self.target_x), self.bottom_y)
                self._start_sit_anim()
            else:
                step_x = self.move_speed if dx > 0 else -self.move_speed
                new_x = round(self.x() + step_x)
                self.move(new_x, self.bottom_y)

                self.direction = 1 if dx > 0 else -1

        self.update()

    def _end_sit_hold(self):
        """Called after the 4-second hold on the last sit frame; walk again."""
        if self.state == "sitting":
            self._choose_destination()
            self._start_walk_anim()

    def _tick_animation(self):
        """Advance the animation frame for the current state."""
        if self.state == "walking":
            self.anim_index = (self.anim_index + 1) % len(self.walk_frames)

        elif self.state == "sitting":
            self.anim_index += 1
            if self.anim_index >= len(self.sit_frames):
                # Reached the last frame — stop animating and hold for 4s.
                self.anim_index = len(self.sit_frames) - 1
                self.anim_timer.stop()
                QTimer.singleShot(4000, self._end_sit_hold)
                return

        elif self.state == "attacking":
            self.anim_index += 1
            if self.anim_index >= len(self.attack_frames):
                # Attack finished — return to previous behaviour.
                self._finish_attack()
                return

        self.update()

    def _finish_attack(self):
        """Return to the appropriate state after the attack sequence ends."""
        if self.pre_attack_state == "walking":
            self._start_walk_anim()
        else:
            self._start_sit_anim()
        self.pre_attack_state = None

    # ======================================================================
    #  Attack
    # ======================================================================

    def start_attack(self):
        """Trigger the attack animation (plays once, ignores rapid clicks)."""
        if self.state == "attacking":
            return  # don't restart if already attacking

        self.pre_attack_state = self.state
        self._start_attack_anim()



    # ======================================================================
    #  Painting
    # ======================================================================

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

        # Select the current frame.
        if self.state == "walking":
            frames = self.walk_frames
        elif self.state == "sitting":
            frames = self.sit_frames
        else:  # attacking
            frames = self.attack_frames

        idx = min(self.anim_index, len(frames) - 1)
        pixmap = frames[idx]

        # Centre the (possibly smaller-than-window) pixmap.
        px = (self.W - pixmap.width()) // 2
        py = (self.H - pixmap.height()) // 2

        painter.save()

        # Flip horizontally when facing left.
        if self.direction < 0:
            painter.translate(self.W, 0)
            painter.scale(-1, 1)

        painter.drawPixmap(px, py, pixmap)
        painter.restore()

        painter.end()


    # ======================================================================
    #  Mouse interaction
    # ======================================================================

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.RightButton:
            menu = QMenu(self)

            pause_action = menu.addAction(
                "Resume movement" if self.paused else "Pause movement"
            )
            quit_action = menu.addAction("Quit DOOM.exe")

            chosen = menu.exec(event.globalPosition().toPoint())

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

            if (current - self.press_pos).manhattanLength() > 5:
                self.did_drag = True

            if self.did_drag:
                self.move(current - self.drag_offset.toPoint())

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            was_dragging = self.did_drag
            self.dragging = False

            if was_dragging:
                # After a drag, clamp to screen and keep current state.
                self._clamp_to_screen()
            else:
                self.start_attack()


# ===========================================================================
#  Entry point
# ===========================================================================

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setApplicationName("DOOM.exe")


    doom = DoomPet()
    doom.show()

    sys.exit(app.exec())
