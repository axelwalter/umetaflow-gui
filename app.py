import streamlit as st
from multiapp import MultiApp
from apps import home, extractchroms, preprocessing, testing, viewchroms # import your app modules here

app = MultiApp()
st.set_page_config(layout="wide")
# Add all your application here
app.add_app("Home", home.app)
app.add_app("Extract Chromatograms", extractchroms.app)
app.add_app("View Chromatograms", viewchroms.app)
app.add_app("Metabolomics Preprocessing", preprocessing.app)
app.add_app("Testing", testing.app)

# The main app
app.run()
