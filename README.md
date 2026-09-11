# kanjo-html-hub

集中分享各專案的自包含 HTML（spec、design doc、report…），透過 GitHub Pages 公開。

- 首頁：https://tommytang0122.github.io/kanjo-html-hub/
- 直接分享某份檔案：`https://tommytang0122.github.io/kanjo-html-hub/projects/<專案>/<檔名>.html`

## 新增一份分享

1. 把單一自包含的 `.html` 放到 `projects/<專案名>/` 底下（可再分子資料夾）。
2. 確保檔案有 `<title>`（首頁標題用），可選 `<meta name="description">`（首頁描述用）。
3. `git add` → `git commit` → `git push`。
4. GitHub Actions 會自動重建首頁並部署，幾分鐘後生效。

### 密碼保護的頁面

GitHub Pages 沒有存取控制（公開 repo、公開站）。需要限制對象的頁面（如 `projects/laoda-simulator/`）
由來源專案先用 [StatiCrypt](https://github.com/robinmoisson/staticrypt) 做客戶端 AES 加密再放進來，
repo 只保存加密後的 HTML；開頁面要輸入密語。首頁索引會照常顯示標題與說明（說明尾端標「密碼保護」）。

## 一次性設定（GitHub Pages）

到 repo 的 **Settings → Pages → Build and deployment → Source**，選擇 **GitHub Actions**。

## 本地預覽

```bash
python build/generate_index.py
python -m http.server -d _site 8000   # 開 http://localhost:8000
```

## 開發

```bash
python -m unittest discover -s build -p 'test_*.py' -v
```
