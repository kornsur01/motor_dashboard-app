import streamlit as st
CSS='''<style>
.block-container {padding-top:1.3rem;max-width:1500px}
[data-testid="stMetric"] {background:#f5f8fc;padding:14px;border:1px solid #e0e9f2;border-radius:13px}
h1,h2,h3 {color:#163454;letter-spacing:-.5px}
[data-testid="stSidebar"] {background:#f6f9fd}
</style>'''
def apply():st.markdown(CSS,unsafe_allow_html=True)
