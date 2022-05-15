from tkinter import filedialog as fd
import os

dir_name = fd.askdirectory(title="Select folder", mustexist=False)
if not os.path.isdir(dir_name):
    os.makedirs(dir_name)

print(dir_name)