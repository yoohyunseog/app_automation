 
import streamlit as st
import plotly.graph_objects as go

def render_nb_chart(bit_value):
    # 예제 데이터
    x = list(range(10))
    y = [bit_value * i for i in x]

    fig = go.Figure(data=go.Scatter(x=x, y=y, mode='lines+markers'))
    st.plotly_chart(fig, width='stretch')
