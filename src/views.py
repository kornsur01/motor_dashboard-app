import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px
from src.metrics import metrics,aggregate,business_metrics,quarter_aggregate,safe_div,risk_label
from src.data_loader import NUMERIC,CLAIM_TYPES
from src.charts import COLORS,chart,bar,line_quarters,download
from src.validation import reconciliation

DIMS=['VEHICLE_MAKE_GROUP','VEHICLE_GROUP','MOTOR_CODE','GARAGE_DESC','LOB_Code','Agent','Flood_Loss_Ind','cal_New_Renew_Group','cal_Year_Quarter']
METRICS=['Loss Ratio','DWP','Earned Premium','Ult Loss','Claim Frequency','Claim Severity','Policy Count','Earned Exposure','Loss Cost']

def fmt(val,kind='amount'):
    if val is None or pd.isna(val):return 'N/A'
    if kind=='pct':return f'{val:.2%}'
    if kind=='pp':return f'{val:+.2f} pp'
    if kind=='integer':return f'{val:,.0f}'
    v=abs(val)
    if v>=1e9:return f'฿{val/1e9:,.2f}B'
    if v>=1e6:return f'฿{val/1e6:,.2f}M'
    if v>=1e3:return f'฿{val/1e3:,.2f}K'
    return f'฿{val:,.2f}'

def kpis(items):
    for column,(name,value,kind) in zip(st.columns(len(items)),items):
        column.metric(name,fmt(value,kind))

def title(text,df):
    st.title(text)
    st.caption(f'Filtered source rows: {len(df):,}  •  UseEst: {st.session_state.get("global_useest","All")}  •  Strict missing-value policy')
    if df.empty:st.warning('No records match the current global filters.');st.stop()

def gridtable(df,name='summary.csv',percentage_cols=None):
    st.dataframe(df,use_container_width=True,hide_index=True,column_config={col:st.column_config.NumberColumn(col,format='%.2f%%') for col in (percentage_cols or []) if col in df})
    download(df,name)

def metric_selector(label,key,default='Loss Ratio'):
    return st.selectbox(label,METRICS,index=METRICS.index(default),key=key)

