import streamlit as st
import plotly.express as px
import pandas as pd
from src.metrics import quarter_aggregate

COLORS=['#146ca6','#13a89e','#ef9e48','#d96b65','#7b78bd']
def chart(fig,key=None):
    fig.update_layout(template='plotly_white',height=370,margin=dict(l=12,r=12,t=35,b=15),font=dict(size=12),legend_title_text='')
    st.plotly_chart(fig,use_container_width=True,key=key)

def bar(df,dimension,metric='Loss Ratio',top=10,orientation='h',color=None):
    view=df.dropna(subset=[metric]).sort_values(metric,ascending=False).head(top) if top else df.dropna(subset=[metric]).sort_values(metric,ascending=False)
    if view.empty:st.info('No valid data for this chart.');return
    fig=px.bar(view,x=metric if orientation=='h' else dimension,y=dimension if orientation=='h' else metric,color=color,orientation=orientation,color_discrete_sequence=COLORS,hover_data=[c for c in ['Earned Premium','Ult Loss','Policy Count','Earned Exposure'] if c in view])
    if orientation=='h':fig.update_layout(yaxis={'categoryorder':'total ascending'})
    chart(fig)

def line_quarters(df,metric='Loss Ratio',segment=None,years=None):
    v=quarter_aggregate(df,[segment] if segment else None,years)
    if segment:
        fig=px.line(v,x='cal_Year_Quarter',y=metric,color=segment,markers=True,color_discrete_sequence=COLORS)
    else:
        fig=px.line(v,x='cal_Year_Quarter',y=metric,markers=True,color_discrete_sequence=COLORS,hover_data=[c for c in ['Earned Premium','Ult Loss','Claim Frequency'] if c in v])
    fig.update_xaxes(categoryorder='array',categoryarray=quarter_aggregate(df,years=years)['cal_Year_Quarter'].tolist(),tickangle=-45)
    chart(fig)

def download(frame,name):
    st.download_button('Export CSV',data=frame.to_csv(index=False).encode('utf-8-sig'),file_name=name,mime='text/csv')
