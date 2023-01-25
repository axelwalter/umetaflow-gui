import streamlit as st

st.write("for testing...")

import numpy as np
import pandas as pd
import plotly.graph_objects as go

df = pd.read_csv('https://raw.githubusercontent.com/plotly/datasets/master/gapminderDataFiveYear.csv')
df = df[df['year'] == 1952]

fig = go.Figure()

for continent in df['continent'].unique():

    df_by_continent = df[df['continent'] == continent]
    st.write(np.stack((df_by_continent['country'], df_by_continent['pop']), axis=-1))

    fig.add_trace(
        go.Scatter(
            x=df_by_continent['gdpPercap'],
            y=df_by_continent['lifeExp'],
            customdata=np.stack((df_by_continent['country'], df_by_continent['pop']), axis=-1),
            mode='markers',
            opacity=0.7,
            marker={'size': 15},
            name=continent,
            hovertemplate='<b>Country</b>: %{customdata[0]}<br>' +
                          '<b>Population</b>: %{customdata[1]:,.0f}<br>' +
                          '<b>GDP</b>: %{x:$,.4f}<br>' +
                          '<b>Life Expectancy</b>: %{y:,.2f} Years' +
                          '<extra></extra>',
        )
    )

fig.update_layout(
    xaxis={'title': 'GDP Per Cap', 'type': 'log'},
    yaxis={'title': 'Life Expectancy'},
)

st.plotly_chart(fig)