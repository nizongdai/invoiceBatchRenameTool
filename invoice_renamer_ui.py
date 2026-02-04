import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
import pdfplumber
import os
import re
import threading

def extract_name_from_block(block_text):
    if not block_text:
        return None
    lines = block_text.split("\n")
    for i, line in enumerate(lines):
        if "名" in line and "称" in line:
            candidate = line
            compact_line = re.sub(r'\s+', '', line)
            if re.search(r'名\s*称\s*[:：]?\s*$', line) or len(compact_line) <= 3:
                if i + 1 < len(lines):
                    candidate += lines[i + 1]
            candidate = re.sub(r'\s+', '', candidate)
            candidate = candidate.replace("购买方信息", "").replace("销售方信息", "")
            m = re.search(r'名称[:：]?(.+)', candidate)
            if m:
                name = re.split(r'纳税人识别号|统一社会信用代码', m.group(1))[0]
                name = re.sub(r'^(销售方信息|售方信息|销方信息|购买方信息|买方信息|购方信息)', '', name)
                if len(name) >= 2:
                    return name
    compact = re.sub(r'\s+', '', block_text)
    compact = compact.replace("购买方信息", "").replace("销售方信息", "")
    m = re.search(r'名称[:：]?(.{2,})', compact)
    if m:
        name = re.split(r'纳税人识别号|统一社会信用代码', m.group(1))[0]
        name = re.sub(r'^(销售方信息|售方信息|销方信息|购买方信息|买方信息|购方信息)', '', name)
        if len(name) >= 2:
            return name
    return None

def extract_name_from_words(words):
    if not words:
        return None
    labels = [w for w in words if "名称" in w["text"]]
    for label in labels:
        m = re.search(r'名称[:：]?(.+)', label["text"])
        if m:
            name = m.group(1).strip()
            name = re.sub(r'^(销售方信息|售方信息|销方信息|购买方信息|买方信息|购方信息)', '', name)
            if len(name) >= 2:
                return name
        label_y = (label["top"] + label["bottom"]) / 2
        line_words = [w for w in words if w["x0"] >= label["x1"] - 5 and abs(((w["top"] + w["bottom"]) / 2) - label_y) <= 3]
        line_words.sort(key=lambda w: w["x0"])
        if line_words:
            texts = []
            for w in line_words:
                if "纳税人识别号" in w["text"] or "统一社会信用代码" in w["text"]:
                    break
                texts.append(w["text"])
            name = "".join(texts).strip()
            name = re.sub(r'^(销售方信息|售方信息|销方信息|购买方信息|买方信息|购方信息)', '', name)
            if len(name) >= 2:
                return name
    return None