def overview(df):
    title('Executive Portfolio Overview',df)
    m=metrics(df); b=business_metrics(df)
    kpis([('Overall Loss Ratio',m['Loss Ratio'],'pct'),('Total DWP',m['DWP'],'amount'),('Earned Premium',m['Earned Premium'],'amount'),('Ultimate Loss',m['Ult Loss'],'amount'),('Renew Mix',b['Renew Mix'],'pct'),('Policy Count',m['Policy Count'],'integer')])
    years=[2024,2025,2026]
    left,right=st.columns([1.5,1])
    with left:
        st.subheader('Quarterly Loss Ratio')
        compare=st.checkbox('Compare New and Renew',key='o_compare')
        line_quarters(df,'Loss Ratio','cal_New_Renew_Group' if compare else None,years)
    with right:
        st.subheader('Vehicle Make • Loss Ratio')
        n=st.selectbox('Show vehicle makes',['Top 5','Top 10','All'],key='overview_top')
        a=aggregate(df,['VEHICLE_MAKE_GROUP'])
        bar(a,'VEHICLE_MAKE_GROUP',top={'Top 5':5,'Top 10':10,'All':None}[n])
        v=st.selectbox('Focus on a make (for details)', ['All']+sorted(a['VEHICLE_MAKE_GROUP'].dropna().astype(str).unique().tolist()),key='o_make_focus')
        if v!='All':st.caption('Selected make: '+v+'; use the global Vehicle Make slicer to cross-filter every page.')
    c1,c2=st.columns(2)
    with c1:
        st.subheader('New / Renew Mix')
        unit=st.selectbox('Measure',['Policy Count','DWP','Earned Premium'],key='o_mix')
        ag=aggregate(df,['cal_New_Renew_Group']);ag=ag[ag['cal_New_Renew_Group'].isin(['New','Renew'])]
        ag=ag.dropna(subset=[unit]);ag=ag[ag[unit]>=0]
        if len(ag) and ag[unit].sum()>0:chart(px.pie(ag,values=unit,names='cal_New_Renew_Group',hole=.65,color_discrete_sequence=COLORS))
        else:st.info('No valid New / Renew mix data.')
    with c2:
        st.subheader('New / Renew Loss Ratio')
        ag=aggregate(df,['cal_New_Renew_Group']);ag=ag[ag['cal_New_Renew_Group'].isin(['New','Renew'])]
        bar(ag,'cal_New_Renew_Group',top=None,orientation='v')
        st.caption('New minus Renew: '+fmt(b['LR Gap (pp)'],'pp'))
    c3,c4=st.columns(2)
    with c3:
        st.subheader('Quarterly Premium Trend')
        unit=st.selectbox('Premium metric',['DWP','Earned Premium'],key='o_premium')
        ag=quarter_aggregate(df,years=years)
        chart(px.bar(ag,x='cal_Year_Quarter',y=unit,color_discrete_sequence=COLORS))
    with c4:
        st.subheader('Highest LR Segments')
        minprem=st.number_input('Minimum Earned Premium (THB)',min_value=0.,value=100000.,step=100000.,key='o_minprem')
        ag=aggregate(df,['VEHICLE_MAKE_GROUP','VEHICLE_GROUP','MOTOR_CODE'])
        ag=ag[(ag['Earned Premium']>=minprem)&ag['Loss Ratio'].notna()].sort_values('Loss Ratio',ascending=False).head(12)
        gridtable(ag[['VEHICLE_MAKE_GROUP','VEHICLE_GROUP','MOTOR_CODE','Earned Premium','Ult Loss','Loss Ratio','Earned Exposure']], 'overview_risk.csv')

def loss_ratio(df):
    title('Loss Ratio Deep Dive',df)
    m=metrics(df)
    kpis([('Portfolio LR',m['Loss Ratio'],'pct'),('Claim Frequency',m['Claim Frequency'],'pct'),('Claim Severity',m['Claim Severity'],'amount'),('Loss Cost',m['Loss Cost'],'amount')])
    c1,c2=st.columns(2)
    with c1:
        st.subheader('Loss Ratio by Vehicle Group')
        bar(aggregate(df,['VEHICLE_GROUP']),'VEHICLE_GROUP')
    with c2:
        st.subheader('Loss Ratio by Motor Code')
        top=st.slider('Top motor codes',5,40,15,key='lr_top')
        bar(aggregate(df,['MOTOR_CODE']),'MOTOR_CODE',top=top)
    c3,c4=st.columns(2)
    with c3:
        st.subheader('Garage Type')
        grouped=st.checkbox('Split by New / Renew',key='lr_garage_split')
        if grouped:
            ag=aggregate(df,['GARAGE_DESC','cal_New_Renew_Group']).dropna(subset=['Loss Ratio'])
            if len(ag):chart(px.bar(ag,x='GARAGE_DESC',y='Loss Ratio',color='cal_New_Renew_Group',barmode='group',color_discrete_sequence=COLORS))
        else:bar(aggregate(df,['GARAGE_DESC']),'GARAGE_DESC',orientation='v')
    with c4:
        st.subheader('Loss Ratio by Agent')
        if 'Agent' in df:
            ag=aggregate(df,['Agent']);bar(ag,'Agent',top=15)
        else:st.info('Agent column not provided.')
    st.subheader('Claim Frequency vs Claim Severity')
    by=st.selectbox('Bubble grouping',['VEHICLE_MAKE_GROUP','VEHICLE_GROUP','MOTOR_CODE','Agent'],key='lr_bubbles')
    ag=aggregate(df,[by]).dropna(subset=['Claim Frequency','Claim Severity','Earned Premium'])
    ag=ag[ag['Earned Premium']>0]
    if not ag.empty:chart(px.scatter(ag,x='Claim Frequency',y='Claim Severity',size='Earned Premium',color='Loss Ratio',hover_name=by,hover_data=['Policy Count'],color_continuous_scale='RdYlGn_r',size_max=52))
    else:st.info('No complete, valid frequency / severity records.')
    st.subheader('Underwriting Performance Matrix')
    levels=st.multiselect('Drill-down levels',['VEHICLE_MAKE_GROUP','VEHICLE_GROUP','MOTOR_CODE'],default=['VEHICLE_MAKE_GROUP','VEHICLE_GROUP'],key='lr_levels')
    if levels:
        ag=aggregate(df,levels)
        cols=levels+['Policy Count','Earned Exposure','DWP','Earned Premium','Ult Loss','Loss Ratio','Claim Frequency','Claim Severity','Loss Cost']
        gridtable(ag[cols].sort_values('Loss Ratio',ascending=False,na_position='last'),'underwriting_matrix.csv')

