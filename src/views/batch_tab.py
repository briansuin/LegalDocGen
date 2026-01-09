from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
                             QFileDialog, QTableWidget, QTableWidgetItem, QHeaderView,
                             QComboBox, QProgressBar, QMessageBox, QGroupBox, QListWidget, QListWidgetItem,
                             QApplication, QLineEdit, QFormLayout, QToolTip)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QDragEnterEvent, QDropEvent, QCursor
import openpyxl
from odf.opendocument import load
from odf.table import Table, TableRow, TableCell
from odf.text import P
import os
import datetime
from docxtpl import DocxTemplate
from src.odt_renderer import OdtTemplate
from src.utils import open_file_or_folder

class BatchWorker(QThread):
    progress = pyqtSignal(int)
    log = pyqtSignal(str)
    finished = pyqtSignal(int, int, str) # success, fail, final_path

    def __init__(self, data, template_path, output_dir_base, key_columns, prefix="", suffix=""):
        super().__init__()
        self.data = data
        self.template_path = template_path
        self.output_dir_base = output_dir_base
        self.key_columns = key_columns # List of column names
        self.prefix = prefix
        self.suffix = suffix
        self.is_running = True

    def run(self):
        success = 0
        fail = 0
        
        # 1. Create Subfolder
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        folder_name = f"批量生成_{timestamp}"
        final_output_dir = os.path.join(self.output_dir_base, folder_name)
        
        try:
            if not os.path.exists(final_output_dir):
                os.makedirs(final_output_dir)
        except Exception as e:
            self.log.emit(f"创建文件夹失败: {e}")
            self.finished.emit(0, len(self.data), self.output_dir_base)
            return

        ext = os.path.splitext(self.template_path)[1].lower()
        
        for i, row in enumerate(self.data):
            if not self.is_running:
                break
                
            try:
                # Determine Filename by joining multiple columns
                name_parts = []
                if self.key_columns:
                    for col in self.key_columns:
                        val = row.get(col, "")
                        if val:
                            name_parts.append(str(val).strip())
                
                if not name_parts:
                    base_name = f"doc_{i+1}"
                else:
                    base_name = "_".join(name_parts)
                
                # Apply Prefix/Suffix
                full_name_str = f"{self.prefix}{base_name}{self.suffix}"

                # Clean filename
                safe_name = "".join([c for c in full_name_str if c.isalpha() or c.isdigit() or c in (' ', '_', '-')]).strip()
                if not safe_name:
                    safe_name = f"doc_{i+1}"
                
                output_path = os.path.join(final_output_dir, f"{safe_name}{ext}")
                
                # Handle duplicates
                counter = 1
                while os.path.exists(output_path):
                    output_path = os.path.join(final_output_dir, f"{safe_name}_{counter}{ext}")
                    counter += 1

                if ext == '.docx':
                    tpl = DocxTemplate(self.template_path)
                    tpl.render(row)
                    tpl.save(output_path)
                    success += 1
                elif ext == '.odt':
                    tpl = OdtTemplate(self.template_path)
                    tpl.render(row, output_path)
                    success += 1
                else:
                    self.log.emit(f"不支持的格式: {ext}")
                    fail += 1

            except Exception as e:
                self.log.emit(f"Error row {i+1}: {e}")
                fail += 1
            
            self.progress.emit(i + 1)
        
        self.finished.emit(success, fail, final_output_dir)

    def stop(self):
        self.is_running = False

class DropLabel(QLabel):
    fileDropped = pyqtSignal(str)

    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setAcceptDrops(True)
        self.setStyleSheet("border: 2px dashed #aaa; padding: 10px; color: gray;")
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.setStyleSheet("border: 2px dashed #2196F3; padding: 10px; color: #2196F3; background-color: #E3F2FD;")
        else:
            event.ignore()

    def dragLeaveEvent(self, event):
        self.setStyleSheet("border: 2px dashed #aaa; padding: 10px; color: gray;")

    def dropEvent(self, event: QDropEvent):
        self.setStyleSheet("border: 2px dashed #aaa; padding: 10px; color: gray;")
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if urls:
                file_path = urls[0].toLocalFile()
                self.fileDropped.emit(file_path)
            event.acceptProposedAction()

