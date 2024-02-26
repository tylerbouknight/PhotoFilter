import os
import shutil
from tkinter import *
from PIL import Image, ImageTk

class PhotoFilter:
    def __init__(self, master, directory):
        self.master = master
        self.directory = directory

        # Set a fixed window size
        self.master.geometry('800x600')

        # Filter out directories
        self.photos = [f for f in os.listdir(self.directory) if os.path.isfile(os.path.join(self.directory, f))]
        self.photos = iter(self.photos)

        self.photo = None
        self.label = Label(self.master)
        self.label.pack()
        self.master.bind('<Left>', self.move_to_trash)
        self.master.bind('<Right>', self.keep)
        self.master.bind('<Up>', self.skip)
        self.next_photo()

        # Create folders if they don't exist
        os.makedirs(os.path.join(self.directory, 'trash'), exist_ok=True)
        os.makedirs(os.path.join(self.directory, 'keep'), exist_ok=True)

    def next_photo(self):
        try:
            self.photo = next(self.photos)
            image = Image.open(os.path.join(self.directory, self.photo))

            # Resize image to fit the window
            max_size = (800, 600)  # Adjust to your desired window size
            image.thumbnail(max_size, Image.LANCZOS)

            photo = ImageTk.PhotoImage(image)
            self.label.config(image=photo)
            self.label.image = photo
        except StopIteration:
            self.master.quit()

    def move_to_trash(self, event):
        shutil.move(os.path.join(self.directory, self.photo), os.path.join(self.directory, 'trash', self.photo))
        self.next_photo()

    def keep(self, event):
        shutil.move(os.path.join(self.directory, self.photo), os.path.join(self.directory, 'keep', self.photo))
        self.next_photo()

    def skip(self, event):
        self.next_photo()

root = Tk()
app = PhotoFilter(root, 'C:/Users/Tyler/Pictures/Found - Copy')
root.mainloop()
