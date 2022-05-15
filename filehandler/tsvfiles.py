from tkinter import filedialog as fd

filenames = fd.askopenfilenames(title="Select chromatogram files", filetypes=[("Chromatogram Table", ".tsv")])

for filename in filenames:
    print(filename)