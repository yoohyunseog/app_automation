 
import streamlit as st

def render_signal_badge(signal_type="STOP", status="ACTIVE"):
    color = "red" if status == "ACTIVE" else "gray"
    st.markdown(f"**[{signal_type}]** 상태: :{color}[{status}]")
