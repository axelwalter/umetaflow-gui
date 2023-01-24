import plotly.graph_objects as go
import plotly.express as px
import numpy as np
import pandas as pd


template = "simple_white"


##############################################################################
#############                 Consensus Graphs           #####################
##############################################################################


def init_consensus_graph(df):   
    fig = px.scatter(
                    df, 
                    x="RT", 
                    y="mz",
                    marginal_x="violin", 
                    marginal_y="violin",
                    # height=600, width=800,
                    template=template
                )

    fig.update_layout(
                    showlegend=False,
                    #title_text=f"RT vs MZ", 
                    title_x=0.5
                )
    return fig

def create_consensus_graph(df1, df2, sample_name):

    fig = px.scatter(
                df1, 
                x="RT", 
                y="mz",
                marginal_x="violin", 
                marginal_y="violin", 
                color=sample_name,
                # height=600, width=800,
                template=template
            )

    fig.add_trace(
                go.Scatter(
                x=df2["RT"],
                y=df2["mz"],
                mode='markers',
                marker=dict(color="rgb(255,255,255)", line=dict(width=1, color='Grey'))
                
            ))

    fig.update_layout(
                    showlegend=False,
                    # title_text=f"RT vs MZ by intensity on {sample_name}", 
                    title_x=0.5
                )

    fig.layout.coloraxis.colorbar.title = 'Intensity'

    return fig


##############################################################################
#############                   MS1 Graphs               #####################
##############################################################################


def create_feature_graph(feat_maps_df):

    fig = px.line(
            feat_maps_df, 
            x="mz", 
            y="intensity",
            height=500, width=900,
            template = template,
            hover_name = feat_maps_df.index
        )

    fig.update_layout(
            showlegend=False,
            title_text=f"mz vs intensity", 
            title_x=0.5
        )

    fig.update_traces(customdata=feat_maps_df.index)

    return fig 


##############################################################################
#############                   MS2 Graphs               #####################
##############################################################################


def create_ms2_graph(df, index_list, sample_name):

    data_fig = []
    for index in index_list:
        rt = df[sample_name][index]["RT"]
        mz_int_data = df[sample_name][index]["mz_int_data"]

        trace = go.Line(
            x = mz_int_data["mz"],
            y = mz_int_data["intensity"],
            name = rt
        )
        data_fig.append(trace)

    fig = go.Figure(data_fig)
    
    fig.update_layout(
        template=template, 
        title="MS2",
        legend_title="Retention Time",
        title_text= f"MZ vs intensity {sample_name}", 
        title_x=0.5,
        height=500, width=900,
        )

    return 

def plot_ms_spectrum(df_spectrum, title, color):
    """
    Takes a pandas Dataframe with one row (spectrum) and generates a needle plot with m/z and intensity dimension.
    """
    def create_spectra(x,y, zero=0):
        x=np.repeat(x,3)
        y=np.repeat(y,3)
        y[::3]=y[2::3]=zero
        return pd.DataFrame({"mz": x, "intensity": y})

    df = create_spectra(df_spectrum['mzarray'].tolist()[0], df_spectrum['intarray'].tolist()[0])
    fig = px.line(df, x="mz", y="intensity")
    # fig = go.Figure()
    # fig.add_trace(go.Scatter(x=x,y=y, hoveron=x))
    fig.update_traces(line_color=color)
    fig.update_layout(
        showlegend=False,
        title_text=title,
        xaxis_title="m/z",
        yaxis_title="intensity"
    )
    return fig


def plot_bpc(df, ms1_rt, ms2_rt = 0):
    intensity = np.array([max(intensity_array) for intensity_array in df["intarray"]])
    fig = px.line(df, x="RT", y=intensity)
    fig.add_trace(go.Scatter(x=[ms1_rt], y=[intensity[np.abs(df["RT"]-ms1_rt).argmin()]], name="MS1 spectrum",
                            text="MS1", textposition="top center", textfont=dict(color='#EF553B', size=20)))
    fig.data[1].update(mode='markers+text', marker_symbol="x", marker=dict(color="#EF553B", size=12)) 
    if ms2_rt > 0:
        fig.add_trace(go.Scatter(x=[ms2_rt], y=[intensity[np.abs(df["RT"]-ms2_rt).argmin()]], name="MS2 spectrum", 
                                text="MS2", textposition="top center", textfont=dict(color='#00CC96', size=20)))
        fig.data[2].update(mode='markers+text', marker_symbol="x", marker=dict(color="#00CC96", size=12))
    fig.update_traces(showlegend=False)
    fig.update_layout(
        showlegend=False,
        title_text="base peak chromatogram",
        xaxis_title="retention time (s)",
        yaxis_title="intensity (cps)")
    return fig

def plot_peak_map_2D(df):
    fig = go.Figure()
    ints = np.concatenate([df.loc[index, "intarray"] for index in df.index])
    int_filter = ints > 1000 # show only ints over threshold
    ints = ints[int_filter]
    mzs = np.concatenate([df.loc[index, "mzarray"] for index in df.index])[int_filter]
    rts = np.concatenate([np.full(len(df.loc[index, "mzarray"]), df.loc[index, "RT"]) for index in df.index])[int_filter]

    sort = np.argsort(ints)
    ints = ints[sort]
    mzs = mzs[sort]
    rts = rts[sort]

    fig.add_trace(go.Scattergl(name="peaks", x=rts, y=mzs, mode="markers", marker_color=ints, marker_symbol="square"))
    fig.update_layout(
        xaxis_title="retention time (s)",
        yaxis_title="m/z",
        plot_bgcolor='rgb(255,255,255)',
        height=800,
        width=1000)

    fig.layout.template = "plotly_white"

    scale=[
        (0.00, "rgba(233, 233, 233, 1.0)"),
        (0.01, "rgba(243, 236, 166, 1.0)"),
        (0.1, "rgba(255, 168, 0, 1.0)"),
        (0.2, "rgba(191, 0, 191, 1.0)"),
        (0.4, "rgba(68, 0, 206, 1.0)"),
        (1.0, "rgba(33, 0, 101, 1.0)")
    ]
    fig.update_traces(marker_colorscale=scale, hovertext=ints.round(), selector=dict(type='scattergl'))
    return fig