#!/usr/bin/env python3
"""
发票PDF整理工具
功能：
1. 选择文件夹
2. 提取PDF文字（文字PDF直接提取，图片PDF用OCR）
3. 解析中国发票信息（开票方、项目、发票号）
4. 按规则重命名：【日期-开票方-项目简述-发票号码】

作者：懒懒 (lanlan)
"""

import os
import re
import sys
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from datetime import datetime
from pathlib import Path

# PDF处理库
try:
    import fitz  # PyMuPDF
    from pdf2image import convert_from_path
    import pytesseract
    from PIL import Image
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False
    print("正在安装必要的依赖...")

class InvoiceProcessor:
    def __init__(self, root):
        self.root = root
        self.root.title("发票PDF整理工具 🧾")
        self.root.geometry("700x500")
        self.root.resizable(True, True)
        
        # 设置样式
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        self.create_ui()
        self.setup_logging()
        
    def create_ui(self):
        """创建用户界面"""
        # 标题
        title = tk.Label(self.root, text="发票PDF整理工具", font=("Helvetica", 20, "bold"))
        title.pack(pady=10)
        
        subtitle = tk.Label(self.root, text="自动识别发票内容并重命名文件", font=("Helvetica", 11))
        subtitle.pack()
        
        # 文件夹选择区域
        folder_frame = tk.Frame(self.root)
        folder_frame.pack(fill=tk.X, padx=20, pady=15)
        
        self.folder_path = tk.StringVar()
        self.folder_entry = tk.Entry(folder_frame, textvariable=self.folder_path, font=("Helvetica", 11))
        self.folder_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        
        browse_btn = tk.Button(folder_frame, text="选择文件夹", command=self.browse_folder, 
                               font=("Helvetica", 11), bg="#4CAF50", fg="white", padx=15)
        browse_btn.pack(side=tk.RIGHT)
        
        # 选项区域
        options_frame = tk.LabelFrame(self.root, text="处理选项", font=("Helvetica", 11), padx=10, pady=10)
        options_frame.pack(fill=tk.X, padx=20, pady=10)
        
        self.backup_var = tk.BooleanVar(value=True)
        backup_cb = tk.Checkbutton(options_frame, text="处理前备份原文件", variable=self.backup_var,
                                   font=("Helvetica", 10))
        backup_cb.pack(anchor=tk.W)
        
        self.preview_var = tk.BooleanVar(value=True)
        preview_cb = tk.Checkbutton(options_frame, text="预览重命名结果（不实际执行）", variable=self.preview_var,
                                    font=("Helvetica", 10))
        preview_cb.pack(anchor=tk.W)
        
        # 进度区域
        progress_frame = tk.LabelFrame(self.root, text="处理进度", font=("Helvetica", 11), padx=10, pady=10)
        progress_frame.pack(fill=tk.X, padx=20, pady=10)
        
        self.progress = ttk.Progressbar(progress_frame, orient=tk.HORIZONTAL, length=600, mode='determinate')
        self.progress.pack(fill=tk.X, pady=5)
        
        self.status_label = tk.Label(progress_frame, text="就绪", font=("Helvetica", 10))
        self.status_label.pack()
        
        # 日志区域
        log_frame = tk.LabelFrame(self.root, text="处理日志", font=("Helvetica", 11))
        log_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        scrollbar = tk.Scrollbar(log_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.log_text = tk.Text(log_frame, height=8, font=("Consolas", 9), 
                                yscrollcommand=scrollbar.set)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.log_text.yview)
        
        # 按钮区域
        btn_frame = tk.Frame(self.root)
        btn_frame.pack(fill=tk.X, padx=20, pady=15)
        
        self.process_btn = tk.Button(btn_frame, text="开始处理", command=self.process_invoices,
                                     font=("Helvetica", 12, "bold"), bg="#2196F3", fg="white",
                                     padx=30, pady=8)
        self.process_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        clear_btn = tk.Button(btn_frame, text="清空日志", command=self.clear_log,
                              font=("Helvetica", 11), padx=20)
        clear_btn.pack(side=tk.LEFT)
        
        exit_btn = tk.Button(btn_frame, text="退出", command=self.root.quit,
                             font=("Helvetica", 11), padx=20)
        exit_btn.pack(side=tk.RIGHT)
    
    def setup_logging(self):
        """设置日志"""
        self.log("发票PDF整理工具已启动")
        self.log("请选择一个包含PDF发票的文件夹")
        self.check_dependencies()
    
    def check_dependencies(self):
        """检查依赖是否安装"""
        missing = []
        try:
            import fitz
        except ImportError:
            missing.append("PyMuPDF")
        try:
            from pdf2image import convert_from_path
        except ImportError:
            missing.append("pdf2image")
        try:
            import pytesseract
        except ImportError:
            missing.append("pytesseract")
        try:
            from PIL import Image
        except ImportError:
            missing.append("Pillow")
            
        if missing:
            self.log(f"⚠️ 缺少依赖: {', '.join(missing)}")
            self.log("请运行: pip install " + " ".join(missing))
            self.process_btn.config(state=tk.DISABLED)
    
    def log(self, message):
        """添加日志"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        self.root.update()
    
    def clear_log(self):
        """清空日志"""
        self.log_text.delete(1.0, tk.END)
        self.log("日志已清空")
    
    def browse_folder(self):
        """选择文件夹"""
        folder = filedialog.askdirectory(title="选择包含PDF发票的文件夹")
        if folder:
            self.folder_path.set(folder)
            self.log(f"已选择文件夹: {folder}")
            
            # 统计PDF文件数量
            pdf_files = list(Path(folder).glob("*.pdf"))
            self.log(f"找到 {len(pdf_files)} 个PDF文件")
    
    def extract_text_from_pdf(self, pdf_path):
        """从PDF提取文字"""
        import fitz
        
        text = ""
        try:
            doc = fitz.open(pdf_path)
            for page in doc:
                text += page.get_text()
            doc.close()
        except Exception as e:
            self.log(f"  提取文字失败: {e}")
        
        return text
    
    def ocr_pdf(self, pdf_path):
        """OCR识别PDF图片"""
        from pdf2image import convert_from_path
        import pytesseract
        
        text = ""
        try:
            # 将PDF转换为图片
            images = convert_from_path(pdf_path, dpi=300, first_page=1, last_page=1)
            
            # OCR识别（中文+英文）
            for img in images:
                # 提高图片对比度
                img = img.convert('L')  # 转为灰度
                text += pytesseract.image_to_string(img, lang='chi_sim+eng')
                
        except Exception as e:
            self.log(f"  OCR识别失败: {e}")
        
        return text
    
    def is_scanned_pdf(self, pdf_path):
        """判断是否是扫描版PDF（图片为主）"""
        import fitz
        
        try:
            doc = fitz.open(pdf_path)
            page = doc[0]
            
            # 检查是否有图片
            images = page.get_images()
            text = page.get_text().strip()
            
            doc.close()
            
            # 如果图片多且文字少，认为是扫描版
            return len(images) > 0 and len(text) < 100
            
        except Exception as e:
            return False
    
    def parse_invoice_info(self, text):
        """解析发票信息"""
        info = {
            'date': '',
            'seller': '',  # 开票方/销售方
            'project': '',  # 项目简述
            'invoice_no': ''  # 发票号码
        }
        
        # 提取日期（多种格式）
        date_patterns = [
            r'(\d{4}[年/-]\d{1,2}[月/-]\d{1,2}[日]?)',
            r'(\d{4}\d{2}\d{2})',
            r'开票日期[：:]\s*(\d{4}[年/-]\d{1,2}[月/-]\d{1,2})',
        ]
        for pattern in date_patterns:
            match = re.search(pattern, text)
            if match:
                date_str = match.group(1)
                # 统一格式为 YYYY-MM-DD
                date_str = re.sub(r'[年月/]', '-', date_str)
                date_str = date_str.replace('日', '').replace('-', '')
                if len(date_str) == 8:
                    info['date'] = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:]}"
                else:
                    info['date'] = date_str[:10]
                break
        
        # 如果没有找到日期，使用文件日期
        if not info['date']:
            info['date'] = datetime.now().strftime("%Y-%m-%d")
        
        # 提取开票方/销售方名称
        seller_patterns = [
            r'销售方.*名[称|稱][：:]\s*([\u4e00-\u9fa5a-zA-Z0-9]+)',
            r'名[称|稱][：:]\s*([\u4e00-\u9fa5]+(?:公司|商店|超市|餐饮|酒店|科技))',
            r'开票方[：:]\s*([\u4e00-\u9fa5]+)',
            r'([\u4e00-\u9fa5]+(?:有限公司|有限责任公司|股份有限公司))',
        ]
        for pattern in seller_patterns:
            match = re.search(pattern, text)
            if match:
                info['seller'] = match.group(1).strip()
                break
        
        # 提取发票号码
        invoice_patterns = [
            r'发票号码[：:]\s*(\d{10,20})',
            r'发票代码.*号码[：:]\s*(\d+)',
            r'No[.:]?\s*(\d{8,20})',
            r'(\d{8,20})',  # 假设最长的数字是发票号
        ]
        for pattern in invoice_patterns:
            match = re.search(pattern, text)
            if match:
                info['invoice_no'] = match.group(1).strip()
                break
        
        # 提取项目名称（通常是发票明细中的商品名称）
        project_patterns = [
            r'[货物|服务|项目名称][名称]*[：:]\s*([\u4e00-\u9fa5]+)',
            r'商品名称[：:]\s*([\u4e00-\u9fa5]+)',
            r'(?:餐饮|住宿|交通|办公|材料|设备|服务|咨询|维修|租赁)',
        ]
        for pattern in project_patterns:
            match = re.search(pattern, text)
            if match:
                info['project'] = match.group(0).strip()
                if len(info['project']) > 8:
                    info['project'] = info['project'][:8]
                break
        
        # 如果项目为空，尝试从全文找关键词
        if not info['project']:
            keywords = ['餐饮', '住宿', '交通', '办公', '材料', '设备', '服务', 
                       '咨询', '维修', '租赁', '会议', '培训', '采购', '电费', '水费']
            for kw in keywords:
                if kw in text:
                    info['project'] = kw
                    break
        
        return info
    
    def generate_new_filename(self, info, original_path):
        """生成新文件名"""
        # 清理字段
        seller = info['seller'] or '未知开票方'
        project = info['project'] or '其他'
        invoice_no = info['invoice_no'] or '00000000'
        
        # 开票方名称简化（取前10个字）
        if len(seller) > 10:
            seller = seller[:10]
        
        # 项目简述限制8个字
        if len(project) > 8:
            project = project[:8]
        
        # 发票号取后8位
        if len(invoice_no) > 8:
            invoice_no = invoice_no[-8:]
        
        # 生成文件名：【日期-开票方-项目-发票号】
        new_name = f"【{info['date']}-{seller}-{project}-{invoice_no}】.pdf"
        
        # 清理非法字符
        new_name = re.sub(r'[\\/:*?"<>|]', '', new_name)
        
        return new_name
    
    def process_invoices(self):
        """处理发票"""
        folder = self.folder_path.get()
        if not folder:
            messagebox.showwarning("警告", "请先选择文件夹！")
            return
        
        folder_path = Path(folder)
        pdf_files = list(folder_path.glob("*.pdf"))
        
        if not pdf_files:
            messagebox.showinfo("提示", "文件夹中没有PDF文件")
            return
        
        # 检查是否预览模式
        preview_mode = self.preview_var.get()
        
        if preview_mode:
            self.log("="*50)
            self.log("【预览模式】将显示重命名结果但不实际执行")
            self.log("="*50)
        else:
            # 备份
            if self.backup_var.get():
                backup_folder = folder_path / f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                backup_folder.mkdir(exist_ok=True)
                self.log(f"创建备份文件夹: {backup_folder}")
        
        # 处理文件
        total = len(pdf_files)
        processed = 0
        renamed = 0
        errors = 0
        
        for i, pdf_file in enumerate(pdf_files, 1):
            self.progress['value'] = (i / total) * 100
            self.status_label.config(text=f"处理中... {i}/{total}")
            self.root.update()
            
            self.log(f"\n[{i}/{total}] 处理: {pdf_file.name}")
            
            try:
                # 判断PDF类型
                is_scanned = self.is_scanned_pdf(pdf_file)
                
                if is_scanned:
                    self.log("  检测到扫描版PDF，使用OCR识别...")
                    text = self.ocr_pdf(pdf_file)
                else:
                    self.log("  检测到文字PDF，直接提取...")
                    text = self.extract_text_from_pdf(pdf_file)
                
                # 提取前500字符用于调试
                text_preview = text[:500].replace('\n', ' ')
                self.log(f"  提取内容预览: {text_preview[:100]}...")
                
                # 解析发票信息
                info = self.parse_invoice_info(text)
                self.log(f"  解析结果: 日期={info['date']}, 开票方={info['seller']}, 项目={info['project']}, 票号={info['invoice_no']}")
                
                # 生成新文件名
                new_filename = self.generate_new_filename(info, pdf_file)
                new_path = folder_path / new_filename
                
                # 检查文件名冲突
                counter = 1
                original_new_path = new_path
                while new_path.exists() and new_path != pdf_file:
                    stem = original_new_path.stem
                    new_path = folder_path / f"{stem}_{counter}.pdf"
                    counter += 1
                
                self.log(f"  新文件名: {new_filename}")
                
                if not preview_mode:
                    # 备份原文件
                    if self.backup_var.get():
                        import shutil
                        shutil.copy2(pdf_file, backup_folder / pdf_file.name)
                    
                    # 重命名
                    pdf_file.rename(new_path)
                    self.log(f"  ✅ 重命名成功")
                    renamed += 1
                else:
                    self.log(f"  [预览] 将重命名为: {new_filename}")
                
                processed += 1
                
            except Exception as e:
                self.log(f"  ❌ 处理失败: {e}")
                errors += 1
        
        # 完成
        self.progress['value'] = 100
        self.status_label.config(text="处理完成")
        
        self.log("\n" + "="*50)
        if preview_mode:
            self.log(f"【预览完成】共 {total} 个文件，成功解析 {processed} 个，失败 {errors} 个")
            self.log("取消预览模式后点击'开始处理'将实际执行重命名")
        else:
            self.log(f"【处理完成】共 {total} 个文件，成功重命名 {renamed} 个，失败 {errors} 个")
            if self.backup_var.get():
                self.log(f"原文件已备份至: {backup_folder}")
        self.log("="*50)
        
        messagebox.showinfo("完成", f"处理完成！\n总计: {total} 个文件\n成功: {processed} 个\n失败: {errors} 个")

def main():
    # 检查依赖
    try:
        import fitz
        from pdf2image import convert_from_path
        import pytesseract
        from PIL import Image
    except ImportError as e:
        print(f"缺少依赖: {e}")
        print("\n请安装以下依赖:")
        print("pip install PyMuPDF pdf2image pytesseract Pillow")
        print("\n并安装Tesseract-OCR引擎:")
        print("- Mac: brew install tesseract tesseract-lang")
        print("- Windows: 下载安装包 https://github.com/UB-Mannheim/tesseract/wiki")
        print("- Linux: sudo apt install tesseract-ocr tesseract-ocr-chi-sim")
        
        # 创建简易提示窗口
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("缺少依赖", 
            "请安装必要的依赖库:\n\n"
            "pip install PyMuPDF pdf2image pytesseract Pillow\n\n"
            "并安装Tesseract-OCR引擎:\n"
            "Mac: brew install tesseract tesseract-lang\n"
            "Windows: https://github.com/UB-Mannheim/tesseract/wiki\n"
            "Linux: sudo apt install tesseract-ocr tesseract-ocr-chi-sim")
        return
    
    # 启动主程序
    root = tk.Tk()
    app = InvoiceProcessor(root)
    root.mainloop()

if __name__ == "__main__":
    main()
