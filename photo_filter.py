import time
import os
import shutil
import sys
import configparser

from PyQt5.QtWidgets import QApplication, QAction, QFileDialog, QLabel, QMainWindow, QMenu, QVBoxLayout, QWidget
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import Qt, QPoint, QEvent, QPropertyAnimation, QEasingCurve, QUrl
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtMultimediaWidgets import QVideoWidget

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
        self.videoWidget = QVideoWidget(self)  # Video widget
        self.player = QMediaPlayer(self)  # Media player
        self.player.setVideoOutput(self.videoWidget)  # Set video output to the widget
        layout = QVBoxLayout()
        layout.addWidget(self.label)
        layout.addWidget(self.videoWidget)  # Add video widget to layout
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
        self.photos = [f for f in os.listdir(self.directory) if os.path.isfile(os.path.join(self.directory, f)) and (f.endswith('.jpg') or f.endswith('.MP4'))]
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
        self.player.stop()  # Stop video if playing
        if self.current_photo_index < len(self.photos) - 1:
            self.current_photo_index += 1
            self.photo = self.photos[self.current_photo_index]
            self.display_photo()
        else:
            self.photo = None  # No more photos to display
            self.display_photo()  # Call this to clear the display or show a default message

    def display_photo(self):
        if self.photo:  # Check if self.photo is not None
            if self.photo.endswith('.MP4'):  # Check if the file is a video
                self.label.clear()  # Clear the photo label
                self.label.hide()  # Hide the photo label as we will use videoWidget for videos
                video_path = os.path.join(self.directory, self.photo)
                self.player.setMedia(QMediaContent(QUrl.fromLocalFile(video_path)))
                self.player.play()
                self.videoWidget.show()  # Show the video widget
            else:  # It's an image
                self.videoWidget.hide()  # Hide the video widget
                self.label.show()  # Show the photo label
                image_path = os.path.join(self.directory, self.photo)
                image = QImage(image_path)
                if not image.isNull():  # Make sure the image is not null
                    pixmap = QPixmap.fromImage(image)
                    self.label.setPixmap(pixmap.scaled(self.size(), Qt.KeepAspectRatio))
                    self.label.setAlignment(Qt.AlignCenter)
                else:
                    self.label.setText("Invalid image file")  # Display error message for invalid images
        else:
            self.label.setText("No photos or videos to display")  # Show a default message
            self.label.setAlignment(Qt.AlignCenter)  # Center the message
            self.videoWidget.hide()  # Ensure video widget is hidden when there are no media files

    def undo(self):
        if self.action_stack:
            action, last_photo = self.action_stack.pop()
            if action == "trash":
                source = os.path.join(self.directory, 'trash', last_photo)
            else:
                source = os.path.join(self.directory, 'keep', last_photo)
            destination = os.path.join(self.directory, last_photo)
            shutil.move(source, destination)
            self.current_photo_index = max(self.current_photo_index - 1, 0)
            self.photo = last_photo
            self.display_photo()
            # Add the reversed action to the stack for redo functionality (optional)
            self.action_stack.append((os.path.basename(source), last_photo))  # Assuming "basename(source)" represents the original directory ("trash" or "keep")

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Left:
            self.move_to_trash()
        elif event.key() == Qt.Key_Right:
            self.keep()
        elif event.key() == Qt.Key_Up:
            self.skip()

    def move_to_trash(self):
        if self.current_photo_index >= 0:
            if self.photo.endswith('.MP4'):
                self.player.stop()
                self.player.setMedia(QMediaContent())  # Clear the current media
                time.sleep(0.5)  # Give it a moment to release the file
            original_location = os.path.join(self.directory, self.photo)
            destination = os.path.join(self.directory, 'trash', self.photo)
            self.try_move_file(original_location, destination)
            self.action_stack.append(("trash", self.photo))  # Update action stack
            self.next_photo()

    def keep(self):
        if self.current_photo_index >= 0:
            if self.photo.endswith('.MP4'):
                self.player.stop()
                self.player.setMedia(QMediaContent())  # Clear the current media
                time.sleep(0.5)  # Give it a moment to release the file
            original_location = os.path.join(self.directory, self.photo)
            destination = os.path.join(self.directory, 'keep', self.photo)
            self.try_move_file(original_location, destination)
            self.action_stack.append(("keep", self.photo))  # Update action stack
            self.next_photo()

    def try_move_file(self, src, dst, attempts=5, delay=1):
        for attempt in range(attempts):
            try:
                shutil.move(src, dst)
                break  # Exit the loop if the move was successful
            except PermissionError:
                if attempt < attempts - 1:  # Avoid waiting after the last attempt
                    time.sleep(delay)  # Wait before retrying
                else:
                    raise  # Re-raise the exception if all attempts fail


# Entry point of the application
if __name__ == "__main__":
    app = QApplication(sys.argv)
    stylesheet = load_stylesheet('style.qss')
    app.setStyleSheet(stylesheet)
    directory = config_path()
    ex = PhotoFilter(directory)
    sys.exit(app.exec_())
