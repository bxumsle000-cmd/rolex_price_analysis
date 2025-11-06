import pandas as pd
from sklearn.preprocessing import LabelEncoder

class DataPreprocessor:
    """用來預處理和清理資料的類別"""
    
    def __init__(self, csv_path="data/data.csv"):
        """
        初始化預處理器
        
        參數:
            csv_path: CSV 檔案路徑
        """
        self.csv_path = csv_path
        self.df = None
        self.label_encoders = {}
        
    def load_data(self):
        """讀取並進行初步清理"""
        df = pd.read_csv(self.csv_path, index_col=0)
        
        # 移除不需要的欄位
        df = df.drop([
            'ad name', 
            'case material', 
            'year of production', 
            'scope of delivery',
            'location'
        ], axis=1)
        
        # 移除關鍵欄位的空值
        df = df.dropna(subset=['reference number', 'price'])
        
        self.df = df
        return self
    
    def remove_outliers(self, iqr_multiplier=1.5):
        """根據 reference number 分組移除價格異常值"""
        def filter_group(group):
            Q1 = group['price'].quantile(0.25)
            Q3 = group['price'].quantile(0.75)
            IQR = Q3 - Q1
            
            lower_bound = Q1 - iqr_multiplier * IQR
            upper_bound = Q3 + iqr_multiplier * IQR
            
            return group[(group['price'] >= lower_bound) & (group['price'] <= upper_bound)]
        
        self.df = self.df.groupby(
            ['reference number']
        ).apply(filter_group).reset_index(drop=True)
        
        return self
    
    def impute_age(self):
        """補值：age（錶齡）"""
        # 先用 reference number 的中位數補值
        ref_age_map = self.df[self.df['age'].notna()].groupby(
            ['reference number']
        )['age'].median()
        self.df["age"] = self.df["age"].fillna(self.df["reference number"].map(ref_age_map))
        
        # 如果還有缺失，用 model 的中位數補值
        if self.df["age"].isna().any():
            model_age_map = self.df[self.df['age'].notna()].groupby(
                ['model']
            )['age'].median()
            self.df["age"] = self.df["age"].fillna(self.df["model"].map(model_age_map))
        
        self.df["age"] = self.df["age"].astype(int)
        return self
    
    def impute_case_diameter(self):
        """補值：case diameter（錶殼直徑）"""
        # 先用 reference number 的中位數補值
        ref_size_map = self.df[self.df['case diameter'].notna()].groupby(
            ['reference number']
        )['case diameter'].median()
        self.df["case diameter"] = self.df["case diameter"].fillna(
            self.df["reference number"].map(ref_size_map)
        )
        
        # 如果還有缺失，用 model 的中位數補值
        if self.df["case diameter"].isna().any():
            model_size_map = self.df[self.df['case diameter'].notna()].groupby(
                ['model']
            )['case diameter'].median()
            self.df["case diameter"] = self.df["case diameter"].fillna(
                self.df["model"].map(model_size_map)
            )
        
        return self
    
    def impute_movement(self):
        """補值：movement（機芯）"""
        # 先用 reference number 的眾數補值
        ref_mvmt_map = self.df[self.df['movement'].notna()].groupby(
            ['reference number']
        )['movement'].agg(lambda x: x.mode()[0])
        self.df["movement"] = self.df["movement"].fillna(
            self.df["reference number"].map(ref_mvmt_map)
        )
        
        # 如果還有缺失，用 model 的眾數補值
        if self.df["movement"].isna().any():
            model_mvmt_map = self.df[self.df['movement'].notna()].groupby(
                ['model']
            )['movement'].agg(lambda x: x.mode()[0])
            self.df["movement"] = self.df["movement"].fillna(
                self.df["model"].map(model_mvmt_map)
            )
        
        return self
    
    def impute_material_group(self):
        """補值：material_group（材質分組）"""
        # 先用 reference number 的眾數補值
        ref_mat_map = self.df[self.df['material_group'].notna()].groupby(
            ['reference number']
        )['material_group'].agg(lambda x: x.mode()[0])
        self.df["material_group"] = self.df["material_group"].fillna(
            self.df["reference number"].map(ref_mat_map)
        )
        
        # 如果還有缺失，用 model 的眾數補值
        if self.df["material_group"].isna().any():
            model_mat_map = self.df[self.df['material_group'].notna()].groupby(
                ['model']
            )['material_group'].agg(lambda x: x.mode()[0])
            self.df["material_group"] = self.df["material_group"].fillna(
                self.df["model"].map(model_mat_map)
            )
        
        return self
    
    def impute_condition(self):
        """補值：condition（狀況）"""
        # 用全體眾數補值
        self.df["condition"] = self.df["condition"].fillna(
            self.df["condition"].mode()[0]
        )
        return self
    
    def convert_price_to_int(self):
        """轉換價格欄位為整數"""
        price_cols = ["price", "aditional shipping price", "ship_total"]
        self.df[price_cols] = self.df[price_cols].astype(int)
        return self
    
    def impute_all(self):
        """執行所有補值步驟"""
        self.impute_age()
        self.impute_case_diameter()
        self.impute_movement()
        self.impute_material_group()
        self.impute_condition()
        self.convert_price_to_int()
        return self
    
    def encode_categorical(self, columns=None):
        """
        對類別變數進行 Label Encoding
        
        參數:
            columns: 要編碼的欄位列表（預設為常用的類別欄位）
        """
        if columns is None:
            columns = ['movement', 'condition', 'material_group', 'country']
        
        le = LabelEncoder()
        
        for col in columns:
            if col in self.df.columns:
                self.df[col + "_encoded"] = le.fit_transform(self.df[col])
                self.label_encoders[col] = le
        
        return self
    
    def process_all(self):
        """執行所有預處理步驟"""
        self.load_data()
        self.remove_outliers()
        self.impute_all()
        self.encode_categorical()
        return self
    
    def get_data(self):
        """取得處理後的資料"""
        return self.df
    
    def save_data(self, output_path="data/data_clean.csv"):
        """
        儲存處理後的資料
        
        參數:
            output_path: 輸出檔案路徑
        """
        self.df.to_csv(output_path)
        print(f"資料已儲存至 {output_path}")
        return self


# 使用範例
if __name__ == "__main__":
    # 方法 1: 一次執行所有步驟
    # preprocessor = DataPreprocessor("data/data.csv")
    # preprocessor.process_all()
    # preprocessor.save_data("data/data_clean.csv")
    
    # # 方法 2: 逐步執行（更靈活）
    preprocessor = DataPreprocessor("data/data.csv")
    preprocessor.load_data()
    preprocessor.remove_outliers(iqr_multiplier=1.5)  # 可調整 IQR 倍數
    preprocessor.impute_all()
    preprocessor.encode_categorical(['movement', 'condition', 'material_group', 'country'])
    df_clean = preprocessor.get_data()
    
    # 或直接儲存
    preprocessor.save_data("data/data_clean.csv")