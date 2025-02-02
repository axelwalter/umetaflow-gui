import streamlit as st
import pandas as pd
from pathlib import Path
from src.common import *
from src.stats import *

params = page_setup(page="workflow")

st.info(INFO)

path = Path(
        st.session_state.workspace,
        "extracted-ion-chromatograms",
        "summary.tsv",
    )
if path.exists():
    df = pd.read_csv(path,
                     sep="\t", index_col=0)

    samples = set(
        [col[:-5].split("#")[0]
            for col in df.columns if col.endswith(".mzML")]
    )

    tabs = st.tabs(
        ["📊 Sample comparison", "🔥 Clustering & Heatmap", "📁 Feature Matrix"])
    with tabs[0]:
        help = "💡 Samples with equal names before a `#` symbol (replicates) will be grouped together."
        c1, c2 = st.columns(2)
        a = c1.selectbox("samples A", samples, help=help)
        samples.remove(a)
        b = c2.selectbox("samples B", samples, help=help)

        if a != b:
            mean, change, std = get_mean_change_std(df, a, b)

            with st.expander("intermediate results"):
                st.markdown("**Mean intensities**")
                show_table(mean, "mean-intensities")
                st.markdown("**Standard deviations**")
                show_table(std, "standard-deviations")
                st.markdown("**Fold Changes**")
                show_table(change, "fold-changes")

            # show plots
            samples = mean.columns.tolist()
            features = mean.index.tolist()
            fig = mean_intensity_plot(samples, features, mean, std)
            show_fig(fig, "metabolite-intensities")

            fig = fold_change_plot(change)
            show_fig(fig, "fold-changes")

    with tabs[1]:
        df = scale_df(
            df[[col for col in df.columns if col.endswith(".mzML")]]
        )
        fig = dendrogram(df.T)
        show_fig(fig, "dendrogram")

        fig = heatmap(df)
        show_fig(fig, "heatmap")
    with tabs[2]:
        show_table(df, "feature-matrix")
