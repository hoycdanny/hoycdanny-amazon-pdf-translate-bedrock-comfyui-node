# -*- coding: utf-8 -*-
"""
AWS PDF翻譯器 - ComfyUI節點
使用Amazon Bedrock AI和Amazon Translate進行PDF翻譯
"""

import os
import logging
import json
from typing import List, Tuple, Any
import torch
import numpy as np
from PIL import Image, ImageDraw, ImageFont

# 設置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AWSPDFTranslator:
    """AWS PDF翻譯器節點"""
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "pdf_source_path": ("STRING", {
                    "default": "/path/to/source.pdf",
                    "multiline": False,
                    "placeholder": "PDF來源文件路徑"
                }),
                "pdf_target_path": ("STRING", {
                    "default": "/path/to/translated_output.txt",
                    "multiline": False,
                    "placeholder": "翻譯輸出文件路徑"
                }),
                "source_language": ("STRING", {
                    "default": "en",
                    "multiline": False,
                    "placeholder": "源語言代碼 (如: en, zh, ja)"
                }),
                "target_language": ("STRING", {
                    "default": "zh-TW",
                    "multiline": False,
                    "placeholder": "目標語言代碼 (如: zh-TW, ja, ko)"
                }),
                "aws_region": ("STRING", {
                    "default": "us-east-1",
                    "multiline": False,
                    "placeholder": "AWS區域"
                }),
                "excluded_words": ("STRING", {
                    "default": "<排除翻譯的字詞>\n每個換行代表一個單字\n例如：\nAWS\nAmazon\nElastiCache\nRedis\nRedis OSS\nMemoryDB\nValkey\nIDC",
                    "multiline": True,
                    "placeholder": "每行輸入一個不需要翻譯的詞彙"
                })
            }
        }
    
    RETURN_TYPES = ("IMAGE", "STRING")
    RETURN_NAMES = ("status_image", "translation_report")
    FUNCTION = "translate_pdf"
    CATEGORY = "AWS/Translation"
    
    def translate_pdf(self, pdf_source_path: str, pdf_target_path: str, 
                     source_language: str, target_language: str, 
                     aws_region: str, excluded_words: str) -> Tuple[torch.Tensor, str]:
        """主要翻譯函數"""
        try:
            logger.info("🚀 AWS PDF Translator v4.2 - Stable & Compatible")
            logger.info(f"📄 Source: {pdf_source_path}")
            logger.info(f"📄 Target: {pdf_target_path}")
            logger.info(f"🌐 Translation: {source_language} → {target_language}")
            
            # 處理排除詞彙 - 支持換行和逗號分隔
            excluded_list = []
            if excluded_words.strip():
                # 首先按換行分割
                lines = excluded_words.strip().split('\n')
                for line in lines:
                    line = line.strip()
                    # 過濾掉指導性文字
                    if line and not line.startswith('<') and not line.startswith('每個換行') and not line.startswith('例如'):
                        # 如果行中包含逗號，再按逗號分割
                        if ',' in line:
                            words = [word.strip() for word in line.split(',') if word.strip()]
                            excluded_list.extend(words)
                        else:
                            excluded_list.append(line)
            
            # 去重並保持順序
            excluded_list = list(dict.fromkeys(excluded_list))
            if excluded_list:
                logger.info(f"🚫 Excluded words ({len(excluded_list)}): {excluded_list}")
            else:
                logger.info("🚫 No excluded words specified")
            
            # 步驟1: 提取PDF文字
            logger.info("📖 Extracting text from PDF with AI content analysis")
            pages_text = self._extract_pdf_text(pdf_source_path, aws_region)
            
            if not pages_text:
                return self._create_error_result("No text extracted from PDF")
            
            # 步驟2: 翻譯文字
            logger.info(f"🌐 Translating {len(pages_text)} pages with Amazon Translate")
            translated_pages = self._translate_pages(pages_text, source_language, target_language, aws_region, excluded_list)
            
            if not translated_pages:
                return self._create_error_result("Translation failed")
            
            # 步驟3: 創建翻譯文字文件
            logger.info("📝 Creating translation text file")
            success = self._create_translation_text_file(pages_text, translated_pages, pdf_target_path)
            
            if not success:
                return self._create_error_result("Failed to create translation file")
            
            # 生成狀態報告
            txt_output_path = pdf_target_path.replace('.pdf', '_translation.txt')
            status_report = self._generate_status_report(len(pages_text), txt_output_path, pages_text, translated_pages)
            
            # 創建成功狀態圖像
            status_image = self._create_success_image()
            
            logger.info("✅ Translation completed successfully!")
            return (status_image, status_report)
            
        except Exception as e:
            logger.error(f"❌ Translation failed: {e}")
            return self._create_error_result(f"Translation failed: {str(e)}")
    
    def _extract_pdf_text(self, pdf_path: str, aws_region: str = None) -> List[str]:
        """提取PDF文字"""
        try:
            import pdfplumber
            
            pages_text = []
            with pdfplumber.open(pdf_path) as pdf:
                for i, page in enumerate(pdf.pages):
                    text = page.extract_text()
                    if text:
                        logger.info(f"  🤖 AI analyzing page {i+1} content...")
                        # 使用AI清理和過濾文字
                        cleaned_text = self._ai_filter_content(text, aws_region)
                        if cleaned_text:
                            pages_text.append(cleaned_text)
            
            logger.info(f"✅ AI extracted and filtered text from {len(pages_text)} pages")
            return pages_text
            
        except Exception as e:
            logger.error(f"❌ Failed to extract PDF text: {e}")
            return []
    
    def _ai_filter_content(self, text: str, aws_region: str) -> str:
        """使用AI智能過濾內容"""
        if not text or len(text.strip()) < 10:
            return text
        
        try:
            import boto3
            import json
            
            bedrock_client = boto3.client('bedrock-runtime', region_name=aws_region)
            
            # 構建AI分析prompt
            prompt = f"""請分析以下從PDF提取的文字，保留簡報的核心內容，移除不必要的元數據。

保留以下內容：
- 標題和主要內容
- 技術說明和功能描述
- 重要的業務信息
- 產品特性和優勢

移除以下內容：
- 版權聲明 (© 2025, Amazon Web Services, Inc...)
- 頁碼和頁面標記
- "All rights reserved" 等法律聲明
- 重複的公司免責聲明

重要：保持內容的完整性和可讀性，不要過度刪減。

原始文字：
{text}

清理後的內容："""

            # 調用Claude進行內容分析
            body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 1000,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            }
            
            response = bedrock_client.invoke_model(
                modelId="anthropic.claude-3-sonnet-20240229-v1:0",
                body=json.dumps(body)
            )
            
            response_body = json.loads(response['body'].read())
            filtered_content = response_body['content'][0]['text'].strip()
            
            # 驗證AI過濾結果
            if len(filtered_content) > 10 and len(filtered_content) < len(text) * 1.2:
                logger.info(f"🤖 AI filtered content: {len(text)} → {len(filtered_content)} chars")
                return filtered_content
            else:
                logger.warning("🤖 AI filtering result seems invalid, using fallback")
                return self._fallback_filter_content(text)
                
        except Exception as e:
            logger.warning(f"🤖 AI filtering failed: {e}, using fallback")
            return self._fallback_filter_content(text)
    
    def _fallback_filter_content(self, text: str) -> str:
        """回退的內容過濾方法"""
        import re
        
        # 簡單的正則表達式過濾
        copyright_patterns = [
            r'©\s*\d{4}.*?All rights reserved\.?',
            r'Copyright.*?\d{4}.*?reserved\.?',
            r'© \d{4}, Amazon Web Services.*?reserved\.?',
            r'Amazon Web Services, Inc\. or its affiliates\. All rights reserved\.?'
        ]
        
        cleaned_text = text
        for pattern in copyright_patterns:
            cleaned_text = re.sub(pattern, '', cleaned_text, flags=re.IGNORECASE | re.DOTALL)
        
        # 移除多餘空白
        cleaned_text = re.sub(r'\s+', ' ', cleaned_text).strip()
        
        return cleaned_text
    
    def _translate_pages(self, pages_text: List[str], source_lang: str, target_lang: str, 
                        aws_region: str, excluded_words: List[str]) -> List[str]:
        """翻譯所有頁面"""
        try:
            import boto3
            
            translate_client = boto3.client('translate', region_name=aws_region)
            translated_pages = []
            
            for i, text in enumerate(pages_text):
                logger.info(f"  🔄 Translating page {i+1}")
                
                # 翻譯文字（保護排除詞彙）
                translated_text = self._translate_with_protection(text, source_lang, target_lang, translate_client, excluded_words)
                translated_pages.append(translated_text)
                
                logger.info(f"    ✅ Page {i+1} translated")
            
            return translated_pages
            
        except Exception as e:
            logger.error(f"❌ Translation failed: {e}")
            return []
    
    def _translate_with_protection(self, text: str, source_lang: str, target_lang: str, 
                                  translate_client, excluded_words: List[str]) -> str:
        """翻譯文字並保護排除詞彙"""
        logger.info(f"🔍 DEBUG: Processing text: '{text[:100]}...'")
        logger.info(f"🔍 DEBUG: Excluded words list: {excluded_words}")
        
        if not excluded_words:
            logger.info("🔍 DEBUG: No excluded words, proceeding with normal translation")
            return self._translate_text(text, source_lang, target_lang, translate_client)
        
        # 步驟1: 用數字標記保護排除詞彙
        protected_text = text
        word_map = {}
        
        # 按長度排序，先處理長詞彙（避免短詞彙覆蓋長詞彙）
        sorted_words = sorted([w.strip() for w in excluded_words if w.strip()], key=len, reverse=True)
        logger.info(f"🔍 DEBUG: Sorted words for protection: {sorted_words}")
        
        for i, word in enumerate(sorted_words):
            if word in text:
                # 使用純數字標記，不太會被翻譯
                marker = f"999{i:03d}999"  # 例如: 999000999, 999001999
                word_map[marker] = word
                
                # 使用詞邊界匹配，避免部分匹配
                import re
                # 對於包含空格的短語，直接替換
                if ' ' in word:
                    protected_text = protected_text.replace(word, marker)
                else:
                    # 對於單詞，使用詞邊界匹配
                    pattern = r'\b' + re.escape(word) + r'\b'
                    protected_text = re.sub(pattern, marker, protected_text, flags=re.IGNORECASE)
                
                logger.info(f"    🛡️ Protected: '{word}' → {marker}")
            else:
                logger.info(f"    ❌ Word '{word}' not found in text")
        
        logger.info(f"🔍 DEBUG: Protected text: '{protected_text[:100]}...'")
        
        # 步驟2: 翻譯保護後的文字
        translated_text = self._translate_text(protected_text, source_lang, target_lang, translate_client)
        logger.info(f"🔍 DEBUG: Translated text: '{translated_text[:100]}...'")
        
        # 步驟3: 恢復原始詞彙
        for marker, original_word in word_map.items():
            if marker in translated_text:
                translated_text = translated_text.replace(marker, original_word)
                logger.info(f"    🔄 Restored: {marker} → '{original_word}'")
            else:
                logger.warning(f"    ⚠️ Marker {marker} not found in translation!")
                # 檢查是否有部分標記殘留
                partial_markers = [m for m in translated_text.split() if '999' in m and m.isdigit()]
                if partial_markers:
                    logger.warning(f"    ⚠️ Found partial markers: {partial_markers}")
                    for partial in partial_markers:
                        translated_text = translated_text.replace(partial, original_word)
                        logger.info(f"    🔄 Fixed partial marker: {partial} → '{original_word}'")
        
        logger.info(f"🔍 DEBUG: Final text: '{translated_text[:100]}...'")
        return translated_text
    
    def _translate_text(self, text: str, source_lang: str, target_lang: str, translate_client) -> str:
        """翻譯文字"""
        try:
            # 檢查是否包含換行，如果有則分段處理
            if '\n' in text:
                lines = text.split('\n')
                translated_lines = []
                
                for line in lines:
                    line = line.strip()
                    if not line:  # 空行
                        translated_lines.append('')
                        continue
                    
                    # 翻譯每一行
                    response = translate_client.translate_text(
                        Text=line,
                        SourceLanguageCode=source_lang,
                        TargetLanguageCode=target_lang
                    )
                    translated_line = response['TranslatedText']
                    
                    # 後處理：改善翻譯質量
                    improved_line = self._improve_translation_quality(translated_line, line)
                    translated_lines.append(improved_line)
                
                # 重新組合，保持換行
                return '\n'.join(translated_lines)
            
            else:
                # 單行文本直接翻譯
                response = translate_client.translate_text(
                    Text=text,
                    SourceLanguageCode=source_lang,
                    TargetLanguageCode=target_lang
                )
                translated_text = response['TranslatedText']
                
                # 後處理：改善翻譯質量
                improved_text = self._improve_translation_quality(translated_text, text)
                return improved_text
            
        except Exception as e:
            logger.error(f"❌ Translation API failed: {e}")
            return text  # 返回原文
    
    def _improve_translation_quality(self, translation: str, original_text: str) -> str:
        """通用翻譯質量改善 - 只做基本的格式清理"""
        import re
        improved = translation
        
        # 1. 基本格式清理（通用）
        # 清理多餘空格
        improved = re.sub(r'\s+', ' ', improved).strip()
        
        # 清理明顯的標點符號錯誤（通用）
        improved = re.sub(r'。」', '。', improved)
        improved = re.sub(r'，」', '，', improved)
        improved = re.sub(r'」([。，！？])', r'\1', improved)
        
        # 2. 處理項目符號格式（通用）
        if original_text.strip().startswith(('•', '-', '►')):
            if not improved.strip().startswith(('•', '-', '►')):
                if original_text.strip().startswith('•'):
                    improved = '• ' + improved.strip()
                elif original_text.strip().startswith('-'):
                    improved = '- ' + improved.strip()
                elif original_text.strip().startswith('►'):
                    improved = '► ' + improved.strip()
        
        return improved
        """選擇最佳翻譯結果，基於通用的幻覺檢測"""
        if len(translations) == 1:
            # 即使只有一個翻譯，也要檢查和修正幻覺
            return self._fix_common_hallucinations(translations[0], original_text)
        
        # 通用幻覺檢測規則
        def has_hallucination_signs(translation: str, original: str) -> int:
            """返回幻覺指數，越高越可能是幻覺"""
            score = 0
            
            # 1. 檢查是否包含明顯不相關的數字年份
            import re
            year_pattern = r'一九\d+年|二〇\d+年|\d{4}年'
            if re.search(year_pattern, translation) and not re.search(r'\d{4}', original):
                score += 20  # 提高分數，這是嚴重的幻覺
                logger.warning(f"🚨 Detected suspicious year in translation: {translation}")
            
            # 2. 檢查特定的幻覺模式
            hallucination_patterns = [
                r'一九+年',  # 連續的一九年
                r'九+年',    # 連續的九年
                r'國際.*署', # 國際XX署
                r'工商.*局', # 工商XX局
            ]
            for pattern in hallucination_patterns:
                if re.search(pattern, translation):
                    score += 15
                    logger.warning(f"🚨 Detected hallucination pattern: {pattern}")
            
            # 3. 檢查長度比例異常
            original_len = len(original.split())
            translation_len = len(translation)
            if original_len > 0:
                ratio = translation_len / original_len
                if ratio > 4 or ratio < 0.2:  # 翻譯結果長度嚴重異常
                    score += 10
                    logger.warning(f"🚨 Suspicious length ratio: {ratio}")
            
            # 4. 檢查英文縮寫是否被錯誤翻譯
            english_abbrevs = re.findall(r'\b[A-Z]{2,}\b', original)
            for abbrev in english_abbrevs:
                if abbrev not in translation and len(abbrev) <= 5:
                    score += 5
                    logger.warning(f"🚨 Missing abbreviation: {abbrev}")
            
            return score
        
        # 評估每個翻譯
        best_translation = translations[0]
        lowest_score = float('inf')
        
        for i, translation in enumerate(translations):
            score = has_hallucination_signs(translation, original_text)
            logger.info(f"Translation {i+1} hallucination score: {score}")
            logger.info(f"Translation {i+1}: {translation[:100]}...")
            
            if score < lowest_score:
                lowest_score = score
                best_translation = translation
        
        # 修正選中的翻譯
        corrected_translation = self._fix_common_hallucinations(best_translation, original_text)
        
        if lowest_score > 0:
            logger.warning(f"⚠️ Applied corrections to translation with hallucination score: {lowest_score}")
        else:
            logger.info("✅ Selected translation appears clean")
        
        return corrected_translation
    
    def _fix_common_hallucinations(self, translation: str, original_text: str) -> str:
        """通用幻覺修正機制 - 基於模式而非特定詞彙"""
        import re
        corrected = translation
        
        # 1. 通用年份幻覺檢測
        # 如果原文沒有年份，但翻譯中出現了明顯的幻覺年份模式
        has_year_in_original = bool(re.search(r'\b\d{4}\b', original_text))
        
        if not has_year_in_original:
            # 移除明顯的幻覺年份模式（連續重複的數字年份）
            hallucination_patterns = [
                r'一九{3,}\d*年?',  # 一九九九九年等（3個以上重複）
                r'二〇{3,}\d*年?',  # 二〇〇〇〇年等
                r'九{3,}\d*年?',   # 九九九九年等
                r'零{2,}\d*年?',   # 零零零年等
            ]
            
            for pattern in hallucination_patterns:
                matches = re.findall(pattern, corrected)
                if matches:
                    corrected = re.sub(pattern, '', corrected)
                    logger.info(f"🔧 Removed hallucination year pattern: {matches}")
        
        # 2. 檢測和修正異常長度的翻譯
        original_length = len(original_text.split())
        translation_length = len(corrected)
        
        if original_length > 0:
            ratio = translation_length / original_length
            if ratio > 10:  # 翻譯結果異常長，可能包含幻覺
                logger.warning(f"⚠️ Translation unusually long (ratio: {ratio:.1f})")
                # 可以考慮截斷或重新翻譯
        
        # 3. 保護原文中的重要術語
        # 提取原文中的英文縮寫和專有名詞
        important_terms = []
        
        # 英文縮寫（2-6個大寫字母）
        abbreviations = re.findall(r'\b[A-Z]{2,6}\b', original_text)
        important_terms.extend(abbreviations)
        
        # 專有名詞（首字母大寫的詞）
        proper_nouns = re.findall(r'\b[A-Z][a-z]{2,}\b', original_text)
        important_terms.extend(proper_nouns)
        
        # 去重
        important_terms = list(set(important_terms))
        
        # 檢查重要術語是否在翻譯中保留
        missing_terms = []
        for term in important_terms:
            if len(term) <= 20 and term not in corrected:
                missing_terms.append(term)
        
        if missing_terms:
            logger.warning(f"⚠️ Important terms missing in translation: {missing_terms}")
            # 注意：這裡只記錄，不自動修正，因為可能有合理的翻譯
        
        # 4. 清理格式問題
        # 移除多餘空格
        corrected = re.sub(r'\s+', ' ', corrected).strip()
        
        # 移除開頭的孤立標點符號
        corrected = re.sub(r'^[-–—•]\s*', '', corrected)
        
        # 移除明顯的格式錯誤（如連續的標點符號）
        corrected = re.sub(r'[。，]{2,}', '，', corrected)
        
        return corrected

    def _create_translation_text_file(self, original_pages: List[str], translated_pages: List[str], output_path: str) -> bool:
        """創建純文字翻譯文件"""
        try:
            # 改變輸出文件為.txt格式
            txt_output_path = output_path.replace('.pdf', '_translation.txt')
            
            logger.info(f"📝 Creating text file at: {txt_output_path}")
            
            # 確保輸出目錄存在
            output_dir = os.path.dirname(txt_output_path)
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
            
            with open(txt_output_path, 'w', encoding='utf-8') as f:
                f.write("AWS PDF Translation Report\n")
                f.write("=" * 50 + "\n\n")
                
                for i, (original, translated) in enumerate(zip(original_pages, translated_pages)):
                    f.write(f"📄 Page {i+1}\n")
                    f.write("-" * 30 + "\n\n")
                    
                    f.write("🔤 Original Text:\n")
                    f.write(original + "\n\n")
                    
                    f.write("🌐 Chinese Translation:\n")
                    f.write(translated + "\n\n")
                    
                    f.write("=" * 50 + "\n\n")
            
            # 驗證文件創建
            if os.path.exists(txt_output_path) and os.path.getsize(txt_output_path) > 0:
                logger.info(f"✅ Translation text file created: {txt_output_path}")
                return True
            else:
                logger.error(f"❌ Text file not created properly")
                return False
            
        except Exception as e:
            logger.error(f"❌ Failed to create text file: {e}")
            return False
    
    def _generate_status_report(self, pages_count: int, output_path: str, 
                               original_pages: List[str] = None, translated_pages: List[str] = None) -> str:
        """生成詳細狀態報告"""
        report = f"""📊 AWS PDF Translation Report
========================================
✅ Status: Completed Successfully
📄 Pages processed: {pages_count}
📁 Output file: {os.path.basename(output_path)}
🌐 Service: Amazon Translate + Bedrock AI
========================================

📝 Translation Preview:
"""
        
        # 添加翻譯預覽
        if original_pages and translated_pages:
            for i, (original, translated) in enumerate(zip(original_pages[:3], translated_pages[:3])):
                report += f"\n📄 Page {i+1}:\n"
                report += f"Original: {original[:150]}{'...' if len(original) > 150 else ''}\n"
                report += f"Translation: {translated[:150]}{'...' if len(translated) > 150 else ''}\n"
                report += "-" * 40 + "\n"
        
        report += f"\n✅ Complete translation saved to: {output_path}"
        return report
    
    def _create_success_image(self) -> torch.Tensor:
        """創建成功狀態圖像"""
        # 創建簡單的成功狀態圖像
        img = Image.new('RGB', (512, 256), color='lightgreen')
        draw = ImageDraw.Draw(img)
        
        try:
            # 嘗試使用系統字體
            font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 24)
        except:
            font = ImageFont.load_default()
        
        # 繪製成功信息
        draw.text((50, 100), "✅ PDF Translation", fill='darkgreen', font=font)
        draw.text((50, 140), "Completed Successfully!", fill='darkgreen', font=font)
        
        # 轉換為tensor
        img_array = np.array(img).astype(np.float32) / 255.0
        img_tensor = torch.from_numpy(img_array)[None,]
        
        return img_tensor
    
    def _create_error_result(self, error_message: str) -> Tuple[torch.Tensor, str]:
        """創建錯誤結果"""
        # 創建錯誤狀態圖像
        img = Image.new('RGB', (512, 256), color='lightcoral')
        draw = ImageDraw.Draw(img)
        
        try:
            font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 20)
        except:
            font = ImageFont.load_default()
        
        draw.text((50, 100), "❌ Translation Failed", fill='darkred', font=font)
        draw.text((50, 140), error_message[:30], fill='darkred', font=font)
        
        # 轉換為tensor
        img_array = np.array(img).astype(np.float32) / 255.0
        img_tensor = torch.from_numpy(img_array)[None,]
        
        error_report = f"""❌ AWS PDF Translation Error
========================================
Error: {error_message}
========================================"""
        
        return (img_tensor, error_report)

# 節點映射
NODE_CLASS_MAPPINGS = {
    "AWSPDFTranslator": AWSPDFTranslator
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "AWSPDFTranslator": "AWS PDF Translator"
}
