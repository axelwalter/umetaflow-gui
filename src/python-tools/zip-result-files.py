import json
import sys
from pathlib import Path
import zipfile
import pandas as pd

############################
# default paramter values #
###########################
#
# Mandatory keys for each parameter
# key: a unique identifier
# value: the default value
#
# Optional keys for each parameter
# name: the name of the parameter
# hide: don't show the parameter in the parameter section (e.g. for input/output files)
# options: a list of valid options for the parameter
# min: the minimum value for the parameter (int and float)
# max: the maximum value for the parameter (int and float)
# step_size: the step size for the parameter (int and float)
# help: a description of the parameter
# widget_type: the type of widget to use for the parameter (default: auto)
# advanced: whether or not the parameter is advanced (default: False)

DEFAULTS = [
    {"key": "in", "value": [], "help": "Feature Matrix parquet file", "hide": True},
]

def get_params():
    if len(sys.argv) > 1:
        with open(sys.argv[1], "r") as f:
            return json.load(f)
    else:
        return {}

if __name__ == "__main__":
    params = get_params()
    # Add code here:
    # Files to package:
    dir = Path(params["in"][0]).parent.parent
    paths = [Path(params["in"][0]),
             Path(params["in"][0]).with_suffix(".tsv"),
             ]
    # create meta value template dataframe
    df = pd.read_parquet(paths[0])
    path = Path(dir, "meta-value-template.tsv")
    df = pd.DataFrame({"Sample_Type": ""}, index=[col for col in df.columns if col.endswith(".mzML")])
    df.index.name = "filename"
    df.to_csv(path, sep="\t")
    paths.append(path)

    paths.append(Path(dir, "ffm-df"))
    path = Path(dir, "ffmid-df")
    if path.exists():
        paths.append(path)
    path = Path(dir, "sirius-export")
    if path.exists():
        paths.append(path)
    path = Path(dir, "gnps-export")
    if path.exists():
        paths.append(path)
        
    with zipfile.ZipFile(Path(dir, "results.zip"), 'w', zipfile.ZIP_DEFLATED) as zipf:
        for path in paths:
            if path.is_file():
                # If the path is a file, write it directly
                zipf.write(path, path.name)
            elif path.is_dir():
                # If the path is a directory, recursively add its contents
                for subpath in path.rglob('*'):
                    # Use as_posix() to ensure correct path format in ZIP across platforms
                    zipf.write(subpath, subpath.relative_to(path.parent).as_posix())