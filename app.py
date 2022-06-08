from lib2to3.pgen2.tokenize import Untokenizer
import streamlit as st
from multiapp import MultiApp
from apps import home, extractchroms, untargeted, targeted, testing, viewchroms, statistics # import your app modules here

app = MultiApp()
st.set_page_config(layout="wide")
# Add all your application here
app.add_app("Home", home.app)
app.add_app("Extract Chromatograms", extractchroms.app)
app.add_app("View Chromatograms", viewchroms.app)
app.add_app("Untargeted Metabolomics", untargeted.app)
app.add_app("Targeted Metabolomics", targeted.app)
app.add_app("Statistics", statistics.app)
app.add_app("Testing", testing.app)

# The main app
app.run()
