#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
分析PDF第一頁內容
"""

import sys
import os

def analyze_pdf_first_page(pdf_path):
    """分析PDF第一頁的內容"""
    
    print(f"🔍 Analyzing PDF: {pdf_path}")
    
    try:
        import pdfplumber
        import fitz  # PyMuPDF
        
        # 方法1: 使用 pdfplumber 提取文字
        print("\n📄 Method 1: PDFPlumber text extraction")
        with pdfplumber.open(pdf_path) as pdf:
            if len(pdf.pages) > 0:
                page = pdf.pages[0]
                text = page.extract_text()
                
                print(f"Text length: {len(text) if text else 0} characters")
                print(f"Text content: '{text}'" if text else "No text found")
                
                # 分析文字特徵
                if text:
                    words = text.strip().split()
                    lines = [line for line in text.split('\n') if line.strip()]
                    print(f"Word count: {len(words)}")
                    print(f"Line count: {len(lines)}")
                    print(f"Lines: {lines}")
        
        # 方法2: 使用 PyMuPDF 檢查圖片
        print("\n🖼️ Method 2: PyMuPDF image analysis")
        pdf_doc = fitz.open(pdf_path)
        if len(pdf_doc) > 0:
            page = pdf_doc[0]
            
            # 檢查圖片
            image_list = page.get_images()
            print(f"Images found: {len(image_list)}")
            
            # 檢查頁面尺寸
            rect = page.rect
            print(f"Page size: {rect.width} x {rect.height}")
            
            # 嘗試OCR
            print("\n🔍 Method 3: OCR test")
            try:
                pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
                img_data = pix.tobytes("png")
                print(f"Generated image data: {len(img_data)} bytes")
                
                # 嘗試本地OCR
                try:
                    import pytesseract
                    from PIL import Image
                    import io
                    
                    img = Image.open(io.BytesIO(img_data))
                    custom_config = r'--oem 3 --psm 6 -l eng+chi_tra+chi_sim'
                    ocr_text = pytesseract.image_to_string(img, config=custom_config)
                    
                    print(f"OCR result length: {len(ocr_text)} characters")
                    print(f"OCR content: '{ocr_text.strip()}'")
                    
                except Exception as e:
                    print(f"Local OCR failed: {e}")
                    
            except Exception as e:
                print(f"Image extraction failed: {e}")
        
        pdf_doc.close()
        
    except Exception as e:
        print(f"❌ Analysis failed: {e}")

if __name__ == "__main__":
    pdf_path = "/Users/dayho/Desktop/IGS_vlakey.pdf"
    analyze_pdf_first_page(pdf_path)