# --- 核心逻辑：提取发票信息 ---
def extract_invoice_info(pdf_path):
    try:
        with pdfplumber.open(pdf_path) as pdf:
            page = pdf.pages[0]
            width = page.width
            height = page.height
            text = page.extract_text()
            
            # --- 1. 提取开票日期 ---
            # 全局搜索日期，因为日期位置比较固定且格式独特
            date_match = re.search(r'(\d{4})\s*年\s*(\d{1,2})\s*月\s*(\d{1,2})\s*日', text)
            if date_match:
                year, month, day = date_match.groups()
                date_str = f"{year}{month.zfill(2)}{day.zfill(2)}"
            else:
                date_match_2 = re.search(r'(\d{4})-(\d{1,2})-(\d{1,2})', text)
                if date_match_2:
                    year, month, day = date_match_2.groups()
                    date_str = f"{year}{month.zfill(2)}{day.zfill(2)}"
                else:
                    date_str = "UnknownDate"

            # --- 2. 优化：使用区域裁剪提取购买方和销售方 ---
            # 策略：将页面分为左右两半，分别提取文本
            # 购买方区域：左半边，上部 (避开下方的项目明细)
            # 销售方区域：右半边，上部
            
            # 定义裁剪区域 (x0, top, x1, bottom)
            # 高度取前 40% 足够覆盖头部信息，且能避开下方的项目列表
            crop_height = height * 0.4
            
            # 左侧区域 (购买方)
            left_bbox = (0, 0, width * 0.55, crop_height) 
            # 右侧区域 (销售方) - 从中间稍微偏左一点开始，防止“销售方信息”竖排字被切断
            right_bbox = (width * 0.52, 0, width, crop_height)
            
            buyer = "UnknownBuyer"
            seller = "UnknownSeller"
            
            try:
                # 提取左侧文本
                left_crop = page.crop(left_bbox)
                left_words = left_crop.extract_words()
                name = extract_name_from_words(left_words)
                if not name:
                    left_text = left_crop.extract_text()
                    if left_text:
                        name = extract_name_from_block(left_text)
                if name:
                    buyer = name
            except Exception:
                pass # 裁剪失败则保持 Unknown
                
            try:
                # 提取右侧文本
                right_crop = page.crop(right_bbox)
                right_words = right_crop.extract_words()
                name = extract_name_from_words(right_words)
                if not name:
                    right_text = right_crop.extract_text()
                    if right_text:
                        name = extract_name_from_block(right_text)
                if name:
                    seller = name
                    print(f"右侧提取到销售方: {seller}")
            except Exception:
                pass

            # 清理结果
            buyer = buyer.replace("名称：", "").replace("名称:", "").strip()
            seller = seller.replace("名称：", "").replace("名称:", "").strip()
            
            # 兜底逻辑：如果裁剪没找到，尝试在全文中简单查找
            # 但要注意区分购买和销售，这在全文中很难，所以仅作为最后的尝试
            # 假设全文搜索到的第一个名称是购买方（通常左上角先被读取）
            if buyer == "UnknownBuyer" and seller == "UnknownSeller":
                 all_matches = re.findall(r'名\s*称\s*[:：]\s*([^\s]+)', text)
                 if len(all_matches) >= 2:
                     # 盲猜：第一个是购买方，第二个是销售方（风险较高，但比 Unknown 好）
                     buyer = all_matches[0]
                     seller = all_matches[1]
                 elif len(all_matches) == 1:
                     # 只有一个，很难说是谁，暂时给购买方
                     buyer = all_matches[0]


            # --- 4. 提取项目名称 ---
            items = []
            lines = text.split('\n')
            start_idx = -1
            for i, line in enumerate(lines):
                if "项目名称" in line:
                    start_idx = i
                    break
            
            if start_idx != -1:
                for i in range(start_idx + 1, len(lines)):
                    line = lines[i].strip()
                    if "合计" in line:
                        break
                    
                    if '*' in line:
                        token = line.split()[0]
                        if '*' in token:
                            items.append(token)
                            if i + 1 < len(lines):
                                next_line = lines[i+1].strip()
                                if next_line and "合计" not in next_line and "*" not in next_line:
                                    if not re.match(r'^\d', next_line) and len(next_line) < 20:
                                         items[-1] += next_line
            
            # --- 5. 汇总和格式化项目名称 ---
            if items:
                clean_items = [x for x in items if len(x) > 1]
                if not clean_items:
                    project_name = "UnknownItem"
                else:
                    first_item = clean_items[0]
                    first_item = re.sub(r'^\*.*?\*', '', first_item)
                    
                    if len(clean_items) > 1:
                        if len(first_item) > 8:
                             project_name = first_item[:9] 
                        else:
                             project_name = first_item + "等"
                    else:
                        project_name = first_item
                    
                    if len(project_name) > 10:
                        project_name = project_name[:10]
            else:
                project_name = "UnknownItem"
                
            # --- 6. 提取发票号码 ---
            invoice_num = "UnknownNum"
            # 常见的发票号码在右上角，格式为 20 位或 8 位数字
            # 搜索 "发票号码" 或 "No" 后面的数字
            # 正则：发票号码[:：]?\s*(\d+)
            num_match = re.search(r'发票号码[:：]?\s*(\d+)', text)
            if num_match:
                invoice_num = num_match.group(1)
            else:
                # 备用：搜索 No. 附近的数字
                num_match_2 = re.search(r'No[:\.]?\s*(\d+)', text, re.IGNORECASE)
                if num_match_2:
                    invoice_num = num_match_2.group(1)
                else:
                    # 备用2：直接搜索长数字串（20位或8位）
                    # 但这可能有误判，作为最后的手段
                    # 20位数字通常是全电发票号码
                    long_digits = re.search(r'\b(\d{20})\b', text)
                    if long_digits:
                        invoice_num = long_digits.group(1)

            return date_str, buyer, seller, project_name, invoice_num

    except Exception as e:
        return None, None, None, f"Error: {str(e)}", None

