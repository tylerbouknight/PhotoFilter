from PyQt5.QtWidgets import QApplication
from photo_filter import *

if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    stylesheet = load_stylesheet('style.qss')
    app.setStyleSheet(stylesheet)

    # Use config_path to get the directory
    directory = config_path()

    ex = PhotoFilter(directory)
    sys.exit(app.exec_())

