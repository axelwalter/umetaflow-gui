import streamlit as st
from src.view import *
from src.constants import ERRORS
from streamlit_plotly_events import plotly_events

st.set_page_config(
    page_title="UmetaFlow",
    page_icon="resources/icon.png",
    layout="wide",
    initial_sidebar_state="auto",
    menu_items=None,
)


def content():
    with st.sidebar:
        st.image("resources/OpenMS.png", "powered by")
    st.title("View raw MS data")

    st.session_state.view_spectra_dict = get_spectra_dict(st.session_state["mzML_dfs"])

    c1, c2 = st.columns(2)
    st.session_state.view_file = c1.selectbox(
        "choose file",
        st.session_state.view_spectra_dict.keys(),
    )

    st.session_state.view_df_ms1, st.session_state.view_df_ms2 = get_dfs(
        st.session_state.view_spectra_dict, st.session_state.view_file
    )

    c1.select_slider(
        "MS1 spectrum (RT) 💡 Scroll with the arrow keys!",
        st.session_state.view_df_ms1["RT"].round(2),
        key="ms1_RT",
    )
    c2.number_input(
        "2D map intensity cutoff",
        1000,
        1000000000,
        5000,
        1000,
        key="cutoff",
    )
    c2.selectbox(
        "MS2 spectrum",
        sorted(
            [
                f"{mz} m/z @ {rt} s"
                for mz, rt in zip(
                    st.session_state.view_df_ms2["precursormz"].round(4),
                    st.session_state.view_df_ms2["RT"].round(2),
                )
            ]
        ),
        key="ms2_spec",
    )

    if not st.session_state.view_df_ms2.empty:
        ms2_precmz = float(st.session_state.ms2_spec.split(" m/z")[0])
        ms2_RT = st.session_state.view_df_ms2[
            st.session_state.view_df_ms2["precursormz"].round(4) == ms2_precmz
        ]["RT"].tolist()[0]
    else:
        ms2_precmz = 0
        ms2_RT = 0

    if not st.session_state.view_df_ms1.empty:
        plot_2D_map(st.session_state.view_df_ms1, st.session_state.cutoff)
        st.session_state.view_fig_bpc = plot_bpc(
            st.session_state.view_df_ms1, st.session_state.ms1_RT, ms2_RT
        )
        st.plotly_chart(st.session_state.view_fig_bpc, use_container_width=True)

        plot_ms_spectrum(
            st.session_state.view_df_ms1[
                st.session_state.view_df_ms1["RT"].round(2) == st.session_state.ms1_RT
            ],
            f"MS1 spectrum @RT {st.session_state.ms1_RT}",
            "#EF553B",
        )
        if not st.session_state.view_df_ms2.empty:
            plot_ms_spectrum(
                st.session_state.view_df_ms2[
                    st.session_state.view_df_ms2["precursormz"].round(4) == ms2_precmz
                ],
                f"MS2 spectrum @precursor m/z {ms2_precmz} @RT {round(ms2_RT, 2)}",
                "#00CC96",
            )


if __name__ == "__main__":
    try:
        content()
    except:
        st.warning(ERRORS["visualization"])
