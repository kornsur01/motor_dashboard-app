import pandas as pd
from src.preprocessing import prepare,parse_useest

def test_three_state_bool():
    vals=parse_useest(pd.Series([True,False,'TRUE','0','yes',None,'unknown']))
    assert vals.tolist()[:5]==[True,False,True,False,True]
    assert pd.isna(vals.iloc[5]) and pd.isna(vals.iloc[6])

def test_no_source_mutation():
    raw=pd.DataFrame({'Date - Year':[2024],'Date - Quarter':['Qtr 1'],'New_Renew':['New'],'UseEst':[None],'Ult Loss':[None]})
    original=raw.copy(deep=True)
    result=prepare(raw)
    pd.testing.assert_frame_equal(raw,original)
    assert result['Ult Loss'].isna().iloc[0]
    assert result['cal_Quarter_Sort'].iloc[0]==2024*4
