import streamlit as st
import pandas as pd
from pathlib import Path
import numpy as np
import plotly.figure_factory as ff
import plotly.express as px
import plotly.graph_objects as go
# from sklearn.preprocessing import StandardScaler

st.set_page_config(page_title="UmetaFlow", page_icon="resources/icon.png", layout="wide", initial_sidebar_state="auto", menu_items=None)

try:
    st.title("Statistics")
    st.info("""#### 💡 Important


We have developed a web app specifically for metabolomics data analyisis. 

Visit [the GitHub repository](https://github.com/axelwalter/streamlit-metabolomics-statistics) or [**open the app**](https://axelwalter-streamlit-metabol-statistics-for-metabolomics-3ornhb.streamlit.app/) directly from here.

#### What you need from this app

Both Workflows let you download a **Feature Matrix** and a **Meta Data** table in `tsv` format. Edit the meta data by defining sample types (e.g. Sample, Blank or Pool)
and add at least one more custom attribute column to where your samples differentiate (e.g. ATTRIBUTE_Treatment: antibiotic and control).
    """)

    st.markdown("##")
    st.markdown("### Basic Statistics")

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

        st.markdown("##### Choose samples for comparison")
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
                st.markdown("**Fold Changes**")
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

        # st.markdown("### Clustering and Heatmap")
        # if st.button("**🔥 Generate Heatmap**"):
        #     df_heat = df[[col for col in df.columns if col.endswith(".mzML")]].set_index(df["metabolite"])
        #     # df_heat = StandardScaler().fit_transform(df_heat)
        #     fig = ff.create_dendrogram(df_heat.T, labels=list(df_heat.T.index))
        #     # fig.update_layout(template='plotly_white')
        #     fig.update_xaxes(side="top")
        #     st.markdown("##### Clustering")
        #     st.plotly_chart(fig)

        #     #Heatmap
        #     fig = px.imshow(df_heat,y=list(df_heat.index), x=list(df_heat.columns), text_auto=True, aspect="auto",
        #                 color_continuous_scale='RdBu_r', range_color=[-3,3])

        #     fig.update_layout(
        #         autosize=False,
        #         width=700,
        #         height=1200,
        #         xaxis_title="",
        #         yaxis_title="")

        #     # fig.update_yaxes(visible=False)
        #     fig.update_xaxes(tickangle = 35)
        #     st.markdown("##### Heatmap")
        #     st.plotly_chart(fig)

except:
    st.warning("Something went wrong.")
