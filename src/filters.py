import pandas as pd

FILTERS={'cal_Year':'Year','cal_Quarter':'Quarter','LOB_Code':'LOB','VEHICLE_MAKE_GROUP':'Vehicle Make','VEHICLE_GROUP':'Vehicle Group','MOTOR_CODE':'Motor Code','GARAGE_DESC':'Garage','Agent':'Agent','Flood_Loss_Ind':'Flood Loss','cal_New_Renew_Group':'New / Renew'}

def filter_data(df, selections, useest):
    result=df
    if useest != 'All':
        result=result.loc[result['cal_UseEst_Bool'].eq(useest=='True').fillna(False)]
    for col,values in selections.items():
        if values:
            result=result.loc[result[col].astype('string').isin([str(v) for v in values])]
    return result

def global_filters(df):
    import streamlit as st
    st.sidebar.markdown('### Global filters')
    # Streamlit app entrypoint hosts these widgets: same keys and states across all pages.
    st.sidebar.selectbox('UseEst', ['All','True','False'], key='global_useest',help='All includes missing/unknown UseEst; True/False exclude missing/unknown.')
    if 'global_useest' not in st.session_state:st.session_state.global_useest='All'
    selections={}
    with st.sidebar.expander('Portfolio & time slicers',expanded=False):
        for col,label in FILTERS.items():
            if col not in df:continue
            options=sorted(df[col].dropna().astype(str).unique().tolist())
            selections[col]=st.multiselect(label,options,key=f'global_{col}')
    if st.sidebar.button('Reset all filters',use_container_width=True):
        for key in list(st.session_state.keys()):
            if key.startswith('global_'):
                del st.session_state[key]
        st.rerun()
    active=[f'UseEst: {st.session_state.global_useest}']
    active += [f"{FILTERS[col]}: {', '.join(vals[:3])}{'…' if len(vals)>3 else ''}" for col,vals in selections.items() if vals]
    st.sidebar.caption(' | '.join(active))
    return filter_data(df,selections,st.session_state.global_useest),active
