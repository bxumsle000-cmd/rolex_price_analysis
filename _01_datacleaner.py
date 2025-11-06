import pandas as pd
import numpy as np
import re

class RolexDataCleaner:
    """用來清理和處理 Rolex 手錶資料的類別"""
    
    def __init__(self, csv_path, data_year=2023):
        """
        初始化清理器
        
        參數:
            csv_path: CSV 檔案路徑
            data_year: 資料年份 (預設 2023)
        """
        self.csv_path = csv_path
        self.data_year = data_year
        self.df = None
    
    def load_data(self):
        """讀取 CSV 檔案"""
        self.df = pd.read_csv(self.csv_path)
        return self
    
    def clean_case_size(self, val):
        """
        清理錶殼尺寸資料
        
        參數:
            val: 原始尺寸值
            
        回傳:
            清理後的數字 (float) 或 np.nan
        """
        if pd.isna(val):
            return np.nan
        
        # 全部轉小寫
        val = str(val).lower().strip()
        
        # 去掉多餘文字 (只保留數字、小數點、逗號、x)
        val = re.sub(r'[^0-9x.,]', ' ', val)
        
        # 取第一個數字 (允許小數或逗號小數)
        match = re.match(r'(\d+[.,]?\d*)', val)
        if not match:
            return np.nan
        
        num = match.group(1).replace(',', '.')
        
        try:
            num = float(num)
        except:
            return np.nan
        
        # 合理範圍檢查 (14mm~60mm 正常)
        if num < 14 or num > 60:
            return np.nan
        
        return num
    
    def clean_year_of_production(self):
        """清理生產年份並計算錶齡"""
        # 不合理的年份設為 NaN
        mask = (self.df["year of production"] > 2023) | (self.df["year of production"] < 1905)
        self.df.loc[mask, "year of production"] = np.nan
        
        # 計算錶齡
        self.df["age"] = self.data_year - self.df["year of production"]
        return self
    
    def clean_case_diameter(self):
        """清理錶殼直徑"""
        self.df["case diameter"] = self.df["case diameter"].apply(self.clean_case_size)
        return self
    
    def group_case_material(self, threshold=0.01):
        """
        將稀有材質分組為 Other
        
        參數:
            threshold: 百分比門檻 (預設 1%)
        """
        case_material_pct = self.df["case material"].value_counts(normalize=True)

        
        # 找出低於門檻的材質
        rare_materials = [m for m, pct in case_material_pct.items() if pct < threshold]
        
        # 分組
        self.df["material_group"] = self.df["case material"].apply(
            lambda x: "Other" if x in rare_materials else x
        )
        return self
    
    def process_scope_of_delivery(self):
        """處理配件資訊 (has_box, has_papers, full_set)"""
        scope_mapping = {
            'Original box, original papers': {'has_box': True, 'has_papers': True},
            'No original box, no original papers': {'has_box': False, 'has_papers': False},
            'Original box, no original papers': {'has_box': True, 'has_papers': False},
            'Original papers, no original box': {'has_box': False, 'has_papers': True}
        }
        
        for scope, mapping in scope_mapping.items():
            mask = self.df["scope of delivery"] == scope
            self.df.loc[mask, "has_box"] = mapping["has_box"]
            self.df.loc[mask, "has_papers"] = mapping["has_papers"]
        
        # 轉換為整數
        self.df["has_box"] = self.df["has_box"].astype(int)
        self.df["has_papers"] = self.df["has_papers"].astype(int)
        self.df["full_set"] = (
            self.df["scope of delivery"] == "Original box, original papers"
        ).astype(int)
        
        return self
    
    def calculate_total_price(self, max_shipping=12000):
        """
        計算總價 (價格 + 運費)
        
        參數:
            max_shipping: 最大運費限制 (預設 12000)
        """
        # 過濾不合理的運費
        self.df = self.df[self.df["aditional shipping price"] <= max_shipping]
        
        # 計算總價
        self.df["ship_total"] = self.df["price"] + self.df["aditional shipping price"]
        return self
    
    def group_location(self, threshold=0.01):
        """
        將稀有國家分組為 Other
        
        參數:
            threshold: 百分比門檻 (預設 1%)
        """
        # 提取國家
        self.df["country"] = self.df["location"].str.split(",").str[0].str.strip()
        
        # 計算百分比
        country_pct = self.df['country'].value_counts(normalize=True)
        
        # 將稀有國家設為 Other
        for country, pct in country_pct.items():
            if pct < threshold:
                mask = self.df["country"] == country
                self.df.loc[mask, "country"] = "Other"
        
        return self
    
    def clean_all(self):
        """執行所有清理步驟"""
        self.load_data()
        self.clean_year_of_production()
        self.clean_case_diameter()
        self.group_case_material()
        self.process_scope_of_delivery()
        self.calculate_total_price()
        self.group_location()
        return self
    
    def get_data(self):
        """取得清理後的資料"""
        return self.df
    
    def save_data(self, output_path):
        """
        儲存清理後的資料
        
        參數:
            output_path: 輸出檔案路徑
        """
        self.df.to_csv(output_path, index=False)
        print(f"資料已儲存至 {output_path}")
        return self


# 使用範例
if __name__ == "__main__":
    # 方法 1: 一次執行所有清理步驟
    """
    cleaner = RolexDataCleaner("data/rolex_scaper_clean.csv")
    df_cleaned = cleaner.clean_all().get_data()
    """
    
    # 方法 2: 逐步執行 (更靈活)
    cleaner = RolexDataCleaner("data/rolex_scaper_clean.csv", data_year=2023)
    cleaner.load_data()
    cleaner.clean_year_of_production()
    cleaner.clean_case_diameter()
    cleaner.group_case_material(threshold=1.0)  # 可以自訂門檻
    cleaner.process_scope_of_delivery()
    cleaner.calculate_total_price(max_shipping=12000)
    cleaner.group_location(threshold=0.01)
    
    # 取得清理後的資料
    df_cleaned = cleaner.get_data()
    
    # 或直接儲存
    cleaner.save_data("data/data.csv")