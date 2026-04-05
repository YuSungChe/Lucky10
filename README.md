# 澳洲幸運10 冠軍預測

每5分鐘自動從 auluckylottery.com 抓取最新開獎資料，冷號策略預測冠軍號碼。

## 部署步驟

### 1. 建立 GitHub Repository

1. 在 GitHub 新建 Repository（可設為 Public 或 Private）
2. 將此資料夾所有檔案 push 上去

```bash
git init
git add .
git commit -m "init"
git remote add origin https://github.com/你的帳號/lucky10.git
git push -u origin main
```

### 2. 啟用 GitHub Pages

1. 進入 Repository → **Settings** → **Pages**
2. Source 選 **Deploy from a branch**
3. Branch 選 **main**，資料夾選 **/ (root)**
4. 儲存後幾分鐘即可訪問 `https://你的帳號.github.io/lucky10/`

### 3. 允許 Actions 寫入

1. **Settings** → **Actions** → **General**
2. 找到 **Workflow permissions**
3. 選 **Read and write permissions** → 儲存

### 4. 手動觸發第一次抓取

1. 進入 Repository → **Actions**
2. 點左側 **Fetch Lucky 10 Ball Results**
3. 點 **Run workflow** → **Run workflow**
4. 等待完成（約30秒），之後每5分鐘自動執行

## 檔案說明

```
lucky10/
├── index.html              # 主程式（GitHub Pages 首頁）
├── fetch_data.py           # 資料抓取腳本
├── data/
│   └── results.json        # 開獎資料（由 Actions 自動更新）
└── .github/
    └── workflows/
        └── fetch-data.yml  # 每5分鐘自動執行
```

## 注意事項

- GitHub Actions 排程最小間隔為 5 分鐘，可能偶爾延遲
- 若網站改版導致抓取失敗，data/results.json 保留舊資料不覆蓋
- 頁面每 30 秒自動重新讀取一次 results.json
- 倒數計時器依本地電腦時鐘同步，對齊每5分鐘整點
