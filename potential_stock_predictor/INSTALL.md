# 🚀 潛力股預測系統安裝指南

## 📋 系統需求

- Python 3.8 或以上版本
- 至少 4GB RAM
- 10GB 可用磁碟空間

## 🔧 安裝步驟

### 1. 基本安裝（核心功能）

```bash
# 進入專案目錄
cd potential_stock_predictor

# 安裝核心依賴
pip install -r requirements.txt
```

這將安裝基本功能所需的套件：
- pandas, numpy (資料處理)
- scikit-learn (基本機器學習)
- matplotlib (基本視覺化)
- tqdm (進度條)

### 2. 高級功能安裝（可選）

如果你需要完整的機器學習功能，請安裝以下套件：

```bash
# 高級機器學習模型
pip install lightgbm>=3.0.0
pip install xgboost>=1.5.0
pip install optuna>=2.10.0

# 統計分析
pip install scipy>=1.7.0

# 進階視覺化
pip install seaborn>=0.11.0

# 模型解釋
pip install shap>=0.40.0
```

### 3. 技術指標套件安裝（可選）

TA-Lib 是一個強大的技術指標計算庫，但安裝較為複雜：

#### macOS 安裝：
```bash
# 使用 Homebrew 安裝 TA-Lib C 庫
brew install ta-lib

# 安裝 Python 包裝器
pip install TA-Lib
```

#### Ubuntu/Debian 安裝：
```bash
# 安裝依賴
sudo apt-get install build-essential
wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz
tar -xzf ta-lib-0.4.0-src.tar.gz
cd ta-lib/
./configure --prefix=/usr
make
sudo make install

# 安裝 Python 包裝器
pip install TA-Lib
```

#### Windows 安裝：
```bash
# 下載預編譯的 wheel 檔案
# 從 https://www.lfd.uci.edu/~gohlke/pythonlibs/#ta-lib 下載對應版本
pip install TA_Lib-0.4.24-cp39-cp39-win_amd64.whl  # 根據你的 Python 版本調整
```

### 4. 開發環境安裝（可選）

如果你要進行開發或測試：

```bash
# 測試套件
pip install pytest>=7.0.0
pip install pytest-cov>=4.0.0

# Jupyter 筆記本
pip install jupyter>=1.0.0
pip install notebook>=6.0.0
pip install ipykernel>=6.0.0
```

## 🧪 驗證安裝

安裝完成後，運行以下命令驗證系統：

```bash
# 基本功能測試
python demo.py

# 如果安裝了測試套件
python -m pytest tests/ -v
```

## ⚠️ 常見問題

### 1. TA-Lib 安裝失敗

如果 TA-Lib 安裝失敗，系統會自動使用內建的技術指標計算方法，功能不受影響。

### 2. LightGBM/XGBoost 安裝失敗

這些套件在某些系統上可能需要額外的編譯工具：

```bash
# macOS
xcode-select --install

# Ubuntu/Debian
sudo apt-get install build-essential

# 然後重新安裝
pip install lightgbm xgboost
```

### 3. 記憶體不足

如果在訓練大型模型時遇到記憶體問題：

1. 減少批次大小
2. 使用較簡單的模型（如 Logistic Regression）
3. 減少特徵數量

### 4. Python 版本相容性

如果遇到版本相容性問題：

```bash
# 檢查 Python 版本
python --version

# 如果版本過舊，建議升級到 Python 3.8+
```

## 🔄 更新系統

定期更新套件以獲得最新功能和修復：

```bash
# 更新核心套件
pip install --upgrade pandas numpy scikit-learn

# 更新機器學習套件
pip install --upgrade lightgbm xgboost optuna
```

## 📦 Docker 安裝（推薦）

如果你熟悉 Docker，可以使用容器化安裝：

```dockerfile
# Dockerfile 範例
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

# 安裝 TA-Lib (可選)
RUN apt-get update && apt-get install -y \
    build-essential \
    wget \
    && wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz \
    && tar -xzf ta-lib-0.4.0-src.tar.gz \
    && cd ta-lib \
    && ./configure --prefix=/usr \
    && make && make install \
    && pip install TA-Lib

COPY . .
CMD ["python", "demo.py"]
```

```bash
# 建立和運行 Docker 容器
docker build -t potential-stock-predictor .
docker run -it potential-stock-predictor
```

## 🆘 獲得幫助

如果遇到安裝問題：

1. 檢查 Python 版本是否符合需求
2. 確保有足夠的磁碟空間和記憶體
3. 查看錯誤訊息並搜尋解決方案
4. 考慮使用虛擬環境隔離依賴

```bash
# 創建虛擬環境
python -m venv venv
source venv/bin/activate  # Linux/macOS
# 或
venv\Scripts\activate     # Windows

# 在虛擬環境中安裝
pip install -r requirements.txt
```

安裝完成後，你就可以開始使用潛力股預測系統了！🎉
