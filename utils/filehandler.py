import tkinter as tk
from tkinter import filedialog as fd

def save_file(title="", type=[("All files", "*.*")], default_ext=""):
    root = tk.Tk()
    root.wm_attributes("-topmost", True)
    root.withdraw()
    return fd.asksaveasfilename(parent=root, title=title, filetypes=type, defaultextension=default_ext)

def get_file(title="", type=[("All files", "*.*")]):
    root = tk.Tk()
    root.wm_attributes("-topmost", True)
    root.withdraw()
    return fd.askopenfilename(parent=root, title=title, filetypes=type)

def get_files(title="", type=[("All files", "*.*")]):
    root = tk.Tk()
    root.wm_attributes("-topmost", True)
    root.withdraw()
    return fd.askopenfilenames(parent=root, title=title, filetypes=type)

def get_dir(title=""):
    root = tk.Tk()
    root.wm_attributes("-topmost", True)
    root.withdraw()
    return fd.askdirectory(parent=root, title=title, mustexist=True)