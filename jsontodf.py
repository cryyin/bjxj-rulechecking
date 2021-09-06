import pandas as pd
import json

path='.\图纸\磁各庄站\extractions\monitoringMeasurementSection\table\BJXJC-SS-302-02-01-00-JG-022.JSON'

#df=pd.read_json(path)
#print(df)
jsonfile=json.load(path)
table=dict()
