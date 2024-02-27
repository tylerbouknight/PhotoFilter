import os
import shutil
from PyQt5.QtWidgets import QMainWindow, QLabel, QVBoxLayout, QWidget, QAction, QMenu
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import Qt, QPropertyAnimation, QEasingCurve, QPoint, QEvent

def load_stylesheet(filename):
    with open(filename, "r") as file:
        return file.read()
class PhotoFilter(QMainWindow):
    def __init__(self, directory):
        super().__init__()
        self.setWindowTitle('Photo Filter')
        self.directory = directory
        self.action_stack = []

        # Filter out directories
        self.photos = [f for f in os.listdir(self.directory) if os.path.isfile(os.path.join(self.directory, f))]
        self.current_photo_index = 0

        self.photo = None
        self.label = QLabel(self)
        layout = QVBoxLayout()
        layout.addWidget(self.label)
        widget = QWidget()
        widget.setLayout(layout)
        self.setCentralWidget(widget)

        self.menu = self.menuBar()
        self.edit_menu = QMenu('Edit', self)
        self.undo_action = QAction('Undo', self)
        self.undo_action.setShortcut('Ctrl+Z')
        self.undo_action.triggered.connect(self.undo)
        self.edit_menu.addAction(self.undo_action)
        self.menu.addMenu(self.edit_menu)
        self.animation = QPropertyAnimation(self.label, b"pos")
        self.animation.finished.connect(self.next_photo)
        self.animation.setEasingCurve(QEasingCurve.OutCubic)
        self.installEventFilter(self)

        # Create folders if they don't exist
        os.makedirs(os.path.join(self.directory, 'trash'), exist_ok=True)
        os.makedirs(os.path.join(self.directory, 'keep'), exist_ok=True)

        self.next_photo()

        # Set a fixed window size
        self.setFixedSize(800, 600)

        self.show()

    def animate_move(self, x, y):
        self.animation.setDuration(500)  # Duration in milliseconds
        self.animation.setStartValue(self.label.pos())
        self.animation.setEndValue(self.label.pos() + QPoint(x, y))
        self.animation.start()

    def eventFilter(self, obj, event):
        if obj == self and event.type() == QEvent.KeyPress and self.animation.state() == QPropertyAnimation.Running:
            return True 
        return super().eventFilter(obj, event)

    def next_photo(self):
        try:
            self.photo = self.photos[self.current_photo_index]
            self.current_photo_index += 1
            self.display_photo()
        except IndexError:
            self.close()

    def display_photo(self):
        image_path = os.path.join(self.directory, self.photo)
        image = QImage(image_path)
        pixmap = QPixmap.fromImage(image)
        self.label.setPixmap(pixmap.scaled(800, 600, Qt.KeepAspectRatio))
        self.label.setAlignment(Qt.AlignCenter)

    def undo(self):
        if self.action_stack:
            last_action, last_photo = self.action_stack.pop()
            shutil.move(os.path.join(self.directory, last_action, last_photo), os.path.join(self.directory, last_photo))
            self.photo = last_photo
            self.current_photo_index -= 1
            self.display_photo()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Left:
            self.move_to_trash()
        elif event.key() == Qt.Key_Right:
            self.keep()
        elif event.key() == Qt.Key_Up:
            self.skip()

    def move_to_trash(self):
        self.animate_move(-800, 0)
        shutil.move(os.path.join(self.directory, self.photo), os.path.join(self.directory, 'trash', self.photo))
        self.action_stack.append(('trash', self.photo))

    def keep(self):
        self.animate_move(800, 0)
        shutil.move(os.path.join(self.directory, self.photo), os.path.join(self.directory, 'keep', self.photo))
        self.action_stack.append(('keep', self.photo))

    def skip(self):
        self.animate_move(0, -600)