#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PDF文字替換功能演示
"""

import os
import sys
import logging
from pdf_text_replacer import PDFTextReplacer

# 設置日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_demo_pdf():
    """創建一個演示用的PDF文件"""
    try:
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter
        
        demo_pdf_path = "demo_input.pdf"
        
        # 創建PDF
        c = canvas.Canvas(demo_pdf_path, pagesize=letter)
        width, height = letter
        
        # 添加標題
        c.setFont("Helvetica-Bold", 20)
        c.drawString(100, height - 100, "AWS PDF Translation Demo")
        
        # 添加內容
        c.setFont("Helvetica", 12)
        y_position = height - 150
        
        demo_texts = [
            "Hello World! This is a test document.",
            "Amazon Web Services provides cloud computing services.",
            "Machine Learning is transforming industries.",
            "Artificial Intelligence enables smart applications.",
            "This document demonstrates PDF text replacement."
        ]
        
        for text in demo_texts:
            c.drawString(100, y_position, text)
            y_position -= 30
        
        c.save()
        logger.info(f"✅ 演示PDF已創建: {demo_pdf_path}")
        return demo_pdf_path
        
    except Exception as e:
        logger.error(f"❌ 創建演示PDF失敗: {e}")
        return None

def demo_pdf_replacement():
    """演示PDF文字替換功能"""
    
    print("🎬 PDF文字替換功能演示")
    print("=" * 50)
    
    # 步驟1: 創建演示PDF
    print("\n📄 步驟1: 創建演示PDF")
    demo_pdf_path = create_demo_pdf()
    if not demo_pdf_path:
        print("❌ 無法創建演示PDF")
        return False
    
    # 步驟2: 準備翻譯映射
    print("\n🌐 步驟2: 準備翻譯映射")
    translation_mapping = {
        "Hello World! This is a test document.": "你好世界！這是一個測試文檔。",
        "Amazon Web Services provides cloud computing services.": "亞馬遜網絡服務提供雲計算服務。",
        "Machine Learning is transforming industries.": "機器學習正在改變各個行業。",
        "Artificial Intelligence enables smart applications.": "人工智能使智能應用成為可能。",
        "This document demonstrates PDF text replacement.": "本文檔演示PDF文字替換功能。",
        "AWS PDF Translation Demo": "AWS PDF翻譯演示"
    }
    
    print(f"📝 準備了 {len(translation_mapping)} 個翻譯映射")
    
    # 步驟3: 執行PDF文字替換
    print("\n🔄 步驟3: 執行PDF文字替換")
    try:
        replacer = PDFTextReplacer()
        output_pdf_path = "demo_translated.pdf"
        
        result_path = replacer.replace_pdf_text(
            demo_pdf_path,
            translation_mapping,
            output_pdf_path
        )
        
        if os.path.exists(result_path):
            print(f"✅ 翻譯PDF創建成功: {result_path}")
            print(f"📁 文件大小: {os.path.getsize(result_path)} bytes")
            return True
        else:
            print("❌ 翻譯PDF創建失敗")
            return False
            
    except Exception as e:
        print(f"❌ PDF替換過程出錯: {e}")
        return False

def demo_text_extraction():
    """演示文字位置提取功能"""
    
    print("\n🔍 額外演示: 文字位置提取")
    print("-" * 30)
    
    demo_pdf_path = "demo_input.pdf"
    if not os.path.exists(demo_pdf_path):
        print("⚠️ 演示PDF不存在，跳過文字提取演示")
        return
    
    try:
        replacer = PDFTextReplacer()
        text_positions = replacer.extract_text_positions(demo_pdf_path)
        
        print(f"📊 提取到 {len(text_positions)} 個文字元素")
        
        # 顯示前3個文字元素的詳細信息
        for i, pos in enumerate(text_positions[:3]):
            print(f"\n文字元素 {i+1}:")
            print(f"  內容: '{pos['text']}'")
            print(f"  位置: {pos['bbox']}")
            print(f"  字體: {pos['font']}")
            print(f"  大小: {pos['size']}")
        
    except Exception as e:
        print(f"❌ 文字提取演示失敗: {e}")

if __name__ == "__main__":
    try:
        # 主演示
        success = demo_pdf_replacement()
        
        # 額外演示
        demo_text_extraction()
        
        # 總結
        print("\n" + "=" * 50)
        if success:
            print("🎉 演示完成！PDF文字替換功能正常工作")
            print("\n📋 生成的文件:")
            print("  • demo_input.pdf - 原始演示PDF")
            print("  • demo_translated.pdf - 翻譯後的PDF")
        else:
            print("⚠️ 演示過程中遇到問題，請檢查日誌")
            
    except KeyboardInterrupt:
        print("\n\n⏹️ 演示被用戶中斷")
    except Exception as e:
        print(f"\n❌ 演示過程中發生錯誤: {e}")
        import traceback
        traceback.print_exc()
