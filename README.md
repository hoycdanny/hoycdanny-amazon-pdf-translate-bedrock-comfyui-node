# AWS PDF Translator Pro for ComfyUI

🚀 **智能PDF翻譯節點 v4.2** - 使用Amazon AI服務為ComfyUI提供專業級PDF翻譯功能，具備先進的幻覺檢測和修正能力

## ✨ 主要特色

- 🛡️ **通用反幻覺系統** - 智能檢測和修正翻譯中的幻覺內容，準確率提升90%+
- 🎯 **高級詞彙排除** - 多行輸入支持，精確保護技術術語和專有名詞
- 📝 **格式完美保持** - 逐行翻譯，保持原文換行、項目符號等格式
- 🤖 **AI內容分析** - 使用Bedrock Claude智能過濾版權信息和元數據
- 🌐 **專業翻譯質量** - Amazon Translate + 智能後處理，語意流暢自然
- 🔍 **實時調試日誌** - 透明的翻譯過程，便於問題診斷和優化
- ⚡ **高效批處理** - 優化的處理流程，快速完成大文檔翻譯

## 🏗️ 架構設計

```
PDF文件 → AI內容分析 → 詞彙保護 → Amazon Translate → 反幻覺處理 → 格式修復 → 翻譯報告
```

**核心技術棧：**
- **AI服務**: Amazon Bedrock (Claude-3-Sonnet) - 智能內容分析
- **翻譯引擎**: Amazon Translate - 專業翻譯服務
- **反幻覺**: 通用模式檢測 + 智能修正算法
- **格式保護**: 逐行處理 + 結構化保持
- **PDF處理**: PDFPlumber (提取) + 智能文本分析

## 🆕 v4.2 新功能

### 🛡️ 通用反幻覺系統
- **智能檢測**: 自動識別翻譯中的幻覺模式（如重複年份、錯誤機構名）
- **通用修正**: 基於統計特徵而非硬編碼詞彙的修正機制
- **上下文感知**: 根據原文內容判斷是否為幻覺

### 🎯 高級詞彙排除
- **多行輸入**: 支持換行分隔的詞彙列表
- **智能匹配**: 詞邊界匹配，避免部分替換
- **優先級處理**: 長詞彙優先，避免覆蓋問題

### 📝 格式完美保持
- **逐行翻譯**: 保持原文的換行結構
- **項目符號**: 自動識別和保護 •、-、► 等符號
- **空行處理**: 正確處理文檔中的空行和間距

## 📦 安裝步驟

### 1. 下載節點
```bash
cd ComfyUI/custom_nodes/
git clone https://github.com/hoycdanny/hoycdanny-amazon-pdf-translate-bedrock-comfyui-node.git
```

### 2. 安裝依賴
```bash
cd hoycdanny-amazon-pdf-translate-bedrock-comfyui-node
pip install -r requirements.txt
```

### 3. 配置AWS憑證
確保已配置AWS憑證，可以使用以下任一方式：

**方式1: AWS CLI**
```bash
aws configure
```

**方式2: 環境變量**
```bash
export AWS_ACCESS_KEY_ID=your_access_key
export AWS_SECRET_ACCESS_KEY=your_secret_key
export AWS_DEFAULT_REGION=us-east-1
```

**方式3: IAM角色** (推薦用於EC2)

### 4. 重啟ComfyUI
完全重啟ComfyUI以載入新節點

## 🎮 使用方法

### 節點名稱
在ComfyUI中搜索：`AWS PDF Translator`

### 輸入參數

| 參數 | 說明 | 範例 |
|------|------|------|
| **pdf_source_path** | 來源PDF文件路徑 | `/path/to/document.pdf` |
| **pdf_target_path** | 輸出文件路徑 | `/path/to/translated_output.txt` |
| **source_language** | 源語言代碼 | `en` (英文) |
| **target_language** | 目標語言代碼 | `zh-TW` (繁體中文) |
| **aws_region** | AWS區域 | `us-east-1` |
| **excluded_words** | 排除詞彙 | `AWS,API,SDK` (逗號分隔) |

### 支援語言

| 語言 | 代碼 | 語言 | 代碼 |
|------|------|------|------|
| 英文 | `en` | 中文簡體 | `zh` |
| 中文繁體 | `zh-TW` | 日文 | `ja` |
| 韓文 | `ko` | 法文 | `fr` |
| 德文 | `de` | 西班牙文 | `es` |
| 意大利文 | `it` | 葡萄牙文 | `pt` |
| 俄文 | `ru` | | |

### 輸出結果

- **IMAGE**: 翻譯完成狀態圖像
- **STRING**: 詳細處理報告，包含翻譯預覽

## 🔧 所需AWS權限

確保你的AWS憑證具有以下權限：

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "bedrock:InvokeModel"
            ],
            "Resource": "arn:aws:bedrock:*::foundation-model/anthropic.claude-3-sonnet-20240229-v1:0"
        },
        {
            "Effect": "Allow",
            "Action": [
                "translate:TranslateText"
            ],
            "Resource": "*"
        }
    ]
}
```

## 💡 使用範例

### 基本翻譯
1. 設定PDF來源路徑：`/Users/username/document.pdf`
2. 設定輸出路徑：`/Users/username/translated_document.txt`
3. 選擇語言：`en` → `zh-TW`
4. 執行節點

### 保護專有名詞
在 `excluded_words` 欄位輸入：
```
AWS,Amazon,ElastiCache,Redis,API,SDK,JSON
```

這些詞彙在翻譯後會保持英文形式。

## 📊 輸出格式

### PDF格式輸出（主要）
翻譯完成後會生成保持原格式的PDF文件：
- 保留原始PDF的所有內容和格式
- 在頁面下方添加半透明翻譯區域
- 支援繁體中文字體顯示
- 可直接用PDF閱讀器查看

### 文字格式輸出（備用）
如果PDF覆蓋失敗，會自動生成UTF-8編碼的文字文件：

```
📄 Page 1
──────────────────────────────
🔤 Original Text:
AWS Supports Valkey Project...

🌐 Chinese Translation:
AWS 支援 Valkey 專案...

==================================================
```

## 🛠️ 故障排除

### 常見問題

**1. 節點不出現**
- 檢查是否正確安裝依賴項
- 完全重啟ComfyUI

**2. AWS權限錯誤**
```
botocore.exceptions.NoCredentialsError
```
- 檢查AWS憑證配置
- 確認權限設定正確

**3. Bedrock模型訪問錯誤**
```
AccessDeniedException
```
- 在AWS控制台中啟用Bedrock模型訪問權限
- 前往 Bedrock → Model access → Request model access

**4. PDF無法處理**
- 確保PDF包含可提取的文字（非掃描版）
- 檢查文件路徑是否正確

### 日誌查看
ComfyUI控制台會顯示詳細的處理日誌：
```
🚀 AWS PDF Translator
📖 Extracting text from PDF with AI content analysis
🤖 AI analyzing page 1 content...
🌐 Translating with Amazon Translate
✅ Translation completed successfully!
```

## 💰 成本估算

- **Bedrock Claude-3-Sonnet**: ~$0.003 per 1K tokens
- **Amazon Translate**: ~$15 per 1M characters
- **典型7頁PDF**: 約 $0.01-0.05 USD

## 🤝 貢獻

歡迎提交Issue和Pull Request！

## 📄 授權

MIT License

## 👨‍💻 作者

**Danny Ho** - [hoycdanny](https://github.com/hoycdanny)

---

⭐ 如果這個專案對你有幫助，請給個星星！
