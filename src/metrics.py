import numpy as np
import pandas as pd
from src.data_loader import NUMERIC

BASE = ['DWP','Policy Count','Written Exposure','Earned Premium','Earned Exposure','Ult Loss','Ult Claim Count']
RATIO_NAMES = ['Loss Ratio','Claim Frequency','Claim Severity','Loss Cost']


def safe_div(n,d):
    if pd.isna(n) or pd.isna(d) or d<=0:
        return np.nan
    return float(n)/float(d)


def totals(df, cols=None):
    cols = cols or BASE
    out={}
    for c in cols:
        if c not in df:
            out[c]=np.nan
            continue
        x=pd.to_numeric(df[c],errors='coerce')
        # A missing value is not an insured zero; don't publish ratios of partial data.
        out[c]=float(x.sum()) if len(x) and x.notna().all() else np.nan
    return out


def add_ratios(row):
    row['Loss Ratio']=safe_div(row.get('Ult Loss'),row.get('Earned Premium'))
    row['Claim Frequency']=safe_div(row.get('Ult Claim Count'),row.get('Earned Exposure'))
    row['Claim Severity']=safe_div(row.get('Ult Loss'),row.get('Ult Claim Count'))
    row['Loss Cost']=safe_div(row.get('Ult Loss'),row.get('Earned Exposure'))
    return row


def metrics(df):
    return add_ratios(totals(df))


def aggregate(df, by, cols=None):
    """Group then recalculate ratios; strict completeness for each required source metric."""
    cols=[c for c in (cols or NUMERIC) if c in df]
    if not by:
        return pd.DataFrame([metrics(df)])
    if df.empty:
        return pd.DataFrame(columns=by+cols+RATIO_NAMES)
    grouped = df.groupby(by,dropna=False,observed=True,sort=False)
    frames = []
    for keys,g in grouped:
        keys=(keys,) if len(by)==1 else keys
        row=dict(zip(by,keys))
        row.update(totals(g,cols))
        frames.append(add_ratios(row))
    return pd.DataFrame(frames)


def business_metrics(df):
    group=df['cal_New_Renew_Group'] if 'cal_New_Renew_Group' in df else df['New_Renew'].astype('string').str.strip().str.capitalize()
    new=metrics(df.loc[group=='New'])
    renew=metrics(df.loc[group=='Renew'])
    count_sum=new['Policy Count']+renew['Policy Count']
    return {'New':new,'Renew':renew,'Renew Mix':safe_div(renew['Policy Count'],count_sum),
            'LR Gap (pp)':(new['Loss Ratio']-renew['Loss Ratio'])*100 if pd.notna(new['Loss Ratio']) and pd.notna(renew['Loss Ratio']) else np.nan}


def risk_label(ratio,threshold=.75):
    if pd.isna(ratio):return 'No Data'
    if ratio<.60:return 'Low Risk'
    if ratio<threshold:return 'Medium Risk'
    return 'High Risk'


def quarter_index(df, years=None):
    y=sorted(set(int(y) for y in pd.to_numeric(df['cal_Year'],errors='coerce').dropna())) if years is None else years
    if not y: y=[2024,2025,2026]
    return pd.DataFrame([{'cal_Year_Quarter':f'{year} Q{q}','cal_Quarter_Sort':year*4+q-1} for year in y for q in range(1,5)])


def quarter_aggregate(df,by_extra=None,years=None):
    keys=['cal_Year_Quarter']+list(by_extra or [])
    out=aggregate(df,keys)
    ix=quarter_index(df,years)
    if by_extra:
        cats=df[by_extra].drop_duplicates() if len(df) else pd.DataFrame(columns=by_extra)
        if len(cats):
            ix=ix.merge(cats,how='cross')
    out=ix.merge(out,on=keys,how='left').sort_values(['cal_Quarter_Sort']+list(by_extra or []))
    return out
