from pathlib import Path
import pandas as pd

REQUIRED = ['VEHICLE_MAKE_GROUP','VEHICLE_GROUP','MOTOR_CODE','GARAGE_DESC','LOB_Code','New_Renew','Flood_Loss_Ind','Date - Year','Date - Quarter','DWP','Policy Count','Written Exposure','Earned Premium','Earned Exposure','Ult Loss','Ult Claim Count','UseEst']
NUMERIC = ['DWP','Policy Count','Written Exposure','Earned Premium','Earned Exposure','Ult Loss','Ult Claim Count','Ult OD Dry Amount','Ult OD Dry Count','Ult OD Fresh Amount','Ult OD Fresh Count','Ult OD FT Amount','Ult OD FT Count','Ult TPPD Amount','Ult TPPD Count','Ult TPBI Amount','Ult TPBI Count','Ult OD Other Amount','Ult OD Other Count']
CLAIM_TYPES = {'OD Dry': ('Ult OD Dry Amount','Ult OD Dry Count'), 'OD Fresh': ('Ult OD Fresh Amount','Ult OD Fresh Count'), 'OD FT': ('Ult OD FT Amount','Ult OD FT Count'), 'TPPD': ('Ult TPPD Amount','Ult TPPD Count'), 'TPBI': ('Ult TPBI Amount','Ult TPBI Count'), 'OD Other': ('Ult OD Other Amount','Ult OD Other Count')}

def read_csv(source):
    return pd.read_csv(source, dtype={'MOTOR_CODE':'string'}, low_memory=False)

def validate_columns(df):
    return [col for col in REQUIRED if col not in df.columns]
