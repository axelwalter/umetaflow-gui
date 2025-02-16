import shutil
import zipfile
from pathlib import Path
from io import BytesIO

import streamlit as st
import pandas as pd

from src.common.common import reset_directory


def save_uploaded_mzML(uploaded_files: list[bytes]) -> None:
    """
    Saves uploaded mzML files to the mzML directory.

    Args:
        uploaded_files (List[bytes]): List of uploaded mzML files.

    Returns:
        None
    """
    mzML_dir = Path(st.session_state.workspace, "mzML-files")
    # If no files are uploaded, exit early
    if not uploaded_files:
        st.warning("Upload some files first.")
        return
    # Write files from buffer to workspace mzML directory, add to selected files
    for f in uploaded_files:
        if f.name not in [f.name for f in mzML_dir.iterdir()] and f.name.endswith(
            "mzML"
        ):
            with open(Path(mzML_dir, f.name), "wb") as fh:
                fh.write(f.getbuffer())
    st.success("Successfully added uploaded files!")


def copy_local_mzML_files_from_directory(local_mzML_directory: str, make_copy: bool=True) -> None:
    """
    Copies local mzML files from a specified directory to the mzML directory.

    Args:
        local_mzML_directory (str): Path to the directory containing the mzML files.
        make_copy (bool): Whether to make a copy of the files in the workspace. Default is True. If False, local file paths will be written to an external_files.txt file.

    Returns:
        None
    """
    mzML_dir = Path(st.session_state.workspace, "mzML-files")
    # Check if local directory contains mzML files, if not exit early
    if not any(Path(local_mzML_directory).glob("*.mzML")):
        st.warning("No mzML files found in specified folder.")
        return
    # Copy all mzML files to workspace mzML directory, add to selected files
    files = Path(local_mzML_directory).glob("*.mzML")
    for f in files:
        if make_copy:
            shutil.copy(f, Path(mzML_dir, f.name))
        else:
            # Create a temporary file to store the path to the local directories
            external_files = Path(mzML_dir, "external_files.txt")
            # Check if the file exists, if not create it
            if not external_files.exists():
                external_files.touch()
            # Write the path to the local directories to the file
            with open(external_files, "a") as f_handle:
                f_handle.write(f"{f}\n")
                
    st.success("Successfully added local files!")


def load_example_mzML_files() -> None:
    """
    Copies example mzML files to the mzML directory.

    Args:
        None

    Returns:
        None
    """
    mzML_dir = Path(st.session_state.workspace, "mzML-files")
    # Copy files from example-data/mzML to workspace mzML directory, add to selected files
    for f in Path("example-data", "mzML").glob("*.mzML"):
        shutil.copy(f, mzML_dir)
    st.success("Example mzML files loaded!")


def remove_selected_mzML_files(to_remove: list[str], params: dict) -> dict:
    """
    Removes selected mzML files from the mzML directory.

    Args:
        to_remove (List[str]): List of mzML files to remove.
        params (dict): Parameters.


    Returns:
        dict: parameters with updated mzML files
    """
    mzML_dir = Path(st.session_state.workspace, "mzML-files")
    # remove all given files from mzML workspace directory and selected files
    for f in to_remove:
        Path(mzML_dir, f + ".mzML").unlink()
    for k, v in params.items():
        if isinstance(v, list):
            if f in v:
                params[k].remove(f)
    st.success("Selected mzML files removed!")
    return params


def remove_all_mzML_files(params: dict) -> dict:
    """
    Removes all mzML files from the mzML directory.

    Args:
        params (dict): Parameters.

    Returns:
        dict: parameters with updated mzML files
    """
    mzML_dir = Path(st.session_state.workspace, "mzML-files")
    # reset (delete and re-create) mzML directory in workspace
    reset_directory(mzML_dir)
    # reset all parameter items which have mzML in key and are list
    for k, v in params.items():
        if "mzML" in k and isinstance(v, list):
            params[k] = []
    st.success("All mzML files removed!")
    return params


def update_mzML_df(df_path, mzML_dir):
    if not df_path.exists():
        files = [f.name for f in Path(mzML_dir).iterdir() if f.is_file()]
        df = pd.DataFrame({"file name": files, "use in workflows": [True] * len(files)})
    else:
        df = pd.read_csv(df_path, sep="\t")

        # Get list of files currently in mzML_dir
        current_files = set(f.name for f in Path(mzML_dir).iterdir() if f.is_file())

        # Keep only rows in DataFrame for files that are in the directory
        df = df[df["file name"].isin(current_files)]

        # Create a set of existing file names for quick lookup
        existing_files = set(df["file name"])

        # Iterate through mzML_dir and check for new .mzML files
        new_files = [f.name for f in Path(mzML_dir).iterdir() if f.is_file() and f.suffix == ".mzML" and f.name not in existing_files]

        # Add new files to the DataFrame
        if new_files:
            new_df = pd.DataFrame({"file name": new_files, "use in workflows": [True] * len(new_files)})
            df = pd.concat([df, new_df])
    # Sort the DataFrame alphabetically by file name
    return df.sort_values(by="file name").reset_index(drop=True)

def zip_files(directory):
    directory = Path(directory)  # Ensure directory is a Path object
    bytes_io = BytesIO()
    my_bar = st.progress(0, text="Compressing mzML files...")

    # List all files in the directory (ignoring subdirectories)
    files = [file for file in directory.iterdir() if file.is_file()]
    n_files = len(files) - 1

    with zipfile.ZipFile(bytes_io, 'w') as zip_file:
        for i, file_path in enumerate(files):
            zip_file.write(file_path, file_path.name)
            my_bar.progress(i / n_files)
    
    my_bar.empty()
    bytes_io.seek(0)
    return bytes_io
