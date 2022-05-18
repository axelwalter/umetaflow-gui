import tkinter as tk
from tkinter import filedialog as fd

# def get_dir(title=""):
#     return easygui.diropenbox(title=title)

# def get_files(type="", multiple=False):
#     title = f"Open {type} file"
#     if multiple:
#         title += "s"
#     files = easygui.fileopenbox(title=title, multiple=multiple)
#     if not files:
#         return []
#     return [file for file in files if file.endswith(type)]

def get_file(title="", type=()):
    root = tk.Tk()
    root.wm_attributes("-topmost", True)
    root.withdraw()
    return fd.askopenfilename(parent=root, title=title, filetypes=[type])

def get_files(title="", type=()):
    root = tk.Tk()
    root.wm_attributes("-topmost", True)
    root.withdraw()
    return fd.askopenfilenames(parent=root, title=title, filetypes=[type])

def get_dir(title=""):
    root = tk.Tk()
    root.wm_attributes("-topmost", True)
    root.withdraw()
    return fd.askdirectory(parent=root, title=title, mustexist=True)