import pandas as pd

def parse_useest(series):
    """True, False, and pd.NA remain three distinct states."""
    norm = series.astype('string').str.strip().str.lower()
    mapped = norm.map({'true':True,'1':True,'yes':True,'t':True,'false':False,'0':False,'no':False,'f':False})
    return mapped.astype('boolean')

def prepare(df):
    """Create ONLY cal_ columns; never overwrite a supplied field."""
    result = df.copy(deep=True)
    year = pd.to_numeric(df['Date - Year'],errors='coerce').astype('Int64')
    quarter = pd.to_numeric(df['Date - Quarter'].astype('string').str.extract(r'([1-4])',expand=False),errors='coerce').astype('Int64')
    derived = {'cal_Year':year,'cal_Quarter':quarter, 'cal_Quarter_Sort':year*4+quarter-1,
               'cal_Year_Quarter':year.astype('string')+' Q'+quarter.astype('string'),
               'cal_Quarter_Date':pd.to_datetime(dict(year=year.fillna(2000).astype(int),month=(quarter.fillna(1).astype(int)-1)*3+1,day=1), errors='coerce')}
    derived['cal_Quarter_Date'] = derived['cal_Quarter_Date'].mask(year.isna()|quarter.isna())
    nr = df['New_Renew'].astype('string').str.strip().str.lower()
    derived['cal_New_Renew_Group'] = nr.map({'new':'New','renew':'Renew','renewal':'Renew'}).fillna('Other')
    for name,values in derived.items():
        if name not in result.columns:
            result[name]=values
    # An independent normalized helper never mutates source UseEst.
    result['cal_UseEst_Bool']=parse_useest(df['UseEst'])
    return result
