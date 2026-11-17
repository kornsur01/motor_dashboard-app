from pathlib import Path
import streamlit as st
from src.data_loader import read_csv,validate_columns
from src.preprocessing import prepare
from src.filters import global_filters
from src.styling import apply
from src.validation import quality

st.set_page_config(page_title='Motor Insurance | Portfolio Analytics',page_icon='🚘',layout='wide',initial_sidebar_state='expanded')
apply()
source=Path(__file__).parent/'data'/'motor_dashboard_checked.csv'
if source.exists():raw=read_csv(source)
else:
    st.warning('data/motor_dashboard.csv not found. Upload your own CSV to use the dashboard. No insurance sample figures are fabricated.')
    uploaded=st.file_uploader('Upload motor_dashboard.csv',type=['csv'])
    if uploaded is None:st.stop()
    raw=read_csv(uploaded)
missing=validate_columns(raw)
if missing:
    st.error('Missing required columns: '+', '.join(missing));st.stop()
df=prepare(raw)
filtered,active=global_filters(df)
st.session_state['motor_data']=filtered
st.session_state['motor_raw']=df
with st.sidebar.expander('Data quality',expanded=False):
    issues=quality(df)
    if issues:
        for issue in issues[:25]:st.caption('⚠ '+issue)
    else:st.success('No basic data-quality warnings')
    st.caption(f'Source rows: {len(df):,} | Filtered rows: {len(filtered):,}')
pages=[st.Page('pages/1_Executive_Overview.py',title='Executive Overview',icon='📊'),
       st.Page('pages/2_Loss_Ratio_Analysis.py',title='Loss Ratio Analysis',icon='📉'),
       st.Page('pages/3_New_vs_Renew.py',title='New vs Renew',icon='🔄'),
       st.Page('pages/4_Claims_Analysis.py',title='Claims Analysis',icon='🧾'),
       st.Page('pages/5_Risk_Monitoring.py',title='Risk Monitoring',icon='🚩'),
       st.Page('pages/6_Data_Explorer.py',title='Data Explorer',icon='🔎')]
pg=st.navigation(pages)
pg.run()
