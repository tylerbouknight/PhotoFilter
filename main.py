import os
import shutil
from tkinter import *
from PIL import Image, ImageTk

class PhotoFilter:
    def __init__(self, master, directory):
        self.master = master
        self.directory = directory
        self.action_stack = []

        # Set a fixed window size
        self.master.geometry('800x600')

        # Filter out directories
        self.photos = [f for f in os.listdir(self.directory) if os.path.isfile(os.path.join(self.directory, f))]
        self.current_photo_index = 0

        self.photo = None
        self.label = Label(self.master)
        self.label.pack()
        self.master.bind('<Left>', self.move_to_trash)
        self.master.bind('<Right>', self.keep)
        self.master.bind('<Up>', self.skip)

        self.menu = Menu(self.master)
        self.master.config(menu=self.menu)

        # Create 'Edit' menu
        self.edit_menu = Menu(self.menu)
        self.menu.add_cascade(label='Edit', menu=self.edit_menu)
        self.edit_menu.add_command(label='Undo', command=self.undo)

        # Bind Ctrl+Z to undo
        self.master.bind_all('<Control-z>', lambda event: self.undo())

        # Create folders if they don't exist
        os.makedirs(os.path.join(self.directory, 'trash'), exist_ok=True)
        os.makedirs(os.path.join(self.directory, 'keep'), exist_ok=True)

        self.next_photo()

    def next_photo(self):
        try:
            self.photo = self.photos[self.current_photo_index]
            self.current_photo_index += 1
            self.display_photo()
        except IndexError:
            self.master.quit()

    
    def display_photo(self):
        image = Image.open(os.path.join(self.directory, self.photo))

        # Resize image to fit the window
        max_size = (800, 600)  # Adjust to your desired window size
        image.thumbnail(max_size, Image.LANCZOS)

        photo = ImageTk.PhotoImage(image)
        self.label.config(image=photo)
        self.label.image = photo

    def undo(self):
        if self.action_stack:
            last_action, last_photo = self.action_stack.pop()
            shutil.move(os.path.join(self.directory, last_action, last_photo), os.path.join(self.directory, last_photo))
            self.photo = last_photo
            self.current_photo_index -= 1
            self.display_photo()
            
    def move_to_trash(self, event):
        shutil.move(os.path.join(self.directory, self.photo), os.path.join(self.directory, 'trash', self.photo))
        self.action_stack.append(('trash', self.photo))
        self.next_photo()

    def keep(self, event):
        shutil.move(os.path.join(self.directory, self.photo), os.path.join(self.directory, 'keep', self.photo))
        self.action_stack.append(('keep', self.photo))
        self.next_photo()

    def skip(self, event):
        self.next_photo()

root = Tk()
app = PhotoFilter(root, 'C:/Users/Tyler/Pictures/Found - Copy')
root.mainloop()
