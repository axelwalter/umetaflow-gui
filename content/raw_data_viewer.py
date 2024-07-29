import streamlit as st
from streamlit_plotly_events import plotly_events

from src.common import *
from src.view import *

params = page_setup()

st.title("View raw MS data")

selected_file = st.selectbox(
    "choose file",
    [f.name for f in Path(st.session_state.workspace,
                          "mzML-files").iterdir()],
)
if selected_file:
    df = get_df(
        Path(st.session_state.workspace, "mzML-files", selected_file))
    df_MS1, df_MS2 = (
        df[df["mslevel"] == 1],
        df[df["mslevel"] == 2],
    )

    df_MS2["precursormz"] = df_MS2["precursormz"].apply(lambda x: str(round(x, 5)))
    df_MS2["RT"] = df_MS2["RT"].apply(lambda x: str(round(x, 1)))

    if not df_MS1.empty:
        tabs = st.tabs(["📈 Base peak chromatogram and MS1 spectra",
                        "📈 Peak map and MS2 spectra"])
        with tabs[0]:
            # BPC and MS1 spec
            st.markdown("💡 Click a point in the BPC to show the MS1 spectrum.")
            bpc_fig = plot_bpc(df_MS1)

            # Determine RT positions from clicks in BPC to show MS1 at this position
            bpc_points = plotly_events(bpc_fig)
            if bpc_points:
                ms1_rt = bpc_points[0]["x"]
            else:
                ms1_rt = df_MS1.loc[0, "RT"]

            spec = df_MS1.loc[df_MS1["RT"] == ms1_rt].squeeze()

            title = f"MS1 spectrum @RT {spec['RT']}"
            fig = plot_ms_spectrum(
                spec,
                title,
                "#EF553B",
            )
            show_fig(fig, title.replace(" ", "_"))

        with tabs[1]:
            with st.form("2D-peak-map-form", border=False):
                st.number_input(
                    "2D map intensity cutoff",
                    0,
                    1000000000,
                    params["2D-map-intensity-cutoff"],
                    1000,
                    key="2D-map-intensity-cutoff"
                )
                if st.form_submit_button("Render 2D peak map", type="primary", use_container_width=True):
                    map2D = plot_2D_map(
                        df_MS1,
                        df_MS2,
                        st.session_state["2D-map-intensity-cutoff"],
                    )
                    show_fig(map2D, f"{selected_file}-2D-peak-map")
            # Determine RT and mz positions from clicks in the map to get closest MS2 spectrum
            if not df_MS2.empty:
                spec = st.selectbox("select MS2 spectrum", df_MS2.apply(lambda x: f"{x['precursormz']}@{x['RT']}", axis=1))
                precursormz_value, rt_value = spec.split("@")
                spec = df_MS2[(df_MS2['precursormz'] == precursormz_value) & (df_MS2['RT'] == rt_value)].iloc[0]
                title = f"MS2 spectrum @precursor m/z {spec['precursormz']} @RT {spec['RT']}"

                ms2_fig = plot_ms_spectrum(
                    spec,
                    title,
                    "#00CC96"
                )
                show_fig(ms2_fig, title.replace(" ", "_"))

save_params(params)
