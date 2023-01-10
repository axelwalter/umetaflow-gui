import streamlit as st
from src.helpers import Helper
from pathlib import Path

st.set_page_config(layout="wide")

st.title("File Selection")

st.markdown("""
**How to upload files**

1. Browse files on your computer
2. Click the Upload mzML files button to use them with this app

The currently uploaded files will be used for data analysis in both workflows.
#
""")
with st.form("my-form", clear_on_submit=True):
        uploaded_mzML = st.file_uploader("mzML files", accept_multiple_files=True)
        _, c2, _ = st.columns(3)
        submitted = c2.form_submit_button("Upload mzML files")
# uploaded_mzML = st.file_uploader("mzML files", accept_multiple_files=True)

mzML_dir = "mzML_files"

# upload mzML files
if submitted:
    if uploaded_mzML:
        for file in uploaded_mzML:
            if file.name not in Path(mzML_dir).iterdir():
                with open(Path(mzML_dir, file.name),"wb") as f:
                        f.write(file.getbuffer())
        st.success("Uploaded all files!")
    else:
        st.warning("Add some files before uploading them.")


to_clear =[] 
st.markdown("##")
st.markdown("### Currently uploaded files")
for file in Path(mzML_dir).iterdir():
    if st.checkbox(str(file.stem)):
        to_clear.append(file)
st.markdown("##")

c1, c2 = st.columns(2)
clear_selection = c1.button("Clear Selection")
clear_all = c2.button("Clear All")

if clear_selection:
    for file in to_clear:
        file.unlink()
    st.experimental_rerun()

if clear_all:
    Helper().reset_directory("mzML_files")
    st.experimental_rerun()