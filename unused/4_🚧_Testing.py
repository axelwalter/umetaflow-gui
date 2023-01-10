import streamlit as st

st.write("for testing...")



uploaded_f = st.sidebar.file_uploader("Choose a CSV file", accept_multiple_files=True)

if uploaded_f is not None:
    @st.experimental_memo
    def kimiwa():
        uploaded_file = uploaded_f
        return uploaded_file