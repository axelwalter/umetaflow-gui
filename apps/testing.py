import streamlit as st
from utils.filehandler import get_files

def app():

    btn = st.button("choose dir")
    if btn:
        st.write(get_files("tsv", True))

    select_samples = st.multiselect("Samples", ["bear", "bee", "bussard", "blue whale", "bonobo"], ["bear", "bee", "bussard", "blue whale", "bonobo"])
    select_chroms = st.multiselect("Chromatograms", ["red", "blue", "green", "yellow"], ["red", "blue", "yellow"])

    st.write(select_samples)
    st.write(select_chroms)

    
    birds = st.multiselect("birds", ["Amsel", "Spatz", "Blaumeise", "Buntspecht"], ["Blaumeise", "Amsel"])
    st.write(birds)
    