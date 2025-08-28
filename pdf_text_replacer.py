# -*- coding: utf-8 -*-
"""
PDF文字替換模塊
將翻譯後的文字精確替換到原PDF的相對位置
"""

import fitz  # PyMuPDF
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os
import logging

logger = logging.getLogger(__name__)

class PDFTextReplacer:
    """PDF文字替換器"""
    
    def __init__(self):
        self.setup_fonts()
    
    def setup_fonts(self):
        """設置中文字體"""
        try:
            # 嘗試註冊系統中文字體
            font_paths = [
                "/System/Library/Fonts/PingFang.ttc",  # macOS
                "/System/Library/Fonts/Arial Unicode MS.ttf",  # macOS
                "C:/Windows/Fonts/msyh.ttc",  # Windows 微軟雅黑
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"  # Linux
            ]
            
            for font_path in font_paths:
                if os.path.exists(font_path):
                    pdfmetrics.registerFont(TTFont('ChineseFont', font_path))
                    logger.info(f"已註冊字體: {font_path}")
                    break
            else:
                logger.warning("未找到中文字體，將使用默認字體")
        except Exception as e:
            logger.warning(f"字體設置失敗: {e}")
    
    def extract_text_positions(self, pdf_path):
        """提取PDF中文字的精確位置信息"""
        doc = fitz.open(pdf_path)
        text_positions = []
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            text_dict = page.get_text("dict")
            
            for block in text_dict["blocks"]:
                if "lines" in block:
                    for line in block["lines"]:
                        for span in line["spans"]:
                            text_positions.append({
                                "page": page_num,
                                "text": span["text"],
                                "bbox": span["bbox"],  # (x0, y0, x1, y1)
                                "font": span["font"],
                                "size": span["size"],
                                "flags": span["flags"]
                            })
        
        doc.close()
        return text_positions
    
    def create_translated_pdf(self, original_pdf_path, translations, output_path):
        """創建包含翻譯文字的新PDF"""
        # 提取原PDF的文字位置
        text_positions = self.extract_text_positions(original_pdf_path)
        
        # 打開原PDF獲取頁面信息
        original_doc = fitz.open(original_pdf_path)
        
        # 創建新PDF
        new_doc = fitz.open()
        
        for page_num in range(len(original_doc)):
            original_page = original_doc[page_num]
            page_rect = original_page.rect
            
            # 創建新頁面
            new_page = new_doc.new_page(width=page_rect.width, height=page_rect.height)
            
            # 複製原頁面的圖像內容（去除文字）
            self._copy_page_without_text(original_page, new_page)
            
            # 添加翻譯後的文字
            self._add_translated_text(new_page, text_positions, translations, page_num)
        
        # 保存新PDF
        new_doc.save(output_path)
        new_doc.close()
        original_doc.close()
        
        logger.info(f"翻譯PDF已保存到: {output_path}")
        return output_path
    
    def _copy_page_without_text(self, source_page, target_page):
        """複製頁面內容但不包含文字"""
        # 獲取頁面的圖像和圖形內容
        pix = source_page.get_pixmap(alpha=False)
        
        # 創建一個遮罩來隱藏文字區域
        text_dict = source_page.get_text("dict")
        
        # 將圖像插入到新頁面
        img_rect = fitz.Rect(0, 0, pix.width, pix.height)
        target_page.insert_image(img_rect, pixmap=pix)
    
    def _add_translated_text(self, page, text_positions, translations, page_num):
        """在指定位置添加翻譯文字"""
        page_texts = [pos for pos in text_positions if pos["page"] == page_num]
        
        for text_pos in page_texts:
            original_text = text_pos["text"].strip()
            if not original_text:
                continue
            
            # 查找對應的翻譯
            translated_text = self._find_translation(original_text, translations)
            if not translated_text:
                translated_text = original_text  # 如果沒有翻譯，保持原文
            
            # 計算文字位置和大小
            bbox = text_pos["bbox"]
            font_size = max(8, min(text_pos["size"], 20))  # 限制字體大小範圍
            
            # 插入翻譯文字
            try:
                page.insert_text(
                    (bbox[0], bbox[1] + font_size),  # 位置調整
                    translated_text,
                    fontsize=font_size,
                    color=(0, 0, 0),  # 黑色
                    fontname="helv"  # 使用Helvetica字體
                )
            except Exception as e:
                logger.warning(f"插入文字失敗: {e}, 文字: {translated_text}")
    
    def _find_translation(self, original_text, translations):
        """查找原文對應的翻譯"""
        # 精確匹配
        if original_text in translations:
            return translations[original_text]
        
        # 模糊匹配（去除空格和標點）
        cleaned_original = ''.join(c for c in original_text if c.isalnum())
        for orig, trans in translations.items():
            cleaned_key = ''.join(c for c in orig if c.isalnum())
            if cleaned_original == cleaned_key:
                return trans
        
        return None
    
    def replace_pdf_text(self, pdf_path, translation_mapping, output_path):
        """主要接口：替換PDF中的文字"""
        try:
            return self.create_translated_pdf(pdf_path, translation_mapping, output_path)
        except Exception as e:
            logger.error(f"PDF文字替換失敗: {e}")
            raise
