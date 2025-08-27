# -*- coding: utf-8 -*-
"""
AWS PDF Translator - 簡潔實用版本
"""

import torch
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import os
import logging
import boto3
from typing import Tuple, List

logger = logging.getLogger(__name__)

class AWSPDFTranslator:
    """AWS PDF翻譯器"""
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "pdf_source_path": ("STRING", {
                    "default": "/Users/dayho/Desktop/IGS_vlakey.pdf", 
                    "multiline": False,
                    "placeholder": "PDF source file path"
                }),
                "pdf_target_path": ("STRING", {
                    "default": "/Users/dayho/Desktop/translated_output.pdf", 
                    "multiline": False,
                    "placeholder": "PDF target file path"
                }),
                "source_language": ([
                    "en", "zh", "zh-TW", "ja", "ko", "fr", "de", "es", "it", "pt", "ru"
                ], {
                    "default": "en"
                }),
                "target_language": ([
                    "zh-TW", "zh", "en", "ja", "ko", "fr", "de", "es", "it", "pt", "ru"
                ], {
                    "default": "zh-TW"
                }),
                "aws_region": ([
                    "us-east-1", "us-west-2", "eu-west-1", "ap-northeast-1", "ap-southeast-1"
                ], {
                    "default": "us-east-1"
                }),
                "excluded_words": ("STRING", {
                    "default": "",
                    "multiline": False,
                    "placeholder": "用逗號分隔不需要翻譯的詞彙 (可留空)"
                })
            }
        }
    
    RETURN_TYPES = ("IMAGE", "STRING")
    RETURN_NAMES = ("translation_result", "status_report")
    FUNCTION = "translate_pdf"
    CATEGORY = "AWS/PDF"
    
    def translate_pdf(self, pdf_source_path: str, pdf_target_path: str, 
                     source_language: str, target_language: str, 
                     aws_region: str, excluded_words: str) -> Tuple[torch.Tensor, str]:
        """
        AWS PDF翻譯主函數
        """
        try:
            logger.info("🚀 AWS PDF Translator")
            logger.info(f"📄 Source: {pdf_source_path}")
            logger.info(f"📄 Target: {pdf_target_path}")
            logger.info(f"🌐 Translation: {source_language} → {target_language}")
            
            # 驗證輸入
            if not os.path.exists(pdf_source_path):
                return self._create_error_result(f"Source PDF not found: {pdf_source_path}")
            
            # 處理排除詞彙
            excluded_list = [word.strip() for word in excluded_words.split(',') if word.strip()]
            
            # 步驟1: 提取PDF文字
            logger.info("📖 Extracting text from PDF with AI content analysis")
            pages_text = self._extract_pdf_text(pdf_source_path, aws_region)
            
            if not pages_text:
                return self._create_error_result("Failed to extract text from PDF")
            
            # 步驟2: 翻譯文字
            logger.info("🌐 Translating with Amazon Translate")
            translated_pages = self._translate_pages(pages_text, source_language, target_language, aws_region, excluded_list)
            
            # 步驟3: 創建翻譯PDF（保持原格式）
            logger.info("📝 Creating translated PDF with original format")
            success = self._create_overlay_pdf(pdf_source_path, pages_text, translated_pages, pdf_target_path)
            
            if not success:
                # 如果PDF覆蓋失敗，回退到文字文件
                logger.warning("📝 PDF overlay failed, creating text file as fallback")
                success = self._create_translation_text_file(pages_text, translated_pages, pdf_target_path)
            
            if not success:
                return self._create_error_result("Failed to create translation file")
            
            # 步驟4: 創建結果圖像
            result_image = self._create_result_image(pages_text, translated_pages)
            
            # 生成狀態報告
            if success and output_path.endswith('.pdf'):
                status_report = self._generate_status_report(len(pages_text), pdf_target_path, pages_text, translated_pages)
            else:
                txt_output_path = pdf_target_path.replace('.pdf', '_translation.txt')
                status_report = self._generate_status_report(len(pages_text), txt_output_path, pages_text, translated_pages)
            
            logger.info("✅ Translation completed successfully!")
            return (result_image, status_report)
            
        except Exception as e:
            logger.error(f"❌ Translation failed: {e}")
            return self._create_error_result(f"Translation failed: {str(e)}")
    
    def _ai_filter_content(self, text: str, aws_region: str) -> str:
        """使用AI智能過濾內容"""
        if not text or len(text.strip()) < 10:
            return text
        
        try:
            import boto3
            import json
            
            bedrock_client = boto3.client('bedrock-runtime', region_name=aws_region)
            
            # 構建AI分析prompt
            prompt = f"""請分析以下從PDF提取的文字，判斷哪些是簡報的核心內容，哪些是元數據（如版權信息、頁碼、頁眉頁腳等）。

只保留簡報的核心內容，移除以下類型的文字：
- 版權聲明和法律聲明
- 頁碼和頁面標記
- 頁眉和頁腳信息
- 公司標準免責聲明
- 文檔元數據

原始文字：
{text}

請只返回清理後的核心內容，不要添加任何解釋："""

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
        
        # 簡單的正則表達式過濾作為回退
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
    
    def _clean_and_filter_text(self, text: str, aws_region: str = None) -> str:
        """清理和過濾文字內容 - 使用AI智能分析"""
        if not text:
            return ""
        
        # 使用AI智能過濾
        if aws_region:
            return self._ai_filter_content(text, aws_region)
        else:
            return self._fallback_filter_content(text)
    
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
                        cleaned_text = self._clean_and_filter_text(text, aws_region)
                        if cleaned_text:  # 只添加有內容的頁面
                            pages_text.append(cleaned_text)
            
            logger.info(f"✅ AI extracted and filtered text from {len(pages_text)} pages")
            return pages_text
            
        except Exception as e:
            logger.error(f"❌ Failed to extract PDF text: {e}")
            return []
    
    def _translate_pages(self, pages_text: List[str], source_lang: str, 
                        target_lang: str, aws_region: str, excluded_words: List[str]) -> List[str]:
        """翻譯頁面文字"""
        try:
            translate_client = boto3.client('translate', region_name=aws_region)
            translated_pages = []
            
            for i, text in enumerate(pages_text):
                if not text.strip():
                    translated_pages.append("")
                    continue
                
                logger.info(f"  🔄 Translating page {i+1}")
                
                # 直接翻譯文字（不使用保護機制）
                translated_text = self._translate_text(text, source_lang, target_lang, translate_client)
                
                # 後處理：手動保護重要詞彙
                if excluded_words:
                    translated_text = self._post_process_translation(translated_text, excluded_words)
                
                translated_pages.append(translated_text)
                logger.info(f"    ✅ Page {i+1} translated")
            
            return translated_pages
            
        except Exception as e:
            logger.error(f"❌ Failed to translate pages: {e}")
            return pages_text  # 返回原文
    
    def _should_exclude_text(self, text: str, excluded_words: List[str]) -> bool:
        """檢查文字是否包含過多排除詞彙"""
        if not excluded_words or not text.strip():
            return False
        
        # 計算排除詞彙的密度
        text_lower = text.lower()
        total_words = len(text.split())
        excluded_count = 0
        
        for word in excluded_words:
            if word.lower() in text_lower:
                # 計算該詞彙出現次數
                excluded_count += text_lower.count(word.lower())
        
        # 如果排除詞彙佔比超過30%，才跳過翻譯
        if total_words > 0:
            exclusion_ratio = excluded_count / total_words
            return exclusion_ratio > 0.3
        
        return False
    
    def _post_process_translation(self, translated_text: str, excluded_words: List[str]) -> str:
        """後處理翻譯，恢復重要詞彙的英文形式"""
        if not excluded_words or not translated_text:
            return translated_text
        
        import re
        
        # 常見的翻譯對應，手動恢復
        replacements = {
            'AWS': ['AWS', 'aws', '亞馬遜網路服務', 'Amazon Web Services'],
            'Amazon': ['Amazon', 'amazon', '亞馬遜', '亞馬遜公司'],
            'ElastiCache': ['ElastiCache', 'elasticache', '彈性快取', '彈性緩存'],
            'Redis': ['Redis', 'redis'],
            'Valkey': ['Valkey', 'valkey'],
            'API': ['API', 'api', '應用程式介面'],
            'SDK': ['SDK', 'sdk', '軟體開發套件'],
            'JSON': ['JSON', 'json'],
            'HTTP': ['HTTP', 'http'],
            'URL': ['URL', 'url', '網址'],
            'PDF': ['PDF', 'pdf']
        }
        
        result = translated_text
        
        for original_word in excluded_words:
            if original_word in replacements:
                for variant in replacements[original_word]:
                    # 使用正則表達式進行替換，保持大小寫
                    pattern = re.escape(variant)
                    result = re.sub(pattern, original_word, result, flags=re.IGNORECASE)
        
        return result
    
    def _translate_text_with_protection(self, text: str, source_lang: str, target_lang: str, 
                                       translate_client, excluded_words: List[str]) -> str:
        """翻譯文字並保護排除詞彙"""
        try:
            if not excluded_words:
                return self._translate_text(text, source_lang, target_lang, translate_client)
            
            # 創建佔位符保護排除詞彙
            protected_text = text
            placeholders = {}
            
            for i, word in enumerate(excluded_words):
                if word.lower() in text.lower():
                    placeholder = f"__PROTECTED_{i}__"
                    placeholders[placeholder] = word
                    # 使用正則表達式進行大小寫不敏感的替換
                    import re
                    protected_text = re.sub(re.escape(word), placeholder, protected_text, flags=re.IGNORECASE)
            
            # 翻譯保護後的文字
            translated_text = self._translate_text(protected_text, source_lang, target_lang, translate_client)
            
            # 恢復排除詞彙
            for placeholder, original_word in placeholders.items():
                translated_text = translated_text.replace(placeholder, original_word)
            
            return translated_text
            
        except Exception as e:
            logger.error(f"❌ Protected translation failed: {e}")
            return text  # 返回原文
    
    def _translate_text(self, text: str, source_lang: str, target_lang: str, translate_client) -> str:
        """翻譯單個文字"""
        try:
            # 分段翻譯（避免文字太長）
            max_length = 4000
            if len(text) <= max_length:
                response = translate_client.translate_text(
                    Text=text,
                    SourceLanguageCode=source_lang,
                    TargetLanguageCode=target_lang
                )
                return response['TranslatedText']
            else:
                # 分段處理
                chunks = []
                words = text.split()
                current_chunk = ""
                
                for word in words:
                    if len(current_chunk + " " + word) <= max_length:
                        current_chunk = current_chunk + " " + word if current_chunk else word
                    else:
                        if current_chunk:
                            chunks.append(current_chunk)
                        current_chunk = word
                
                if current_chunk:
                    chunks.append(current_chunk)
                
                # 翻譯每個段落
                translated_chunks = []
                for chunk in chunks:
                    response = translate_client.translate_text(
                        Text=chunk,
                        SourceLanguageCode=source_lang,
                        TargetLanguageCode=target_lang
                    )
                    translated_chunks.append(response['TranslatedText'])
                
                return ' '.join(translated_chunks)
                
        except Exception as e:
            logger.error(f"❌ Translation failed: {e}")
            return text  # 返回原文
    
    def _create_overlay_pdf(self, original_pdf_path: str, original_pages: List[str], 
                           translated_pages: List[str], output_path: str) -> bool:
        """創建覆蓋翻譯的PDF"""
        try:
            from .pdf_overlay_writer import PDFOverlayWriter
            
            # 準備頁面數據
            pages_data = []
            for i, (original, translated) in enumerate(zip(original_pages, translated_pages)):
                page_data = {
                    'page_number': i + 1,
                    'original_text': original,
                    'translated_text': translated
                }
                pages_data.append(page_data)
            
            # 創建PDF覆蓋寫入器
            overlay_writer = PDFOverlayWriter()
            
            # 創建翻譯PDF
            success = overlay_writer.create_translated_pdf(
                original_pdf_path, pages_data, output_path
            )
            
            # 清理
            overlay_writer.cleanup()
            
            return success
            
        except Exception as e:
            logger.error(f"❌ PDF overlay creation failed: {e}")
            return False
    
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
                logger.info(f"📊 File size: {os.path.getsize(txt_output_path)} bytes")
                return True
            else:
                logger.error(f"❌ Text file not created properly")
                return False
            
        except Exception as e:
            logger.error(f"❌ Failed to create text file: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _create_translated_pdf(self, original_pages: List[str], translated_pages: List[str], output_path: str) -> bool:
        """創建翻譯PDF - 修復版本"""
        try:
            from reportlab.pdfgen import canvas
            from reportlab.lib.pagesizes import A4
            
            logger.info(f"📝 Creating PDF at: {output_path}")
            
            # 確保輸出目錄存在
            output_dir = os.path.dirname(output_path)
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
            
            c = canvas.Canvas(output_path, pagesize=A4)
            page_width, page_height = A4
            
            for i, (original, translated) in enumerate(zip(original_pages, translated_pages)):
                if i > 0:
                    c.showPage()
                
                logger.info(f"  📄 Creating page {i+1}")
                
                # 頁面標題
                c.setFont("Helvetica-Bold", 16)
                c.drawString(50, page_height - 50, f"Page {i+1} Translation")
                
                y_pos = page_height - 100
                
                # 原文區域
                c.setFont("Helvetica-Bold", 12)
                c.drawString(50, y_pos, "Original Text:")
                y_pos -= 25
                
                c.setFont("Helvetica", 9)
                if original:
                    # 更好的文字換行處理
                    original_lines = self._smart_wrap_text(original, 100)
                    for line in original_lines[:15]:  # 增加到15行
                        if line.strip():
                            # 清理特殊字符
                            clean_line = self._clean_text_for_pdf(line)
                            c.drawString(60, y_pos, clean_line)
                        y_pos -= 11
                else:
                    c.drawString(60, y_pos, "[No original text]")
                    y_pos -= 11
                
                y_pos -= 30
                
                # 翻譯區域
                c.setFont("Helvetica-Bold", 12)
                c.drawString(50, y_pos, "Chinese Translation:")
                y_pos -= 25
                
                c.setFont("Helvetica", 9)
                if translated:
                    # 處理翻譯文字
                    translated_lines = self._smart_wrap_text(translated, 80)
                    for line in translated_lines[:15]:  # 增加到15行
                        if line.strip():
                            # 清理和轉換中文字符
                            clean_line = self._clean_text_for_pdf(line)
                            try:
                                c.drawString(60, y_pos, clean_line)
                            except:
                                # 如果中文字符有問題，顯示提示
                                c.drawString(60, y_pos, "[Chinese text - view in text report]")
                        y_pos -= 11
                else:
                    c.drawString(60, y_pos, "[No translation]")
                
                # 添加分隔線
                if y_pos > 100:
                    c.line(50, y_pos - 20, page_width - 50, y_pos - 20)
            
            c.save()
            
            # 驗證文件創建
            if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                logger.info(f"✅ PDF created successfully: {output_path}")
                logger.info(f"📊 File size: {os.path.getsize(output_path)} bytes")
                return True
            else:
                logger.error(f"❌ PDF file not created properly")
                return False
            
        except Exception as e:
            logger.error(f"❌ Failed to create PDF: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _smart_wrap_text(self, text: str, max_length: int) -> List[str]:
        """智能文字換行"""
        if not text:
            return [""]
        
        # 先按句號、逗號等分割
        sentences = []
        current = ""
        
        for char in text:
            current += char
            if char in '.!?。！？' and len(current) > 20:
                sentences.append(current.strip())
                current = ""
        
        if current.strip():
            sentences.append(current.strip())
        
        # 再按長度換行
        lines = []
        for sentence in sentences:
            if len(sentence) <= max_length:
                lines.append(sentence)
            else:
                # 長句子按單詞分割
                words = sentence.split()
                current_line = ""
                
                for word in words:
                    if len(current_line + " " + word) <= max_length:
                        current_line = current_line + " " + word if current_line else word
                    else:
                        if current_line:
                            lines.append(current_line)
                        current_line = word
                
                if current_line:
                    lines.append(current_line)
        
        return lines if lines else [""]
    
    def _clean_text_for_pdf(self, text: str) -> str:
        """清理文字以適合PDF顯示"""
        if not text:
            return ""
        
        # 移除或替換問題字符
        cleaned = text.replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')
        
        # 壓縮多個空格
        import re
        cleaned = re.sub(r'\s+', ' ', cleaned)
        
        # 移除非打印字符，但保留中文
        result = ""
        for char in cleaned:
            # 保留ASCII可打印字符和中文字符
            if (32 <= ord(char) <= 126) or (0x4e00 <= ord(char) <= 0x9fff):
                result += char
            else:
                result += " "  # 替換為空格
        
        return result.strip()
    
    def _wrap_text(self, text: str, max_length: int) -> List[str]:
        """文字換行"""
        if not text:
            return [""]
        
        words = text.split()
        lines = []
        current_line = ""
        
        for word in words:
            if len(current_line + " " + word) <= max_length:
                current_line = current_line + " " + word if current_line else word
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word
        
        if current_line:
            lines.append(current_line)
        
        return lines if lines else [""]
    
    def _create_result_image(self, original_pages: List[str], translated_pages: List[str]) -> torch.Tensor:
        """創建結果圖像"""
        try:
            img = Image.new('RGB', (800, 600), 'white')
            draw = ImageDraw.Draw(img)
            
            try:
                font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 16)
            except:
                font = ImageFont.load_default()
            
            draw.text((20, 20), "AWS PDF Translation Complete", fill='black', font=font)
            draw.text((20, 60), f"Pages processed: {len(original_pages)}", fill='blue', font=font)
            draw.text((20, 100), f"Translation successful", fill='green', font=font)
            
            # 轉換為tensor
            img_array = np.array(img).astype(np.float32) / 255.0
            return torch.from_numpy(img_array).unsqueeze(0)
            
        except Exception as e:
            logger.error(f"❌ Failed to create result image: {e}")
            empty_img = np.ones((1, 400, 600, 3), dtype=np.float32)
            return torch.from_numpy(empty_img)
    
    def _generate_status_report(self, pages_count: int, output_path: str, 
                               original_pages: List[str] = None, translated_pages: List[str] = None) -> str:
        """生成詳細狀態報告"""
        report = f"""📊 AWS PDF Translation Report
========================================
✅ Status: Completed Successfully
📄 Pages processed: {pages_count}
📁 Output file: {os.path.basename(output_path)}
🌐 Service: Amazon Translate
========================================

📝 Translation Preview:
"""
        
        # 添加翻譯預覽
        if original_pages and translated_pages:
            for i, (original, translated) in enumerate(zip(original_pages[:3], translated_pages[:3])):  # 只顯示前3頁
                report += f"\n📄 Page {i+1}:\n"
                report += f"Original: {original[:150]}{'...' if len(original) > 150 else ''}\n"
                report += f"Translation: {translated[:150]}{'...' if len(translated) > 150 else ''}\n"
                report += "-" * 40 + "\n"
        
        report += f"\n✅ Complete translation saved to: {output_path}"
        return report
    
    def _create_error_result(self, error_message: str) -> Tuple[torch.Tensor, str]:
        """創建錯誤結果"""
        logger.error(f"❌ {error_message}")
        empty_image = np.zeros((1, 100, 100, 3), dtype=np.float32)
        return (torch.from_numpy(empty_image), f"❌ Error: {error_message}")
