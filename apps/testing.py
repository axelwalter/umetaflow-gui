import streamlit as st
import time

def update_session(state, data):
    state = data
    time.sleep(2)
    return state

def app():
    select_samples = st.multiselect("Samples", ["bear", "bee", "bussard", "blue whale", "bonobo"], ["bear", "bee", "bussard", "blue whale", "bonobo"])
    select_chroms = st.multiselect("Chromatograms", ["red", "blue", "green", "yellow"], ["red", "blue", "yellow"])

    st.write(select_samples)
    st.write(select_chroms)

    
    birds = st.multiselect("birds", ["Amsel", "Spatz", "Blaumeise", "Buntspecht"], ["Blaumeise", "Amsel"])
    st.write(birds)
    