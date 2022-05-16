from tkinter import filedialog as fd

filename = fd.askopenfilename(title="Select library for targeted metabolomics", filetypes=[("Library Table", ".tsv")])

print(filename)