import streamlit as st

st.set_page_config(layout="wide")

st.title("Statistics")
st.markdown("""## Important


We have developed a web app specifically for metabolomics data analyisis. Visit [the GitHub repository](https://github.com/axelwalter/streamlit-metabolomics-statistics) or [**open the app**](https://axelwalter-streamlit-metabol-statistics-for-metabolomics-3ornhb.streamlit.app/) directly from here.

### What you need from this app

Both Workflows let you download a **Feature Matrix** and a **Meta Data** table in `tsv` format. Edit the meta data by defining sample types (e.g. Sample, Blank or Pool)
and add at least one more custom attribute column to where your samples differentiate (e.g. ATTRIBUTE_Treatment: antibiotic and control).
""")
with st.sidebar:
    if "statistics_matrix_file" not in st.session_state:
        st.session_state.statistics_matrix_file = ""
    if "statistics_samples" not in st.session_state:
        st.session_state.statistics_samples = []
    if "statistics_features" not in st.session_state:
        st.session_state.statistics_features = []