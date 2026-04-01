import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import re
import numpy as np
import statsmodels.api as sm



df= pd.read_csv("data/data.csv",index_col=0)

# price VS log_price
fig, axes = plt.subplots(1,2, figsize=(15,8))
axes[0].hist(df['price'])
axes[0].set_title("price")
axes[1].hist(np.log1p(df['price']))
axes[1].set_title("log1p(price)")
fig.savefig("plot/01_price_vs_pricelog.png")

# Price by Age / Price by Case diameter
fig, axes = plt.subplots(1,2, figsize=(15,8))
axes[0].scatter(df['age'], df['price'], s=5, alpha=0.15)
lowess = sm.nonparametric.lowess
xy = df[['age','price']].dropna()
fit = lowess(np.log1p(xy['price']), xy['age'], frac=0.2)    
axes[0].plot(fit[:,0], np.expm1(fit[:,1]), color="red")
axes[0].set_yscale('log')
axes[0].set_xlabel('age'); axes[0].set_ylabel('price')
axes[0].set_title("Price by Age")

axes[1].scatter(df['case diameter'], df['price'], s=5, alpha=0.15)
xy = df[['case diameter','price']].dropna()
fit = lowess(np.log1p(xy['price']), xy['case diameter'], frac=0.25)
axes[1].plot(fit[:,0], np.expm1(fit[:,1]), color="red")
axes[1].set_yscale('log')
axes[1].set_xlabel('case diameter'); axes[1].set_ylabel('price')
axes[1].set_title("Price by Case diameter")
plt.tight_layout()
fig.savefig("plot/01_Price_by_Age_Case_diameter.png")

# Price by Movement / Price by Condition
fig, axes = plt.subplots(1,2, figsize=(15,8))
sns.boxplot(data=df, x="movement", y="price",ax=axes[0])
axes[0].set_yscale("log")
axes[0].set_title("Price by Movement")

sns.boxplot(data=df, x="condition", y="price",ax=axes[1])
axes[1].set_yscale("log")
axes[1].set_title("Price by Condition")
fig.savefig("plot/01_Price_by_Movement_Condition.png")

# Price by Material
plt.figure(figsize=(12,8))
sns.boxplot(data=df, x="material_group", y="price")
plt.yscale("log")
plt.title("Price by Material")
plt.savefig("plot/01_Price_by_Material_group.png")

# Price by Country
plt.figure(figsize=(15,8))
sns.boxplot(data=df, x="country", y="price")
plt.yscale("log")
plt.xticks(rotation=45)
plt.title("Price by Country")
plt.savefig("plot/01_Price_by_country.png")

# Price by Box / Price by Papers / Price by Full Set
fig, ax = plt.subplots(1, 3, figsize=(15, 5))
sns.boxplot(data=df, x='has_box', y='price', ax=ax[0])
ax[0].set_yscale('log')
ax[0].set_title('Price by Box')

sns.boxplot(data=df, x='has_papers', y='price', ax=ax[1])
ax[1].set_yscale('log')
ax[1].set_title('Price by Papers')

sns.boxplot(data=df, x='full_set', y='price', ax=ax[2])
ax[2].set_yscale('log')
ax[2].set_title('Price by Full Set')
plt.tight_layout()
plt.savefig("plot/01_Price_by_Accessories.png")



# temp
"""
# 數值缺失 heatmap
plt.figure(figsize=(15,8))
sns.heatmap(df[['price','aditional shipping price','case diameter','year of production']].isna(), cbar=False)
plt.show()
"""

"""
# median price by features
for col in ['movement', 'case material', 'condition', 'scope of delivery']:
    g = df.groupby(col)['price'].median().sort_values(ascending=False).head(10)
    print(f"[{col}] median price (top10)\n", g, "\n")

"""

"""
# category value counts
for col in ["model",'movement','case material','condition','scope of delivery']:
    print(df[col].value_counts(dropna=False))
    print("="*50)
    
"""

"""
# price eda
fig, axes = plt.subplots(1,2, figsize=(10,4))
axes[0].hist(df['price'].dropna(), bins=50)
axes[0].set_title("price")
axes[1].hist(np.log1p(df['price'].clip(lower=0)).dropna(), bins=50)
axes[1].set_title("log1p(price)")
plt.show()

"""
"""
sns.set_theme(style="ticks", palette="pastel")

# Draw a nested boxplot to show bills by day and time
sns.boxplot( x="condition",y="price",
            palette=["m", "g"],
            data=df,log_scale=True
            )
"""