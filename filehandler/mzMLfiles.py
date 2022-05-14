from tkinter import filedialog as fd

filenames = fd.askopenfilenames(title="Select mzML files", filetypes=[("MS data", ".mzML")])

for filename in filenames:
    print(filename)