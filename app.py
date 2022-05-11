import streamlit as st
from multiapp import MultiApp
from apps import home, chromatograms, preprocessing # import your app modules here

app = MultiApp()
# st.set_page_config(layout="wide")
# Add all your application here
app.add_app("Home", home.app)
app.add_app("Extract Chromatograms", chromatograms.app)
app.add_app("Metabolomics Preprocessing", preprocessing.app)

# The main app
app.run()
