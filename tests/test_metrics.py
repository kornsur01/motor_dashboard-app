import pandas as pd
import numpy as np
from src.metrics import metrics,aggregate,business_metrics,quarter_aggregate
from src.filters import filter_data
from src.preprocessing import prepare


def sample():
    return prepare(pd.DataFrame({'Date - Year':[2024,2024,2025],'Date - Quarter':['Qtr 1','Qtr 1','Qtr 4'],'New_Renew':['New','Renew','New'],'UseEst':['True','False',None], 'VEHICLE_MAKE_GROUP':['A','A','B'], 'DWP':[100.,300.,500.], 'Earned Premium':[100.,300.,500.], 'Ult Loss':[80.,30.,None], 'Policy Count':[1.,3.,5.], 'Earned Exposure':[1.,3.,5.], 'Ult Claim Count':[1.,1.,None]}))

def test_ratio_of_sums_not_mean():
    d=sample().iloc[:2]
    assert np.isclose(metrics(d)['Loss Ratio'],110/400)
    assert not np.isclose(metrics(d)['Loss Ratio'],(.8+.1)/2)

def test_strict_missing_loss():
    assert np.isnan(metrics(sample())['Loss Ratio'])
    assert np.isnan(metrics(sample().iloc[2:])['Loss Ratio'])

def test_null_is_not_zero():
    assert sample()['Ult Loss'].isna().iloc[2]

def test_business_mix():
    b=business_metrics(sample().iloc[:2]);assert np.isclose(b['Renew Mix'],.75)
    assert np.isclose(b['LR Gap (pp)'],70.)

def test_frequency_severity():
    m=metrics(sample().iloc[:2]);assert np.isclose(m['Claim Frequency'],.5)
    assert np.isclose(m['Claim Severity'],55.)

def test_zero_denominator():
    d=sample().iloc[:1].copy();d['Earned Premium']=0
    assert np.isnan(metrics(d)['Loss Ratio'])

def test_useest_three_options():
    d=sample()
    assert len(filter_data(d,{},'All'))==3
    assert len(filter_data(d,{},'True'))==1
    assert len(filter_data(d,{},'False'))==1

def test_quarters_gaps():
    q=quarter_aggregate(sample(),years=[2024,2025,2026])
    assert len(q)==12
    assert pd.isna(q.loc[q.cal_Year_Quarter=='2026 Q4','Loss Ratio']).all()

def test_preserve_original_columns():
    d=sample();assert d['UseEst'].tolist()==['True','False',None]
    assert all(col.startswith('cal_') for col in d.columns if col not in ['Date - Year','Date - Quarter','New_Renew','UseEst','VEHICLE_MAKE_GROUP','DWP','Earned Premium','Ult Loss','Policy Count','Earned Exposure','Ult Claim Count'])

def test_aggregated_group():
    out=aggregate(sample().iloc[:2],['VEHICLE_MAKE_GROUP']);assert np.isclose(out['Loss Ratio'].iloc[0],.275)
