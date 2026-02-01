#!/bin/bash
# 发票整理工具安装脚本

echo "🧾 发票PDF整理工具 - 安装脚本"
echo "================================"
echo ""

# 检查Python
if ! command -v python3 &> /dev/null; then
    echo "❌ 未找到 Python3，请先安装 Python3"
    exit 1
fi

echo "✅ 找到 Python3"

# 检查pip
if ! command -v pip3 &> /dev/null; then
    echo "❌ 未找到 pip3，请先安装 pip"
    exit 1
fi

echo "✅ 找到 pip3"

# 安装Python依赖
echo ""
echo "📦 安装Python依赖..."
pip3 install PyMuPDF pdf2image pytesseract Pillow -q

if [ $? -eq 0 ]; then
    echo "✅ Python依赖安装成功"
else
    echo "⚠️ Python依赖安装可能有问题，请手动运行:"
    echo "pip3 install PyMuPDF pdf2image pytesseract Pillow"
fi

# 检测操作系统并安装Tesseract
echo ""
echo "🔧 检查Tesseract-OCR..."

if command -v tesseract &> /dev/null; then
    echo "✅ Tesseract已安装"
else
    echo "❌ Tesseract未安装"
    echo ""
    
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        echo "检测到macOS系统，建议安装Tesseract:"
        echo "brew install tesseract tesseract-lang"
        echo ""
        read -p "是否自动安装？(y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            if command -v brew &> /dev/null; then
                brew install tesseract tesseract-lang
            else
                echo "❌ 未找到Homebrew，请先安装: https://brew.sh"
            fi
        fi
        
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux
        echo "检测到Linux系统，建议安装Tesseract:"
        echo "sudo apt update && sudo apt install tesseract-ocr tesseract-ocr-chi-sim"
        
    elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]]; then
        # Windows
        echo "检测到Windows系统，请下载安装:"
        echo "https://github.com/UB-Mannheim/tesseract/wiki"
        
    fi
fi

echo ""
echo "================================"
echo "安装完成！"
echo ""
echo "使用方法:"
echo "python3 invoice_organizer.py"
echo ""
echo "或者双击运行（macOS/Windows）"
echo ""
