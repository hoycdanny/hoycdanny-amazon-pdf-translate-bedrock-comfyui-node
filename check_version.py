#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
檢查當前代碼版本
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def check_code_version():
    """檢查代碼是否包含最新的OCR功能"""
    
    print("🔍 Checking current code version...")
    
    try:
        # 讀取代碼文件
        with open('aws_pdf_translator.py', 'r', encoding='utf-8') as f:
            code = f.read()
        
        # 檢查關鍵功能
        checks = [
            ("OCR trigger logic", "needs_ocr = False"),
            ("OCR reason tracking", "ocr_reason = \"\""),
            ("Detailed logging", "📊 Page {i+1} text analysis:"),
            ("AWS Textract method", "_aws_textract_ocr"),
            ("Local Tesseract method", "_local_tesseract_ocr"),
            ("PyMuPDF import", "import fitz"),
        ]
        
        print("\n📋 Feature check:")
        all_good = True
        
        for feature, pattern in checks:
            if pattern in code:
                print(f"✅ {feature}")
            else:
                print(f"❌ {feature} - MISSING")
                all_good = False
        
        # 檢查觸發條件
        if "len(text.strip()) < 100" in code:
            print("✅ OCR trigger condition updated")
        else:
            print("❌ OCR trigger condition not updated")
            all_good = False
            
        print(f"\n{'✅ Code is up to date!' if all_good else '❌ Code needs updating!'}")
        
        # 檢查是否可以導入
        try:
            from aws_pdf_translator import AWSPDFTranslator
            translator = AWSPDFTranslator()
            
            if hasattr(translator, '_extract_text_from_images'):
                print("✅ OCR methods are available in loaded class")
            else:
                print("❌ OCR methods not found in loaded class")
                print("⚠️  You may need to restart ComfyUI to load the updated code!")
                
        except Exception as e:
            print(f"❌ Failed to import translator: {e}")
            
    except Exception as e:
        print(f"❌ Failed to read code file: {e}")

if __name__ == "__main__":
    check_code_version()