def new_renew(df):
    title('New vs Renew Business Performance',df)
    b=business_metrics(df)
    kpis([('New Policies',b['New']['Policy Count'],'integer'),('Renew Policies',b['Renew']['Policy Count'],'integer'),('Renew Mix',b['Renew Mix'],'pct'),('New LR',b['New']['Loss Ratio'],'pct'),('Renew LR',b['Renew']['Loss Ratio'],'pct'),('LR Gap',b['LR Gap (pp)'],'pp')])
    c1,c2=st.columns(2)
    with c1:
        st.subheader('Business Mix')
        unit=st.selectbox('Mix metric',['Policy Count','DWP','Earned Premium'],key='nr_mix')
        ag=aggregate(df,['cal_New_Renew_Group']);ag=ag[ag['cal_New_Renew_Group'].isin(['New','Renew'])].dropna(subset=[unit]);ag=ag[ag[unit]>=0]
        if len(ag) and ag[unit].sum()>0:chart(px.pie(ag,names='cal_New_Renew_Group',values=unit,hole=.6,color_discrete_sequence=COLORS))
        else:st.info('No valid mix data')
    with c2:
        st.subheader('Quarterly New vs Renew LR')
        line_quarters(df[df['cal_New_Renew_Group'].isin(['New','Renew'])],segment='cal_New_Renew_Group',years=[2024,2025,2026])
    c3,c4=st.columns(2)
    with c3:
        st.subheader('Quarterly New vs Renew DWP')
        ag=quarter_aggregate(df[df['cal_New_Renew_Group'].isin(['New','Renew'])],['cal_New_Renew_Group'],[2024,2025,2026])
        chart(px.bar(ag,x='cal_Year_Quarter',y='DWP',color='cal_New_Renew_Group',barmode='group',color_discrete_sequence=COLORS))
    with c4:
        st.subheader('New vs Renew LR by Make')
        ag=aggregate(df,['VEHICLE_MAKE_GROUP','cal_New_Renew_Group']).dropna(subset=['Loss Ratio'])
        ag=ag[ag['cal_New_Renew_Group'].isin(['New','Renew'])]
        if len(ag):
            top=ag.groupby('VEHICLE_MAKE_GROUP')['Earned Premium'].sum().nlargest(10).index
            ag=ag[ag['VEHICLE_MAKE_GROUP'].isin(top)]
            chart(px.bar(ag,y='VEHICLE_MAKE_GROUP',x='Loss Ratio',color='cal_New_Renew_Group',orientation='h',barmode='group',color_discrete_sequence=COLORS))
        else:st.info('No New / Renew data')
    st.subheader('Performance by Vehicle Make')
    rows=[]
    for make,g in df.groupby('VEHICLE_MAKE_GROUP',dropna=False):
        b=business_metrics(g)
        n,r=b['New'],b['Renew']
        rows.append({'Vehicle Make':make,'New Policy Count':n['Policy Count'],'Renew Policy Count':r['Policy Count'],'Renew Mix':b['Renew Mix'],'New DWP':n['DWP'],'Renew DWP':r['DWP'],'New LR':n['Loss Ratio'],'Renew LR':r['Loss Ratio'],'LR Gap (pp)':b['LR Gap (pp)']})
    gridtable(pd.DataFrame(rows),'new_renew_by_make.csv')
    st.info('Renew Mix is the share of Renew business among New + Renew policies, NOT a true renewal/retention rate. True renewal requires expiring policy and matching information.')

