import streamlit as st

st.write("for testing...")


# from zipfile import ZipFile
# import base64

# zipObj = ZipFile("sample.zip", "w")
# # Add multiple files to the zip
# zipObj.write("results_metabolomics/")
# # zipObj.write("results_metabolomics/MetaData.tsv")
# # close the Zip File
# zipObj.close()

# ZipfileDotZip = "sample.zip"

# with open(ZipfileDotZip, "rb") as f:
#     bytes = f.read()
#     b64 = base64.b64encode(bytes).decode()
#     href = f"<a href=\"data:file/zip;base64,{b64}\" download='{ZipfileDotZip}.zip'>\
#         Click last model weights\
#     </a>"

# st.sidebar.markdown(href, unsafe_allow_html=True)


import shutil
shutil.make_archive("sample", 'zip', "results_metabolomics")

with open("sample.zip", "rb") as fp:
    btn = st.download_button(
        label="Download ZIP",
        data=fp,
        file_name="myfile.zip",
        mime="application/zip"
    )