import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
import matplotlib
from scipy import stats
import sqlite3

matplotlib.rc("font", family="Microsoft JhengHei")  # Windows 範例
matplotlib.rc("axes", unicode_minus=False)

df= pd.read_csv("data/data_clean.csv",index_col=0)

ref_depreciation = {}

for ref in df['reference number'].unique():
    ref_data = df[df['reference number'] == ref]
    if len(ref_data) >10 and len(ref_data["age"].unique())>1:
        slope, intercept, r_value, p_value, std_err = stats.linregress(ref_data['age'], ref_data['price'])
        r_squared= r_value**2
        if p_value<0.05 and r_squared> 0.3:
            ref_depreciation[ref] = {
                'slope': slope,  # 負值表示衰減程度
                'r_squared':r_squared,
                'avg_price': ref_data['price'].mean(),
                "p_value" : p_value,
                "n":len(ref_data)
            }

r_rate_df= pd.DataFrame(ref_depreciation).T
r_rate_df = r_rate_df.reset_index().rename(columns={'index': 'ref'})
r_rate_df.sort_values(by="slope",ascending=False,inplace=True)

r_rate_df["年貶值率"]= r_rate_df["slope"]*-1
r_rate_df["年升值率"]= r_rate_df["slope"]

depreciation_10= r_rate_df.nsmallest(10,"slope").reset_index(drop=True)
appreciation_10=r_rate_df.nlargest(10,"slope").reset_index(drop=True)

# ===================================================
#  SQL
# ===================================================

connection= sqlite3.connect("data/rolex.db")
df.to_sql("rolex",con=connection,if_exists="replace",index=False)
r_rate_df.to_sql("value_retention_rate",con=connection,if_exists="replace",index=False)

cur= connection.cursor()
drop_view_sql="""Drop VIEW IF EXISTS top10_depreciation_data ;
                 Drop VIEW IF EXISTS top10_appreciation_data ;
                 Drop VIEW IF EXISTS price_analysis ;
                 """

create_d_view_sql="""
Create VIEW top10_depreciation_data AS 
SELECT  DISTINCT rolex.[reference number],
        rolex.model,
        value_retention_rate.avg_price,
        value_retention_rate.年貶值率
FROM rolex
JOIN value_retention_rate
ON rolex.[reference number] = value_retention_rate.ref
ORDER BY 年貶值率 DESC
LIMIT 10
"""
create_a_view_sql="""
Create VIEW top10_appreciation_data AS 
SELECT  DISTINCT rolex.[reference number],
        rolex.model,
        value_retention_rate.avg_price,
        value_retention_rate.年升值率
FROM rolex
JOIN value_retention_rate
ON rolex.[reference number] = value_retention_rate.ref
ORDER BY 年升值率 DESC
LIMIT 10
"""
create_price_analysis_sql= """
CREATE VIEW price_analysis AS
SELECT [reference number],
        price,
        condition,
        age,
        full_set,
        has_box,
        has_papers
    FROM rolex ;
"""

cur.executescript(drop_view_sql)
cur.execute(create_d_view_sql)
cur.execute(create_a_view_sql)
cur.execute(create_price_analysis_sql)

cur.close()