def claims(df):
    title('Claims Analysis',df)
    columns=[(label,a,c) for label,(a,c) in CLAIM_TYPES.items() if a in df and c in df]
    if not columns:st.warning('No component claim-type columns found');return
    rows=[]
    for label,a,c in columns:
        val=metrics_subset(df,[a,c]);amt=val[a];cnt=val[c]
        ep=metrics(df)['Earned Premium']
        rows.append({'Claim Type':label,'Ultimate Amount':amt,'Claim Count':cnt,'Severity':safe_div(amt,cnt),'LR Contribution':safe_div(amt,ep)})
    comp=pd.DataFrame(rows)
    recon=reconciliation(df)
    if recon is not None:st.caption(f'Ultimate claim component reconciliation difference: {fmt(recon[0])} across {recon[1]:,} complete rows (Ult Loss minus component sum).')
    c1,c2=st.columns(2)
    with c1:
        st.subheader('Ultimate Loss Composition')
        good=comp.dropna(subset=['Ultimate Amount'])
        if len(good) and good['Ultimate Amount'].sum()>0:chart(px.pie(good,names='Claim Type',values='Ultimate Amount',hole=.4,color_discrete_sequence=COLORS))
        else:st.info('No complete amount data')
    with c2:
        st.subheader('Claim Count Distribution')
        bar(comp.rename(columns={'Claim Type':'Type'}),'Type','Claim Count',None,orientation='v')
    st.subheader('Quarterly Claim Type Amount')
    periods=[]
    for q,group in df.groupby('cal_Year_Quarter',dropna=True):
        for label,a,c in columns:
            vals=metrics_subset(group,[a]);periods.append({'Quarter':q,'Claim Type':label,'Amount':vals[a]})
    qdf=pd.DataFrame(periods)
    if len(qdf):
        order=[f'{y} Q{q}' for y in [2024,2025,2026] for q in range(1,5)]
        chart(px.line(qdf,x='Quarter',y='Amount',color='Claim Type',markers=True,category_orders={'Quarter':order},color_discrete_sequence=COLORS))
    c3,c4=st.columns(2)
    with c3:
        st.subheader('Loss Ratio Contribution by Claim Type')
        bar(comp,'Claim Type','LR Contribution',None,orientation='v')
    with c4:
        st.subheader('Average Severity by Claim Type')
        bar(comp,'Claim Type','Severity',None,orientation='v')
    st.subheader('Claim Type Breakdown by Make')
    makes=st.multiselect('Select vehicle makes',sorted(df['VEHICLE_MAKE_GROUP'].dropna().astype(str).unique()),default=sorted(df['VEHICLE_MAKE_GROUP'].dropna().astype(str).unique())[:5],key='claim_makes')
    rows=[]
    for make,g in df[df['VEHICLE_MAKE_GROUP'].isin(makes)].groupby('VEHICLE_MAKE_GROUP'):
        for label,a,c in columns:rows.append({'Make':make,'Claim Type':label,'Amount':metrics_subset(g,[a])[a]})
    if rows:chart(px.bar(pd.DataFrame(rows),x='Make',y='Amount',color='Claim Type',barmode='stack',color_discrete_sequence=COLORS))
    gridtable(comp,'claim_components.csv')
    st.caption('LR Contribution = claim type amount / total Earned Premium. It is distinct from share of total losses; components may not reconcile to total Ult Loss.')

def metrics_subset(df,cols):
    from src.metrics import totals
    return totals(df,cols)

