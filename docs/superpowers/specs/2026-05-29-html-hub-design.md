# kanjo-html-hub 設計文件

- **日期**：2026-05-29
- **狀態**：已確認，待實作
- **Repo**：https://github.com/tommytang0122/kanjo-html-hub

## 目標

把各專案中想對外分享的單一自包含 HTML（spec、design doc、report 等）集中到一個 public repo，透過 GitHub Pages 分享。需求：

- 有一個首頁 index 可瀏覽全部內容，個別檔案也能用乾淨的直接網址分享。
- 分享內容皆為**單一自包含 HTML**（CSS/JS/圖片內嵌）。
- 先依**專案分資料夾**組織；未來可無痛擴充成「專案內再分類型」。
- 首頁**全自動產生**（GitHub Actions），丟檔案 + commit 即可，免手動維護清單。
- 每份 HTML 的標題/描述自動從檔案內 `<title>` / `<meta name="description">` 抓取；更新日期從 git commit 時間取得。

## 非目標（YAGNI）

- 不支援多檔案網頁（含獨立 css/js/asset 資料夾）。所有分享一律單檔自包含。
- 不引入靜態網站產生器（Eleventy / Jekyll）或任何第三方建構依賴。
- 不做搜尋、標籤、權限控管（public repo，內容皆可公開）。

## 目錄結構

```
kanjo-html-hub/
├── projects/                  # 所有分享的 HTML
│   ├── <專案A>/
│   │   ├── spec.html
│   │   └── report.html
│   └── <專案B>/
│       └── design.html
├── build/
│   └── generate_index.py      # 無依賴產生器（Python 標準庫）
├── assets/
│   └── index.css              # 首頁樣式（乾淨極簡）
├── .github/workflows/
│   └── deploy.yml             # push 時跑腳本 → 部署 Pages
└── README.md                  # 新增分享的說明
```

> **A → D 擴充**：產生器遞迴掃描 `projects/` 下任意層級的 `.html`，因此把
> `projects/<專案A>/spec.html` 改成 `projects/<專案A>/specs/spec.html` 不需修改任何程式碼。

## 元件設計

### 1. 產生器 `build/generate_index.py`

- **用途**：掃描 `projects/`，產生首頁 `index.html` 與部署目錄 `_site/`。
- **依賴**：僅 Python 3 標準庫（`pathlib`、`html.parser`、`subprocess`、`html`）。
- **行為**：
  1. 遞迴找出 `projects/` 底下所有 `.html`（任意層級）。
  2. 解析每個檔案，抓 `<title>`（缺則用檔名去副檔名）、`<meta name="description">`（可選）。
  3. 以 `git log -1 --format=%cI -- <file>` 取得最後 commit 時間作為更新日期（無 git 紀錄則留空）。
  4. 依**最上層資料夾（= 專案名）分組**排序，組內依更新日期新→舊排序。
  5. 產生 `_site/index.html`，並把整個 `projects/` 樹複製進 `_site/`，CSS 複製到 `_site/assets/`。
- **介面**：`python build/generate_index.py`（在 repo 根目錄執行，輸出到 `_site/`）。
- **HTML 解析**：用標準庫 `html.parser.HTMLParser` 只讀 `<head>`，遇到 `</head>` 即停止，避免解析整份大檔。

### 2. 首頁樣式 `assets/index.css`

- 乾淨極簡單頁：頁首標題 + 各專案區塊。
- 每個項目顯示：標題 · 描述（若有）· 更新日期 · 連結。
- 純靜態、無外部 CDN / 字型，確保離線與隱私。

### 3. 部署 workflow `.github/workflows/deploy.yml`

- **觸發**：push 到 `main`。
- **權限**：`pages: write`、`id-token: write`、`contents: read`。
- **步驟**：
  1. `actions/checkout`（`fetch-depth: 0`，取完整 git 歷史以計算更新日期）。
  2. 設定 Python，執行 `python build/generate_index.py`。
  3. `actions/upload-pages-artifact`（path：`_site`）。
  4. `actions/deploy-pages`。
- 產生的 `index.html` 與 `_site/` **不進 repo**，只存在部署產物中，保持 repo 乾淨（`_site/` 加入 `.gitignore`）。

## 資料流

```
push main
  → Actions checkout (full history)
  → generate_index.py 掃描 projects/ → 解析 head + git 日期 → 寫 _site/
  → upload-pages-artifact (_site)
  → deploy-pages → GitHub Pages
```

## 網址形式

- 首頁：`https://tommytang0122.github.io/kanjo-html-hub/`
- 直接分享：`https://tommytang0122.github.io/kanjo-html-hub/projects/<專案>/<檔名>.html`

## 錯誤處理 / 邊界情況

- `projects/` 不存在或為空 → 產生空首頁（顯示「尚無內容」提示），不報錯。
- HTML 無 `<title>` → 以檔名（去副檔名）為標題。
- HTML 無 `<meta description>` → 不顯示描述。
- 檔案無 git 歷史（尚未 commit）→ 更新日期留空。
- 非 `.html` 檔案 → 略過。

## 測試策略

- 放入 2~3 個樣本 HTML（含 title/description、缺 title、巢狀層級各一）。
- 本地執行 `python build/generate_index.py`，檢查 `_site/index.html` 是否正確分組、抓題、列日期、連結可點。
- push 後確認 GitHub Actions 綠燈、Pages 首頁與直接網址皆可正常開啟。

## 一次性設定

GitHub repo → Settings → Pages → Source 設為 **GitHub Actions**（README 會寫明步驟）。
