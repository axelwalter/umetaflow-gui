import streamlit as st
import os
import sys
import uuid
from pathlib import Path

st.set_page_config(page_title="UmetaFlow", page_icon="resources/icon.png", layout="wide", initial_sidebar_state="auto", menu_items=None)

try:
    # default location is online (instead of local)
    st.session_state.location = "online"

    # check if app is run locally and set default workspace
    if "local" in sys.argv:
        st.session_state.location = "local"
        if "workspace" not in st.session_state:
            st.session_state["workspace"] = "default-workspace"
    # online we want a new key generated each time
    elif "workspace" not in st.session_state:
        st.session_state["workspace"] = str(uuid.uuid1())

    # show the workspace options and info text
    with st.sidebar:
        st.markdown("### Workspaces")
        new_workspace = st.text_input("enter workspace", "")
        if st.button("**Enter Workspace**") and new_workspace:
            st.session_state["workspace"] = new_workspace
        info = f"""💡 Your workspace name:

**{st.session_state['workspace']}**

"""
        if st.session_state["location"] == "online":
            info += """
You can share this unique workspace ID with other people.

⚠️ Anyone with this ID can access your data!
"""
        else:
            info += "You can create a new workspace or enter an existing one."
        st.info(info)

    # if the selected workspace does not exist, create it
    if not os.path.exists(str(st.session_state["workspace"])):
        os.mkdir(str(st.session_state["workspace"]))

    # define directory to store mzML files
    st.session_state["mzML_files"] = Path(st.session_state["workspace"], "mzML_files")
    if not os.path.isdir(st.session_state["mzML_files"]):
        os.mkdir(st.session_state["mzML_files"])

    # if we run the packaged windows version, we start within the Python directory -> need to change working directory to ..\umetaflow-gui-main
    if "windows" in sys.argv:
        os.chdir("../umetaflow-gui-main")

    # set page title
    st.title("UmetaFlow")

    st.markdown("""
    ## A universal tool for metabolomics data analysis

    This app is based on the [UmetaFlow](https://chemrxiv.org/engage/chemrxiv/article-details/634fb68fdfbd2b6abc5c5fcd) workflow for LC-MS data analysis. UmetaFlow is implemented as a [snakemake pipeline](https://github.com/NBChub/snakemake-UmetaFlow) and as a Python version in [Jupyter notebooks](https://github.com/eeko-kon/pyOpenMS_UmetaFlow).

    ## About
    All LC-MS related analysis is done with [pyOpenMS](https://pyopenms.readthedocs.io/en/latest/index.html).
    """)
except:
    st.warning("Something went wrong.")