# --- UI 界面类 ---
class InvoiceRenamerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("发票自动重命名工具")
        self.root.geometry("600x500") # 增加高度以容纳新选项
        
        # 文件夹选择区域
        self.frame_top = tk.Frame(root, pady=20)
        self.frame_top.pack(fill=tk.X, padx=20)
        
        self.lbl_instruction = tk.Label(self.frame_top, text="请选择包含PDF发票的文件夹：", font=("Arial", 12))
        self.lbl_instruction.pack(anchor='w')
        
        self.frame_select = tk.Frame(self.frame_top)
        self.frame_select.pack(fill=tk.X, pady=5)
        
        self.entry_path = tk.Entry(self.frame_select, font=("Arial", 10))
        self.entry_path.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        
        self.btn_select = tk.Button(self.frame_select, text="选择文件夹", command=self.select_folder)
        self.btn_select.pack(side=tk.RIGHT)
        
        # --- 新增：命名规则选项 ---
        self.lbl_options = tk.Label(self.frame_top, text="请勾选文件名包含的内容：", font=("Arial", 10))
        self.lbl_options.pack(anchor='w', pady=(10, 0))

        self.frame_options = tk.Frame(self.frame_top)
        self.frame_options.pack(fill=tk.X, pady=5)
        
        self.var_date = tk.BooleanVar(value=True)
        self.var_buyer = tk.BooleanVar(value=False) # 默认不勾选购买方，因为是新功能且可能不常用
        self.var_seller = tk.BooleanVar(value=True)
        self.var_item = tk.BooleanVar(value=True)
        self.var_num = tk.BooleanVar(value=True)
        
        chk_date = tk.Checkbutton(self.frame_options, text="开票日期", variable=self.var_date)
        chk_date.pack(side=tk.LEFT, padx=(0, 10))
        
        chk_buyer = tk.Checkbutton(self.frame_options, text="购买方名称", variable=self.var_buyer)
        chk_buyer.pack(side=tk.LEFT, padx=(0, 10))
        
        chk_seller = tk.Checkbutton(self.frame_options, text="销售方名称", variable=self.var_seller)
        chk_seller.pack(side=tk.LEFT, padx=(0, 10))
        
        chk_item = tk.Checkbutton(self.frame_options, text="项目简述", variable=self.var_item)
        chk_item.pack(side=tk.LEFT, padx=(0, 10))

        chk_num = tk.Checkbutton(self.frame_options, text="发票号码", variable=self.var_num)
        chk_num.pack(side=tk.LEFT, padx=(0, 10))
        
        # 操作按钮
        self.btn_start = tk.Button(root, text="开始自动命名", font=("Arial", 14, "bold"), bg="#4CAF50", fg="black", command=self.start_renaming_thread)
        self.btn_start.pack(pady=10)
        
        # 日志输出区域
        self.lbl_log = tk.Label(root, text="运行日志：", font=("Arial", 10))
        self.lbl_log.pack(anchor='w', padx=20)
        
        self.txt_log = scrolledtext.ScrolledText(root, height=15, font=("Courier New", 10))
        self.txt_log.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))
        
        self.selected_directory = ""

    def select_folder(self):
        folder_selected = filedialog.askdirectory()
        if folder_selected:
            self.selected_directory = folder_selected
            self.entry_path.delete(0, tk.END)
            self.entry_path.insert(0, self.selected_directory)
            self.log(f"已选择文件夹: {self.selected_directory}")

    def log(self, message):
        self.txt_log.insert(tk.END, message + "\n")
        self.txt_log.see(tk.END)

    def start_renaming_thread(self):
        # 使用多线程避免界面卡顿
        if not self.selected_directory:
            messagebox.showwarning("提示", "请选择存放发票的文件夹！")
            return
        
        # 检查至少选择了一个命名规则
        if not any([self.var_date.get(), self.var_buyer.get(), self.var_seller.get(), self.var_item.get(), self.var_num.get()]):
            messagebox.showwarning("提示", "请至少勾选一个文件名规则！")
            return
            
        self.btn_start.config(state=tk.DISABLED, text="正在处理...")
        thread = threading.Thread(target=self.process_files)
        thread.start()

    def process_files(self):
        directory = self.selected_directory
        self.log("-" * 30)
        self.log("开始处理...")
        
        try:
            files = [f for f in os.listdir(directory) if f.lower().endswith('.pdf')]
            total = len(files)
            self.log(f"发现 {total} 个 PDF 文件。")
            
            count_success = 0
            count_fail = 0
            
            for filename in files:
                path = os.path.join(directory, filename)
                self.log(f"正在分析: {filename}")
                
                date_str, buyer, seller, project_name, invoice_num = extract_invoice_info(path)
                
                # 只要不是严重错误（Exception），即使某些字段是 Unknown 也可以尝试重命名
                if project_name and project_name.startswith("Error:"):
                    self.log(f"❌ 解析错误: {project_name}")
                    count_fail += 1
                    continue

                # 构建新文件名
                name_parts = []
                if self.var_date.get(): name_parts.append(date_str)
                if self.var_buyer.get(): name_parts.append(buyer)
                if self.var_seller.get(): name_parts.append(seller)
                if self.var_item.get(): name_parts.append(project_name)
                if self.var_num.get(): name_parts.append(invoice_num)
                
                if name_parts:
                    new_name = " - ".join(name_parts) + ".pdf"
                    # 清理文件名中的非法字符
                    new_name = re.sub(r'[\\/*?:"<>|]', "", new_name)
                    
                    new_path = os.path.join(directory, new_name)
                    
                    if path != new_path:
                        try:
                            os.rename(path, new_path)
                            self.log(f"✅ 重命名为: {new_name}")
                            count_success += 1
                        except OSError as e:
                            self.log(f"❌ 重命名失败: {e}")
                            count_fail += 1
                    else:
                        self.log(f"⚠️ 跳过 (文件名已正确): {filename}")
                        count_success += 1
                else:
                    self.log(f"⚠️ 跳过 (未生成有效文件名)")
                    count_fail += 1
                    
            self.log("-" * 30)
            self.log(f"处理完成。成功: {count_success}, 失败: {count_fail}")
            #messagebox.showinfo("完成", "执行完毕")
            
        except Exception as e:
            self.log(f"发生严重错误: {e}")
            messagebox.showerror("错误", f"发生错误: {e}")
        finally:
            self.root.after(0, self.reset_button)

    def reset_button(self):
        self.btn_start.config(state=tk.NORMAL, text="开始自动命名")

if __name__ == "__main__":
    root = tk.Tk()
    app = InvoiceRenamerApp(root)
    root.mainloop()
