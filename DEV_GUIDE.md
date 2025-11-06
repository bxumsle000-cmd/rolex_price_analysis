# Rolex 資料處理

## 概述

兩階段的 Rolex 手錶資料處理流程：
1. **RolexDataCleaner**: 初步資料清理與特徵工程
2. **DataPreprocessor**: 缺失值補值與編碼

---


## 階段一：RolexDataCleaner

### 功能
清理原始資料並建立衍生特徵。

### 基本用法

```python
from _01_datacleaner import RolexDataCleaner

# 快速執行
cleaner = RolexDataCleaner("data/rolex_scaper_clean.csv")
df = cleaner.clean_all().get_data()
cleaner.save_data("data/data.csv")
```

### 逐步執行

```python
cleaner = RolexDataCleaner("data/rolex_scaper_clean.csv", data_year=2023)
cleaner.load_data()
cleaner.clean_year_of_production()
cleaner.clean_case_diameter()
cleaner.group_case_material(threshold=0.01)
cleaner.process_scope_of_delivery()
cleaner.calculate_total_price(max_shipping=12000)
cleaner.group_location(threshold=0.01)
df = cleaner.get_data()
cleaner.save_data("data/data.csv")
```

### 參數

- `data_year`: 計算錶齡的年份（預設：2023）
- `threshold`: 稀有值分組到 "Other" 的百分比門檻（預設：0.01）
- `max_shipping`: 最大運費過濾值（預設：12000）

### 新增欄位

- `age`: 錶齡（年）
- `material_group`: 分組後的錶殼材質
- `has_box`, `has_papers`, `full_set`: 配件資訊的二元指標
- `ship_total`: 總價（價格 + 運費）
- `country`: 從 location 提取的國家

---

## 階段二：DataPreprocessor

### 功能
處理異常值、缺失值並編碼類別變數。

### 基本用法

```python
from _02_preprocess import DataPreprocessor

# 快速執行
preprocessor = DataPreprocessor("data/data.csv")
preprocessor.process_all()
preprocessor.save_data("data/data_clean.csv")
```

### 逐步執行

```python
preprocessor = DataPreprocessor("data/data.csv")
preprocessor.load_data()
preprocessor.remove_outliers(iqr_multiplier=1.5)
preprocessor.impute_all()
preprocessor.encode_categorical()
df = preprocessor.get_data()
preprocessor.save_data("data/data_clean.csv")
```

### 參數

- `iqr_multiplier`: 異常值偵測的 IQR 倍數（預設：1.5）
- `columns`: 要編碼的欄位（預設：['movement', 'condition', 'material_group', 'country']）

### 補值策略

| 欄位 | 方法 |
|--------|--------|
| `age`, `case diameter` | reference number 中位數 → model 中位數 |
| `movement`, `material_group` | reference number 眾數 → model 眾數 |
| `condition` | 全體眾數 |

### 移除的欄位

`ad name`, `case material`, `year of production`, `scope of delivery`, `location`

### 新增編碼欄位

`movement_encoded`, `condition_encoded`, `material_group_encoded`, `country_encoded`

---

## 完整流程

```python
from rolex_cleaner import RolexDataCleaner
from data_preprocessor import DataPreprocessor

# 階段一：清理
cleaner = RolexDataCleaner("data/rolex_scaper_clean.csv")
cleaner.clean_all().save_data("data/data.csv")

# 階段二：預處理
preprocessor = DataPreprocessor("data/data.csv")
preprocessor.process_all().save_data("data/data_clean.csv")

# 取得最終資料
df_final = preprocessor.get_data()

# 或直接儲存
preprocessor.save_data("data/data_clean.csv")
```

---

## 主要方法

### RolexDataCleaner
- `clean_case_size(val)`: 提取並驗證錶殼尺寸（14-60mm）
- `clean_year_of_production()`: 過濾無效年份（1905-2023），計算錶齡
- `group_case_material(threshold)`: 分組稀有材質
- `process_scope_of_delivery()`: 建立配件的二元指標
- `calculate_total_price(max_shipping)`: 計算價格與運費總和
- `group_location(threshold)`: 分組稀有國家

### DataPreprocessor
- `remove_outliers(iqr_multiplier)`: 依 reference number 移除價格異常值
- `impute_age()`: 補值缺失的錶齡
- `impute_case_diameter()`: 補值缺失的錶殼直徑
- `impute_movement()`: 補值缺失的機芯類型
- `impute_material_group()`: 補值缺失的材質分組
- `impute_condition()`: 補值缺失的狀況
- `encode_categorical(columns)`: 對指定欄位進行標籤編碼

---

## 注意事項

- 異常值移除是依 reference number 分組進行
- 缺失值補值優先使用 reference number，其次使用 model 分組
- 標籤編碼器儲存在 `preprocessor.label_encoders` 字典中

## 階段三：_03_create_database

## 概述

1. 線性迴歸計算各型號保值率
2. 建立 SQLite 資料庫與 Views

---

## 核心邏輯

### 保值率計算

對每個型號進行線性迴歸（age vs price）：

```python
slope, intercept, r_value, p_value, std_err = stats.linregress(
    ref_data['age'], 
    ref_data['price']
)
```

### 篩選條件

| 條件 | 預設值 | 說明 |
|------|--------|------|
| 樣本數 | `> 10` | 該型號資料筆數 |
| 錶齡多樣性 | `> 1` | 不同錶齡數量 |
| p-value | `< 0.05` | 統計顯著性 |
| R² | `> 0.3` | 迴歸解釋力 |

### 結果處理

- `年貶值率 = slope * -1`
- `年升值率 = slope`
- slope 負值 = 貶值，正值 = 升值

---

## 資料庫結構

### 資料表

#### 1. rolex
完整手錶資料（來自 data_clean.csv）

#### 2. value_retention_rate
保值率分析結果

| 欄位 | 說明 |
|------|------|
| `ref` | 型號編號 |
| `slope` | 斜率 |
| `r_squared` | R² 值 |
| `avg_price` | 平均價格 |
| `p_value` | p 值 |
| `n` | 樣本數 |
| `年貶值率` | 年貶值率 |
| `年升值率` | 年升值率 |

### SQL Views

#### 1. top10_depreciation_data
- 前 10 名貶值最快型號

#### 2. top10_appreciation_data
- 前 10 名升值最快型號

#### 3. price_analysis
- 價格分析使用資料

---

## 查詢範例

```python
import pandas as pd
import sqlite3

connection = sqlite3.connect("data/rolex.db")

# 查詢 Top 10 貶值
df_dep = pd.read_sql("SELECT * FROM top10_depreciation_data", connection)

# 查詢 Top 10 升值
df_app = pd.read_sql("SELECT * FROM top10_appreciation_data", connection)

# 價格分析使用資料
df= pd.read_sql("""SELECT * FROM price_analysis""", con=connection)

connection.close()
```