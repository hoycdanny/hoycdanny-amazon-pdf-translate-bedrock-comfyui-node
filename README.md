# AWS PDF Translator for ComfyUI

🚀 **智能PDF翻譯節點** - 使用Amazon Bedrock AI和Amazon Translate為ComfyUI提供高質量PDF翻譯功能

## ✨ 特色功能

- 🤖 **AI智能內容過濾** - 使用Bedrock Claude自動識別並移除版權信息、頁碼等元數據
- 🌐 **高質量翻譯** - Amazon Translate提供專業級翻譯服務
- 🎯 **專有名詞保護** - 智能保護AWS、API、SDK等技術詞彙
- 📄 **完整格式輸出** - 生成清晰的原文對照翻譯文件
- ⚡ **快速處理** - 7頁PDF僅需4秒完成翻譯

## 🏗️ 架構設計

```
PDF文件 → AI內容分析 → Amazon Translate → 智能後處理 → 翻譯文件
```

**使用的AWS服務：**
- Amazon Bedrock (Claude-3-Sonnet) - AI內容分析
- Amazon Translate - 文字翻譯

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

翻譯完成後會生成UTF-8編碼的文字文件：

```
📄 Page 1
──────────────────────────────
🔤 Original Text:
AWS Supports Valkey Project...

🌐 Chinese Translation:
AWS 支援 Valkey 專案...

==================================================

📄 Page 2
──────────────────────────────
...
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
