import pandas as pd
from src.data_loader import REQUIRED,NUMERIC,CLAIM_TYPES

def quality(df):
    issues=[]
    for c in REQUIRED:
        if c not in df:issues.append(f'Missing required column: {c}')
    for c in NUMERIC:
        if c in df:
            v=pd.to_numeric(df[c],errors='coerce')
            bad=(df[c].notna() & v.isna()).sum()
            if bad:issues.append(f'{c}: {bad} non-numeric values')
            null=df[c].isna().sum()
            if null:issues.append(f'{c}: {null} missing values; strict ratios may show N/A')
    norm=df['cal_UseEst_Bool'] if 'cal_UseEst_Bool' in df else None
    if norm is not None and norm.isna().sum():issues.append(f'UseEst: {norm.isna().sum()} missing/unrecognized values (included in All only)')
    if 'cal_Quarter_Date' in df and df['cal_Quarter_Date'].isna().any():issues.append('Some Year/Quarter values could not be parsed.')
    return issues

def reconciliation(df):
    comps=[a for a,_ in CLAIM_TYPES.values() if a in df]
    if not comps or 'Ult Loss' not in df:return None
    a=df[comps].apply(pd.to_numeric,errors='coerce')
    total=pd.to_numeric(df['Ult Loss'],errors='coerce')
    good=total.notna() & a.notna().all(axis=1)
    if not good.any():return None
    return float((total[good]-a[good].sum(axis=1)).sum()),int(good.sum())
