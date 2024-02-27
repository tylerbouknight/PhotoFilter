import os
import shutil
import configparser
from PyQt5.QtWidgets import QMainWindow, QLabel, QVBoxLayout, QWidget, QAction, QMenu, QGraphicsOpacityEffect, QFileDialog
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import Qt, QPropertyAnimation, QEasingCurve, QPoint, QEvent

def config_path(filename='config.ini', section='DEFAULT', option='directory', default='C:\\'):
    config = configparser.ConfigParser()
    config.read(filename)
    if config.has_option(section, option):
        return config.get(section, option)
    else:
        config.set(section, option, default)
        with open(filename, 'w') as configfile:
            config.write(configfile)
        return default

def write_config_path(new_directory, filename='config.ini', section='DEFAULT', option='directory'):
    config = configparser.ConfigParser()
    config.read(filename)
    config.set(section, option, new_directory)
    with open(filename, 'w') as configfile:
        config.write(configfile)

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
        self.change_dir_action = QAction('Change Directory', self)
        self.change_dir_action.triggered.connect(self.change_directory)
        self.edit_menu.addAction(self.change_dir_action)
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

    def change_directory(self):
        self.directory = QFileDialog.getExistingDirectory(None, 'Select a folder:', 'C:\\', QFileDialog.ShowDirsOnly)
        write_config_path(self.directory)  # Store the new directory path
        self.photos = [f for f in os.listdir(self.directory) if os.path.isfile(os.path.join(self.directory, f))]
        self.current_photo_index = 0
        self.next_photo()
        
    def animate_move(self, x, y):
        self.animation.setDuration(350)  # Duration in milliseconds
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

        # Create an opacity effect and set it to the label
        self.opacity_effect = QGraphicsOpacityEffect(self.label)
        self.label.setGraphicsEffect(self.opacity_effect)

        # Create an animation for the opacity
        self.opacity_anim = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.opacity_anim.setDuration(100)  # Duration in milliseconds
        self.opacity_anim.setStartValue(0)
        self.opacity_anim.setEndValue(1)
        self.opacity_anim.start()

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