class BatchTab(QWidget):
    def __init__(self):
        super().__init__()
        self.excel_path = None
        self.template_path = None
        self.excel_data = [] # List of dicts
        self.headers = []
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # 1. File Selection Area
        grp_files = QGroupBox("1. 文件选择")
        layout_files = QVBoxLayout(grp_files)
        
        # Excel Selection
        hbox_excel = QHBoxLayout()
        self.btn_load_excel = QPushButton("📂上传 Excel/ODS 表格")
        self.btn_load_excel.clicked.connect(self.select_excel_file)
        
        self.lbl_excel_path = DropLabel("未选择文件 (支持拖拽上传)")
        self.lbl_excel_path.fileDropped.connect(self.load_excel_file)
        
        hbox_excel.addWidget(self.btn_load_excel)
        hbox_excel.addWidget(self.lbl_excel_path, 1) # Provide stretch
        layout_files.addLayout(hbox_excel)
        
        # Template Selection
        hbox_tpl = QHBoxLayout()
        self.btn_load_tpl = QPushButton("📄上传 Word/ODT 模板")
        self.btn_load_tpl.clicked.connect(self.select_template_file)
        
        self.lbl_tpl_path = DropLabel("未选择文件 (支持拖拽上传)")
        self.lbl_tpl_path.fileDropped.connect(self.load_template_file)
        
        hbox_tpl.addWidget(self.btn_load_tpl)
        hbox_tpl.addWidget(self.lbl_tpl_path, 1)
        layout_files.addLayout(hbox_tpl)
        
        layout.addWidget(grp_files)

        # 2. Data Preview & Settings
        grp_data = QGroupBox("2. 数据预览与设置")
        layout_data = QVBoxLayout(grp_data)
        
        self.table_preview = QTableWidget()
        self.table_preview.setColumnCount(0)
        self.table_preview.setRowCount(0)
        self.table_preview.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table_preview.setStyleSheet("font-size: 13px;")
        layout_data.addWidget(self.table_preview)
        
        hbox_settings = QHBoxLayout()
        
        # Left: Column Selection
        vbox_cols = QVBoxLayout()
        vbox_cols.addWidget(QLabel("文件名组成列 (多选 | 单击复制变量):"))
        self.list_key_cols = QListWidget()
        self.list_key_cols.setMaximumHeight(100)
        self.list_key_cols.setStyleSheet("font-size: 13px;")
        self.list_key_cols.itemClicked.connect(self.copy_col_variable) # Click to copy
        vbox_cols.addWidget(self.list_key_cols)
        hbox_settings.addLayout(vbox_cols, 1)
        
        # Right: Prefix/Suffix
        vbox_affix = QVBoxLayout()
        vbox_affix.addWidget(QLabel("文件名修饰:"))
        form_affix = QFormLayout()
        self.input_prefix = QLineEdit()
        self.input_prefix.setPlaceholderText("例如: 2024_")
        self.input_suffix = QLineEdit()
        self.input_suffix.setPlaceholderText("例如: _邀请函")
        form_affix.addRow("前缀:", self.input_prefix)
        form_affix.addRow("后缀:", self.input_suffix)
        vbox_affix.addLayout(form_affix)
        vbox_affix.addStretch()
        hbox_settings.addLayout(vbox_affix, 1)

        layout_data.addLayout(hbox_settings)
        
        layout.addWidget(grp_data)

        # 3. Output & Action
        grp_action = QGroupBox("3. 生成设置")
        layout_action = QVBoxLayout(grp_action)
        
        hbox_out = QHBoxLayout()
        self.btn_out_dir = QPushButton("📂 选择保存位置")
        self.btn_out_dir.clicked.connect(self.select_output_dir)
        self.lbl_out_dir = QLabel(os.path.join(os.path.expanduser("~"), "Desktop"))
        hbox_out.addWidget(self.btn_out_dir)
        hbox_out.addWidget(self.lbl_out_dir)
        layout_action.addLayout(hbox_out)
        
        lbl_hint = QLabel("提示: 系统将自动在选定位置创建一个包含时间戳的文件夹来存放生成的文件")
        lbl_hint.setStyleSheet("font-style: italic; color: gray; font-size: 12px;")
        layout_action.addWidget(lbl_hint)
        
        self.pbar = QProgressBar()
        self.pbar.setValue(0)
        layout_action.addWidget(self.pbar)
        
        self.btn_run = QPushButton("🚀 开始批量生成")
        self.btn_run.setStyleSheet("background-color: #2196F3; color: white; font-weight: bold; padding: 12px; font-size: 14px;")
        self.btn_run.clicked.connect(self.start_generation)
        self.btn_run.setEnabled(False)
        layout_action.addWidget(self.btn_run)
        
        layout.addWidget(grp_action)
    
    def select_excel_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "选择表格文件", "", "Excel/ODS Files (*.xlsx *.xls *.ods)")
        if path:
            self.load_excel_file(path)

    def load_excel_file(self, path):
         try:
            ext = os.path.splitext(path)[1].lower()
            if ext == '.ods':
                self.load_ods_data(path)
            elif ext in ['.xlsx', '.xls']:
                self.load_xlsx_data(path)
            else:
                QMessageBox.warning(self, "格式错误", "不支持的文件格式")
                return
            
            self.lbl_excel_path.setText(os.path.basename(path))
            self.lbl_excel_path.setStyleSheet("border: 2px solid #4CAF50; padding: 10px; color: black; background-color: #E8F5E9;") # Green border for success
            self.excel_path = path
            
            # Update UI
            self.update_preview()
            self.update_key_list()
            self.check_ready()
            
         except Exception as e:
            QMessageBox.critical(self, "加载失败", f"无法读取文件: {e}")
            self.lbl_excel_path.setText("未选择文件 (支持拖拽上传)")
            self.lbl_excel_path.setStyleSheet("border: 2px dashed #aaa; padding: 10px; color: gray;")

    def load_xlsx_data(self, path):
        wb = openpyxl.load_workbook(path, data_only=True)
        ws = wb.active
        
        rows = list(ws.iter_rows(values_only=True))
        if not rows:
            raise Exception("文件为空")
            
        self.headers = [str(h) if h else f"Col_{i}" for i, h in enumerate(rows[0])]
        data_rows = rows[1:]
        
        self.excel_data = []
        for r in data_rows:
            row_dict = {}
            for i, val in enumerate(r):
                if i < len(self.headers):
                    row_dict[self.headers[i]] = val
            self.excel_data.append(row_dict)

    def load_ods_data(self, path):
        doc = load(path)
        # Get first sheet
        try:
            sheet = doc.spreadsheet.getElementsByType(Table)[0]
        except IndexError:
            raise Exception("找不到工作表")

        rows = sheet.getElementsByType(TableRow)
        if not rows:
            raise Exception("文件为空")
        
        # Helper to extract text from cell
        def get_cell_text(cell):
            ps = cell.getElementsByType(P)
            if not ps: return ""
            return "".join([p.firstChild.data for p in ps if p.firstChild])

        # Parse data
        all_data = []
        for row in rows:
            cells = row.getElementsByType(TableCell)
            row_vals = []
            
            for cell in cells:
                repeat = int(cell.getAttribute("numbercolumnsrepeated") or 1)
                text = get_cell_text(cell)
                for _ in range(repeat):
                    row_vals.append(text)
            
            # Filter empty trailing rows if needed
            if any(row_vals):
                all_data.append(row_vals)

        if not all_data:
            raise Exception("没有数据")

        self.headers = [str(h) for h in all_data[0]]
        self.excel_data = []
        for r in all_data[1:]:
            row_dict = {}
            for i, val in enumerate(r):
                if i < len(self.headers):
                    row_dict[self.headers[i]] = val
            self.excel_data.append(row_dict)

    def update_preview(self):
        self.table_preview.clear()
        self.table_preview.setColumnCount(len(self.headers))
        self.table_preview.setHorizontalHeaderLabels(self.headers)
        
        # Show max 5 data rows
        display_rows = self.excel_data[:5]
        self.table_preview.setRowCount(len(display_rows))
        
        for r_idx, row_data in enumerate(display_rows):
            for c_idx, col_name in enumerate(self.headers):
                val = row_data.get(col_name, "")
                self.table_preview.setItem(r_idx, c_idx, QTableWidgetItem(str(val) if val is not None else ""))

    def update_key_list(self):
        self.list_key_cols.clear()
        for h in self.headers:
            item = QListWidgetItem(h)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled) 
            # Note: need ItemIsEnabled to be clickable
            
            # Auto-check likely candidates
            if "姓名" in h or "Name" in h:
                item.setCheckState(Qt.CheckState.Checked)
            else:
                item.setCheckState(Qt.CheckState.Unchecked)
                
            self.list_key_cols.addItem(item)
            
        # If nothing checked, check first
        checked_items = [self.list_key_cols.item(i) for i in range(self.list_key_cols.count()) if self.list_key_cols.item(i).checkState() == Qt.CheckState.Checked]
        if not checked_items and self.list_key_cols.count() > 0:
             self.list_key_cols.item(0).setCheckState(Qt.CheckState.Checked)

    def select_template_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "选择模板文件", "", "Word/ODT Files (*.docx *.odt)")
        if path:
            self.load_template_file(path)

    def load_template_file(self, path):
         ext = os.path.splitext(path)[1].lower()
         if ext not in ['.docx', '.odt']:
             QMessageBox.warning(self, "格式错误", "不支持的模板格式")
             return

         self.template_path = path
         self.lbl_tpl_path.setText(os.path.basename(path))
         self.lbl_tpl_path.setStyleSheet("border: 2px solid #4CAF50; padding: 10px; color: black; background-color: #E8F5E9;")
         self.check_ready()

    def select_output_dir(self):
        d = QFileDialog.getExistingDirectory(self, "选择保存位置", self.lbl_out_dir.text())
        if d:
            self.lbl_out_dir.setText(d)

    def check_ready(self):
        if self.excel_data and self.template_path:
            self.btn_run.setEnabled(True)
            self.btn_run.setText(f"🚀 开始批量生成 ({len(self.excel_data)} 份)")
        else:
            self.btn_run.setEnabled(False)
            self.btn_run.setText("🚀 开始批量生成")

    def copy_col_variable(self, item):
        # Click to copy {{Variable}}
        txt = item.text()
        var_text = f"{{{{{txt}}}}}"
        QApplication.clipboard().setText(var_text)
        
        # In QListWidget, itemClicked triggers on check too. 
        # But that's fine, copying is harmless side effect.
        # Ideally differentiate, but checkState check is separated from clicked usually.
        # We can just show tooltip.
        QToolTip.showText(QCursor.pos(), f"已复制: {var_text}")

    def start_generation(self):
        out_dir = self.lbl_out_dir.text()
        if not os.path.exists(out_dir):
            os.makedirs(out_dir)
            
        # Get selected key columns
        selected_keys = []
        for i in range(self.list_key_cols.count()):
            item = self.list_key_cols.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                selected_keys.append(item.text())
        
        if not selected_keys:
             QMessageBox.warning(self, "提示", "请至少选择一列作为文件名。")
             return

        prefix = self.input_prefix.text()
        suffix = self.input_suffix.text()

        self.btn_run.setEnabled(False)
        self.pbar.setMaximum(len(self.excel_data))
        self.pbar.setValue(0)
        
        self.worker = BatchWorker(self.excel_data, self.template_path, out_dir, selected_keys, prefix, suffix)
        self.worker.progress.connect(self.pbar.setValue)
        self.worker.log.connect(lambda s: print(s)) 
        self.worker.finished.connect(self.on_generation_finished)
        self.worker.start()

    def on_generation_finished(self, success, fail, final_path):
        self.btn_run.setEnabled(True)
        QMessageBox.information(self, "完成", f"生成结束。\n成功: {success}\n失败: {fail}\n\n文件已保存至:\n{final_path}")
        open_file_or_folder(final_path)
