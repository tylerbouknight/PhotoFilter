from PyQt5.QtWidgets import QApplication
from photo_filter import PhotoFilter

if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    directory = 'C:/Users/Tyler/Pictures/Found - Copy'
    ex = PhotoFilter(directory)
    sys.exit(app.exec_())
