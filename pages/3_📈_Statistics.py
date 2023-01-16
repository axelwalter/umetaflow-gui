import streamlit as st
import pandas as pd
from pathlib import Path
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="UmetaFlow", page_icon="resources/icon.png", layout="wide", initial_sidebar_state="auto", menu_items=None)

try:
    st.title("Statistics")
    st.info("""### 💡 Important


    We have developed a web app specifically for metabolomics data analyisis. Visit [the GitHub repository](https://github.com/axelwalter/streamlit-metabolomics-statistics) or [**open the app**](https://axelwalter-streamlit-metabol-statistics-for-metabolomics-3ornhb.streamlit.app/) directly from here.

    ### What you need from this app

    Both Workflows let you download a **Feature Matrix** and a **Meta Data** table in `tsv` format. Edit the meta data by defining sample types (e.g. Sample, Blank or Pool)
    and add at least one more custom attribute column to where your samples differentiate (e.g. ATTRIBUTE_Treatment: antibiotic and control).
    """)

    st.markdown("##")
    st.markdown("### Calculate Fold Changes")

    st.radio("choose data from workflow", ["Extracted Ion Chromatograms", "Metabolomics"], key="stats-choice")

    df = pd.DataFrame()

    if st.session_state["stats-choice"] == "Metabolomics":
        if Path(st.session_state["workspace"], "results-metabolomics", "FeatureMatrix.tsv").is_file():
            df = pd.read_csv(Path(st.session_state["workspace"], "results-metabolomics", "FeatureMatrix.tsv"), sep="\t")
        else:
            st.warning("No metabolomics results found.")
    else:
        if Path(st.session_state["workspace"], "results-extract-chromatograms", "summary.tsv").is_file():
            df = pd.read_csv(Path(st.session_state["workspace"], "results-extract-chromatograms", "summary.tsv"), sep="\t")
        else:
            st.warning("No chromatogram extraction results found.")

    if not df.empty:
        st.dataframe(df)
        samples = set([col[:-5].split("#")[0] for col in df.columns if col.endswith(".mzML")])

        st.markdown("**Choose samples for comparison**")
        st.info("💡 Samples with equal names before a `#` symbol (replicates) will be grouped together.")
        c1, c2 = st.columns(2)
        a = c1.selectbox("samples A", samples)
        b = c2.selectbox("samples B", samples)

        if a != b:
            mean = pd.concat([df[[col for col in df.columns if a in col]].mean(axis=1), df[[col for col in df.columns if b in col]].mean(axis=1)], axis=1).set_index(df.metabolite).rename(columns={0: a, 1: b})
            change = pd.DataFrame(np.log2(mean[a] / mean[b])).rename(columns={0: "log2 fold change"})
            std = pd.concat([df[[col for col in df.columns if a in col]].std(axis=1), df[[col for col in df.columns if b in col]].std(axis=1)], axis=1).set_index(df.metabolite).rename(columns={0: a, 1: b})
            with st.expander("intermediate results"):
                st.markdown("**Mean intensities**")
                st.dataframe(mean)
                st.markdown("**Standard deviations**")
                st.dataframe(std)
                st.markdown("**Standard deviations**")
                st.dataframe(change)
            
            # show plots
            samples = mean.columns.tolist()
            features = mean.index.tolist()
            fig = go.Figure()
            for feature in features:
                if not std.empty:
                    fig.add_trace(go.Bar(x=samples, y=mean.loc[feature], name=feature, error_y=dict(type="data", array=std.loc[feature], visible=True)))
                else:
                    fig.add_trace(go.Bar(x=samples, y=mean.loc[feature], name=feature))
            fig.update_layout(title="Metabolite Intensities", yaxis=dict(title="mean intensity"))
            st.plotly_chart(fig)

            fig = px.bar(std, barmode="group")
            fig.update_layout(title="log 2 fold change", yaxis=dict(title="log 2 fold change"))
            st.plotly_chart(fig)

        else:
            st.warning("Choose different samples for comparison.")

except:
    st.warning("Something went wrong.")
