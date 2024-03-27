# Standard library imports
import os
import shutil
import sys
import configparser

# Third-party library imports
from PyQt5.QtWidgets import (QApplication, QAction, QFileDialog, QLabel, QMainWindow, 
                             QMenu, QVBoxLayout, QWidget)
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import Qt, QPoint, QEvent, QPropertyAnimation, QEasingCurve

# Configuration functions
def config_path(filename='config.ini', section='DEFAULT', option='directory', default='C:\\'):
    config = configparser.ConfigParser()
    config.read(filename)
    if config.has_option(section, option):
        return config.get(section, option)
    else:
        with open(filename, 'w') as configfile:
            config.set(section, option, default)
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

# Main application class
class PhotoFilter(QMainWindow):
    def __init__(self, directory):
        super().__init__()
        self.initialize_ui(directory)
        self.create_actions()
        self.setup_animation()
        self.load_photos()
        self.display_photo()

    def initialize_ui(self, directory):
        self.setWindowTitle('Photo Filter')
        self.directory = directory
        self.action_stack = []
        self.current_photo_index = 0
        self.setFixedSize(800, 600)
        self.setup_layout()
        self.show()

    def setup_layout(self):
        self.label = QLabel(self)
        layout = QVBoxLayout()
        layout.addWidget(self.label)
        widget = QWidget()
        widget.setLayout(layout)
        self.setCentralWidget(widget)

    def create_actions(self):
        self.menu = self.menuBar()
        self.edit_menu = QMenu('Edit', self)
        self.setup_edit_menu_actions()
        self.menu.addMenu(self.edit_menu)

    def setup_edit_menu_actions(self):
        self.undo_action = QAction('Undo', self)
        self.undo_action.setShortcut('Ctrl+Z')
        self.undo_action.triggered.connect(self.undo)
        self.edit_menu.addAction(self.undo_action)

        self.change_dir_action = QAction('Change Directory', self)
        self.change_dir_action.triggered.connect(self.change_directory)
        self.edit_menu.addAction(self.change_dir_action)

    def setup_animation(self):
        self.animation = QPropertyAnimation(self.label, b"pos")
        self.animation.finished.connect(self.next_photo)
        self.animation.setEasingCurve(QEasingCurve.OutCubic)
        self.installEventFilter(self)

    def load_photos(self):
        self.photos = [f for f in os.listdir(self.directory) if os.path.isfile(os.path.join(self.directory, f))]
        os.makedirs(os.path.join(self.directory, 'trash'), exist_ok=True)
        os.makedirs(os.path.join(self.directory, 'keep'), exist_ok=True)
        if self.photos:
            self.photo = self.photos[0]
        else:
            self.photo = None

    def change_directory(self):
        directory = QFileDialog.getExistingDirectory(self, 'Select a folder:', self.directory, QFileDialog.ShowDirsOnly)
        if directory:
            self.directory = directory
            write_config_path(self.directory)
            self.load_photos()
            self.current_photo_index = 0
            self.next_photo()

    def animate_move(self, x, y):
        self.animation.setDuration(350)
        self.animation.setStartValue(self.label.pos())
        self.animation.setEndValue(self.label.pos() + QPoint(x, y))
        self.animation.start()

    def eventFilter(self, obj, event):
        if obj == self and event.type() == QEvent.KeyPress and self.animation.state() == QPropertyAnimation.Running:
            return True 
        return super().eventFilter(obj, event)

    def next_photo(self):
        if self.current_photo_index < len(self.photos) - 1:
            self.current_photo_index += 1
            self.photo = self.photos[self.current_photo_index]
            self.display_photo()
        else:
            self.photo = None  # No more photos to display
            self.display_photo()  # Call this to clear the display or show a default message


    def display_photo(self):
        if self.photo:  # Check if self.photo is not None
            image_path = os.path.join(self.directory, self.photo)
            image = QImage(image_path)
            pixmap = QPixmap.fromImage(image)
            self.label.setPixmap(pixmap.scaled(self.size(), Qt.KeepAspectRatio))
            self.label.setAlignment(Qt.AlignCenter)
        else:
            self.label.setText("No photos to display")  # Show a default message
            self.label.setAlignment(Qt.AlignCenter)  # Center the message


    def undo(self):
        if self.action_stack:
            last_action, last_photo = self.action_stack.pop()
            shutil.move(os.path.join(self.directory, last_action, last_photo), os.path.join(self.directory, last_photo))
            self.current_photo_index = max(self.current_photo_index - 1, 0)
            self.photo = last_photo
            self.display_photo()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Left:
            self.move_to_trash()
        elif event.key() == Qt.Key_Right:
            self.keep()
        elif event.key() == Qt.Key_Up:
            self.skip()

    def move_to_trash(self):
        if self.current_photo_index > 0:  # Prevents moving non-existent photo
            self.animate_move(-800, 0)
            shutil.move(os.path.join(self.directory, self.photo), os.path.join(self.directory, 'trash', self.photo))
            self.action_stack.append(('trash', self.photo))
            self.next_photo()

    def keep(self):
        if self.current_photo_index > 0:  # Prevents moving non-existent photo
            self.animate_move(800, 0)
            shutil.move(os.path.join(self.directory, self.photo), os.path.join(self.directory, 'keep', self.photo))
            self.action_stack.append(('keep', self.photo))
            self.next_photo()

    def skip(self):
        if self.current_photo_index > 0:  # Prevents skipping non-existent photo
            self.animate_move(0, -600)
            self.next_photo()

# Entry point of the application
if __name__ == "__main__":
    app = QApplication(sys.argv)
    stylesheet = load_stylesheet('style.qss')
    app.setStyleSheet(stylesheet)
    directory = config_path()
    ex = PhotoFilter(directory)
    sys.exit(app.exec_())