def risk(df):
    title('Risk Monitoring',df)
    a,b,c,d=st.columns(4)
    with a:threshold=st.slider('High LR threshold',0.40,1.50,.75,.05,key='r_threshold')
    with b:minprem=st.number_input('Min Earned Premium',min_value=0.,value=100000.,step=50000.,key='r_minprem')
    with c:minexp=st.number_input('Min Earned Exposure',min_value=0.,value=0.,step=100.,key='r_minexp')
    with d:minpol=st.number_input('Min Policy Count',min_value=0.,value=0.,step=100.,key='r_minpol')
    by=st.selectbox('Segment dimension',DIMS,key='r_by')
    ag=aggregate(df,[by]);ag=ag[(ag['Earned Premium']>=minprem)&(ag['Earned Exposure']>=minexp)&(ag['Policy Count']>=minpol)].copy()
    ag['Risk Level']=ag['Loss Ratio'].map(lambda x:risk_label(x,threshold))
    summary=ag['Risk Level'].value_counts()
    kpis([('High Risk Segments',summary.get('High Risk',0),'integer'),('Medium Risk',summary.get('Medium Risk',0),'integer'),('Low Risk',summary.get('Low Risk',0),'integer'),('No Data',summary.get('No Data',0),'integer')])
    levels=st.multiselect('Risk level', ['High Risk','Medium Risk','Low Risk','No Data'],default=['High Risk','Medium Risk','Low Risk','No Data'],key='r_levels')
    ag=ag[ag['Risk Level'].isin(levels)].sort_values('Loss Ratio',ascending=False,na_position='last')
    st.subheader('Risk Segment Ranking')
    gridtable(ag[[by,'Earned Premium','Ult Loss','Loss Ratio','Claim Frequency','Claim Severity','Earned Exposure','Policy Count','Risk Level']],'risk_monitoring.csv')
    st.caption('Thresholds are illustrative monitoring assumptions, not universal pricing standards. Risk classifications use aggregated filtered LR, never row-level cal_LR_Risk_Level.')

def explorer(df):
    title('Data Explorer',df)
    st.subheader('Build a Pivot-like Summary')
    dims=st.multiselect('Group by dimensions',DIMS,default=['VEHICLE_MAKE_GROUP','cal_Year_Quarter','cal_New_Renew_Group'],key='e_dims')
    chosen=st.multiselect('Metrics',METRICS,default=['DWP','Earned Premium','Ult Loss','Loss Ratio','Policy Count'],key='e_mets')
    query=st.text_input('Search displayed categories',key='e_search')
    summary=aggregate(df,dims)
    if query and dims:
        mask=pd.Series(False,index=summary.index)
        for col in dims:mask=mask | summary[col].astype('string').str.contains(query,case=False,regex=False,na=False)
        summary=summary.loc[mask]
    cols=dims+chosen
    st.caption(f'{len(summary):,} summarized groups')
    gridtable(summary[[c for c in cols if c in summary]],'pivot_analysis.csv')
    with st.expander('Data quality and column profiling'):
        profile=pd.DataFrame({'Column':df.columns,'Null Count':[int(df[col].isna().sum()) for col in df], 'Null %':[100*df[col].isna().mean() for col in df], 'Unique Categories':[int(df[col].nunique(dropna=True)) for col in df]})
        gridtable(profile,'data_profile.csv')
    with st.expander('Filtered raw rows'):
        st.caption('Raw source columns are unchanged; any added helpers begin with cal_.')
        st.dataframe(df,use_container_width=True,hide_index=True)
        download(df,'filtered_raw_data.csv')

def render(page):
    df=st.session_state['motor_data']
    if page.startswith('1_'):overview(df)
    elif page.startswith('2_'):loss_ratio(df)
    elif page.startswith('3_'):new_renew(df)
    elif page.startswith('4_'):claims(df)
    elif page.startswith('5_'):risk(df)
    elif page.startswith('6_'):explorer(df)
