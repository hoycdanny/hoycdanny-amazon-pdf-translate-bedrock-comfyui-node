# -*- coding: utf-8 -*-
"""
AWS PDF Translator - 單一簡潔版本
"""

from .aws_pdf_translator import AWSPDFTranslator

NODE_CLASS_MAPPINGS = {
    "AWSPDFTranslator": AWSPDFTranslator
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "AWSPDFTranslator": "AWS PDF Translator"
}

print("🎉 AWS PDF Translator loaded successfully!")
print("✨ Features: PDF翻譯 + 排除詞彙 + Amazon Translate")

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS"]
