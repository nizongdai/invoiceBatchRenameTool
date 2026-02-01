# 🧾 发票PDF整理工具

一个智能的发票PDF整理工具，可以自动识别发票内容并重命名文件。

## ✨ 功能特点

- 📁 **批量处理**：自动处理文件夹中的所有PDF发票
- 🔍 **智能识别**：自动区分文字PDF和扫描版PDF（图片）
- 📝 **OCR识别**：对扫描版发票使用OCR提取文字
- 🏷️ **自动重命名**：按照【日期-开票方-项目-发票号】规则重命名
- 💾 **安全备份**：处理前自动备份原文件
- 👁️ **预览模式**：可以先预览重命名结果，确认后再执行

## 🎯 命名规则

处理后文件名格式：
```
【日期-开票方名称-项目简述-发票号码】.pdf
```

示例：
```
【2024-01-15-京东-办公用品-12345678】.pdf
【2024-02-20-美团-餐饮费-87654321】.pdf
```

## 📦 安装要求

### 系统要求
- Python 3.7+
- macOS / Windows / Linux

### 依赖安装

```bash
# Python依赖
pip3 install PyMuPDF pdf2image pytesseract Pillow

# macOS: 安装Tesseract
brew install tesseract tesseract-lang

# Windows: 下载安装
# https://github.com/UB-Mannheim/tesseract/wiki

# Linux:
sudo apt install tesseract-ocr tesseract-ocr-chi-sim
```

或使用安装脚本：
```bash
chmod +x install.sh
./install.sh
```

## 🚀 使用方法

### 方式1：命令行启动
```bash
python3 invoice_organizer.py
```

### 方式2：双击运行
- macOS: 右键选择"打开"，或使用终端运行
- Windows: 双击运行（需安装Python）

### 使用步骤

1. **选择文件夹**：点击"选择文件夹"按钮，选择包含PDF发票的文件夹
2. **设置选项**：
   - ✅ 建议勾选"处理前备份原文件"
   - ✅ 首次使用建议勾选"预览重命名结果"
3. **开始处理**：点击"开始处理"按钮
4. **查看结果**：在日志区域查看处理详情

## 📝 识别信息

工具会自动提取以下发票信息：
- **日期**：开票日期（多种格式自动识别）
- **开票方**：销售方名称
- **项目**：发票项目类型（餐饮、住宿、办公用品等）
- **发票号码**：发票编号

## ⚠️ 注意事项

1. **OCR识别率**：扫描版发票的识别准确率取决于图片清晰度
2. **中文支持**：确保安装了中文语言包（tesseract-lang）
3. **文件备份**：建议始终开启备份功能，以防意外
4. **文件名冲突**：如果生成的新文件名已存在，会自动添加序号

## 🔧 故障排除

### 问题1：提示缺少依赖
```bash
pip3 install PyMuPDF pdf2image pytesseract Pillow
```

### 问题2：OCR识别中文失败
```bash
# macOS
brew install tesseract-lang

# 或手动下载中文训练数据
wget https://github.com/tesseract-ocr/tessdata/raw/main/chi_sim.traineddata
sudo mv chi_sim.traineddata /usr/local/share/tessdata/
```

### 问题3：pdf2image报错
确保已安装 poppler：
```bash
# macOS
brew install poppler

# Linux
sudo apt install poppler-utils
```

## 📄 文件说明

- `invoice_organizer.py` - 主程序
- `install.sh` - 安装脚本
- `README.md` - 使用说明

## 🐱 作者

懒懒 (lanlan) - 白白的私人助理

如有问题，请随时反馈！
