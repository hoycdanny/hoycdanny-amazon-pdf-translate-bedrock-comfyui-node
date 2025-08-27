# -*- coding: utf-8 -*-
"""
PDF覆蓋寫入器 - 使用reportlab將翻譯覆蓋到原PDF上
"""

import os
import logging
from typing import List, Dict, Any
import tempfile

logger = logging.getLogger(__name__)

class PDFOverlayWriter:
    """PDF覆蓋寫入器 - 保持原格式並添加翻譯"""
    
    def __init__(self):
        self.temp_dir = tempfile.mkdtemp()
        logger.info("✅ PDF Overlay Writer initialized")
    
    def create_translated_pdf(self, original_pdf_path: str, pages_data: List[Dict], 
                            output_path: str) -> bool:
        """
        創建翻譯PDF - 在原PDF上覆蓋翻譯文字
        """
        try:
            from reportlab.pdfgen import canvas
            from reportlab.lib.pagesizes import letter, A4
            from reportlab.pdfbase import pdfmetrics
            from reportlab.pdfbase.ttfonts import TTFont
            from pypdf import PdfReader, PdfWriter
            import io
            
            logger.info(f"📝 Creating translated PDF overlay")
            logger.info(f"📄 Original: {original_pdf_path}")
            logger.info(f"📄 Output: {output_path}")
            
            # 讀取原PDF
            reader = PdfReader(original_pdf_path)
            writer = PdfWriter()
            
            # 註冊中文字體
            chinese_font = self._register_chinese_font()
            
            for page_num, page_data in enumerate(pages_data):
                if page_num >= len(reader.pages):
                    break
                
                logger.info(f"  📄 Processing page {page_num + 1}")
                
                # 獲取原頁面
                original_page = reader.pages[page_num]
                
                # 創建翻譯覆蓋層
                overlay_buffer = self._create_translation_overlay(
                    page_data, original_page, chinese_font
                )
                
                if overlay_buffer:
                    # 讀取覆蓋層
                    overlay_reader = PdfReader(overlay_buffer)
                    overlay_page = overlay_reader.pages[0]
                    
                    # 合併原頁面和覆蓋層
                    original_page.merge_page(overlay_page)
                
                writer.add_page(original_page)
            
            # 寫入最終PDF
            with open(output_path, 'wb') as output_file:
                writer.write(output_file)
            
            logger.info(f"✅ Translated PDF created: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to create translated PDF: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _register_chinese_font(self) -> str:
        """註冊中文字體"""
        try:
            from reportlab.pdfbase import pdfmetrics
            from reportlab.pdfbase.ttfonts import TTFont
            
            # 嘗試系統中文字體
            font_paths = [
                "/System/Library/Fonts/PingFang.ttc",
                "/System/Library/Fonts/Helvetica.ttc",
                "/Library/Fonts/Arial Unicode MS.ttf",
                "/System/Library/Fonts/STHeiti Light.ttc"
            ]
            
            for font_path in font_paths:
                if os.path.exists(font_path):
                    try:
                        pdfmetrics.registerFont(TTFont('ChineseFont', font_path))
                        logger.info(f"✅ Registered Chinese font: {font_path}")
                        return 'ChineseFont'
                    except Exception as e:
                        logger.debug(f"Failed to register {font_path}: {e}")
                        continue
            
            logger.warning("⚠️ No Chinese font found, using Helvetica")
            return 'Helvetica'
            
        except Exception as e:
            logger.error(f"❌ Font registration failed: {e}")
            return 'Helvetica'
    
    def _create_translation_overlay(self, page_data: Dict, original_page, font_name: str):
        """創建翻譯覆蓋層"""
        try:
            from reportlab.pdfgen import canvas
            from reportlab.lib.colors import Color
            import io
            
            # 獲取頁面尺寸
            page_width = float(original_page.mediabox.width)
            page_height = float(original_page.mediabox.height)
            
            # 創建內存中的PDF
            buffer = io.BytesIO()
            c = canvas.Canvas(buffer, pagesize=(page_width, page_height))
            
            # 獲取翻譯文字
            translated_text = page_data.get('translated_text', '')
            
            if translated_text:
                # 設置半透明背景
                c.setFillColor(Color(1, 1, 1, alpha=0.85))  # 白色半透明背景
                
                # 計算文字區域（頁面下方1/3）
                text_area_height = page_height / 3
                text_y_start = text_area_height
                
                # 繪製背景矩形
                c.rect(20, 20, page_width - 40, text_area_height - 40, fill=1, stroke=0)
                
                # 設置文字
                c.setFillColor(Color(0, 0, 0, alpha=1))  # 黑色文字
                
                try:
                    c.setFont(font_name, 10)
                except:
                    c.setFont('Helvetica', 10)
                
                # 添加標題
                c.drawString(30, text_area_height - 30, "🌐 Chinese Translation:")
                
                # 分行顯示翻譯文字
                lines = self._wrap_text_for_pdf(translated_text, 80)
                y_pos = text_area_height - 50
                
                for line in lines[:15]:  # 最多15行
                    if y_pos > 30:
                        try:
                            c.drawString(30, y_pos, line)
                        except:
                            # 如果中文字符有問題，顯示提示
                            c.drawString(30, y_pos, "[Chinese text - see text output]")
                        y_pos -= 12
                    else:
                        break
            
            c.save()
            buffer.seek(0)
            return buffer
            
        except Exception as e:
            logger.error(f"❌ Failed to create overlay: {e}")
            return None
    
    def _wrap_text_for_pdf(self, text: str, max_chars: int) -> List[str]:
        """為PDF顯示包裝文字"""
        if not text:
            return [""]
        
        # 按句子分割
        sentences = []
        current = ""
        
        for char in text:
            current += char
            if char in '。！？.!?' and len(current) > 10:
                sentences.append(current.strip())
                current = ""
        
        if current.strip():
            sentences.append(current.strip())
        
        # 按長度分行
        lines = []
        for sentence in sentences:
            if len(sentence) <= max_chars:
                lines.append(sentence)
            else:
                # 長句子分割
                words = sentence.split()
                current_line = ""
                
                for word in words:
                    if len(current_line + " " + word) <= max_chars:
                        current_line = current_line + " " + word if current_line else word
                    else:
                        if current_line:
                            lines.append(current_line)
                        current_line = word
                
                if current_line:
                    lines.append(current_line)
        
        return lines if lines else [""]
    
    def cleanup(self):
        """清理臨時文件"""
        try:
            import shutil
            shutil.rmtree(self.temp_dir, ignore_errors=True)
            logger.info("🧹 Temporary files cleaned up")
        except Exception as e:
            logger.warning(f"⚠️ Failed to cleanup temp files: {e}")
