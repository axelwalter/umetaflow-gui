from audioop import mul
import easygui

def get_dir(title=""):
    return easygui.diropenbox(title=title)

def get_files(type="", multiple=False):
    title = f"Open {type} file"
    if multiple:
        title += "s"
    files = easygui.fileopenbox(title=title, multiple=multiple)
    if not files:
        return []
    return [file for file in files if file.endswith(type)]