from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QFormLayout, QLineEdit, QPushButton, 
                             QMessageBox, QLabel, QFileDialog, QScrollArea)
from PyQt6.QtCore import Qt
from docxtpl import DocxTemplate
import os
import datetime
from src.utils import open_file_or_folder

from src.odt_renderer import OdtTemplate

class DraftTab(QWidget):
    def __init__(self, project_manager, settings_tab):

        super().__init__()
        self.pm = project_manager
        self.settings_tab = settings_tab # Reference to get checked templates? 
        # Ideally, Model should manage state, but "checked items" is UI state.
        # We can ask SettingsTab for selection.
        self.input_widgets = {}
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Scroll Area for Form
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        self.form_container = QWidget()
        self.form_layout = QFormLayout(self.form_container)
        
        # FIX for MacOS: Ensure fields expand to fill width
        self.form_layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
        self.form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight) # Optional nice-to-have
        
        scroll.setWidget(self.form_container)
        layout.addWidget(scroll, 1)

        
        self.btn_generate = QPushButton("🚀 生成文档")
        self.btn_generate.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; padding: 15px; font-size: 14px;")
        self.btn_generate.clicked.connect(self.generate_documents)
        layout.addWidget(self.btn_generate)

        # Fix: Allow Enter key to trigger button when focused
        from PyQt6.QtGui import QShortcut, QKeySequence
        # Use WidgetShortcut so it only triggers when the button itself has focus
        self.shortcut_enter = QShortcut(QKeySequence(Qt.Key.Key_Return), self.btn_generate, context=Qt.ShortcutContext.WidgetShortcut)
        self.shortcut_enter.activated.connect(self.btn_generate.click)
        self.shortcut_return = QShortcut(QKeySequence(Qt.Key.Key_Enter), self.btn_generate, context=Qt.ShortcutContext.WidgetShortcut)
        self.shortcut_return.activated.connect(self.btn_generate.click)

    def build_form(self):
        # Clear existing
        while self.form_layout.count():
            item = self.form_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self.input_widgets.clear()
        
        fields = self.pm.project_data.get('fields', [])
        
        def add_fields_recursive(fields_list, prefix="", level=0):
            for field in fields_list:
                label_text = field['label']
                field_id = field['id']
                
                # Always create input for the field
                inp = QLineEdit()
                inp.setStyleSheet("font-size: 14px; padding: 4px;")
                
                # Style Guidelines:
                # Level 0 (Top Level): Bold, 14px
                # Level > 0 (Children): Normal, 14px
                
                label_widget = QLabel(prefix + label_text + ":")
                if level == 0:
                    label_widget.setStyleSheet("font-weight: bold; font-size: 14px; margin-top: 5px;")
                else:
                    # Normal style for children but ensure size is 14px
                    label_widget.setStyleSheet("font-size: 14px;")
                
                self.form_layout.addRow(label_widget, inp)
                self.input_widgets[field_id] = inp

                if 'children' in field and field['children']:
                     # Recurse with increased indentation
                     add_fields_recursive(field['children'], prefix=prefix + "    ", level=level+1)

        add_fields_recursive(fields)
        
        # KEYBOARD ACCESSIBILITY IMPROVEMENT:
        # 1. Enforce Tab Order: Input 1 -> Input 2 ... -> Generate Button
        widgets = list(self.input_widgets.values())
        if widgets:
            for i in range(len(widgets) - 1):
                self.setTabOrder(widgets[i], widgets[i+1])
            # Last input -> Generate Button
            self.setTabOrder(widgets[-1], self.btn_generate)
            
            # 2. Enter Key Shortcut:
            # Pressing Enter on the LAST input automatically focuses the Generate Button.
            # This allows the "Tab -> Enter" flow, or just "Enter -> Enter" flow.
            widgets[-1].returnPressed.connect(self.btn_generate.setFocus)

    def generate_documents(self):
        # 1. Validate Inputs
        context = {}
        missing_fields = []
        
        for fid, widget in self.input_widgets.items():
            val = widget.text() # User requests allowing spaces, so do not strip()
            if not val and val != "": 
                # Actually, if we allow spaces, we might just want to check if len == 0?
                # But 'val' is string. if val == "": it's empty.
                # If user wants to replace with empty string, they might just leave it blank?
                # But typically valid filling requires something.
                # User specifically asked for "spaces".
                pass
            
            # Revised Logic:
            # If user enters " ", keep it.
            # If user enters "", warn? Or just allow empty?
            # User said "allow input spaces". 
            # If I remove strip(), " " is Truthy. "" is Falsy.
            
            if len(val) == 0:
                # Find label for error message
                label = fid # fallback
                missing_fields.append(label)
            context[fid] = val
            
        if missing_fields:
            QMessageBox.warning(self, "信息不完整", f"以下字段未填写，请补充:\n{', '.join(missing_fields)}")
            return

        # 2. Get Selected Templates from Settings Tab
        # Accessing sibling tab directly is tight coupling, but simplest for now.
        # Ideally: Main Window gathers data or Model holds selection state.
        # Let's use the list in settings tab.
        selected_templates = []
        list_widget = self.settings_tab.settings_template_list
        for i in range(list_widget.count()):
            item = list_widget.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                selected_templates.append(item.text())

        if not selected_templates:
            QMessageBox.warning(self, "提示", "没有勾选任何模板。请在“模板设置”页勾选要生成的模板。")
            return

        # 3. Output Directory
        default_name = f"{self.pm.project_data.get('project_name')}_{datetime.date.today()}"
        folder_path, _ = QFileDialog.getSaveFileName(self, "保存生成文件到文件夹", 
                                                     os.path.join(os.path.expanduser("~"), "Desktop", default_name),
                                                     "Directory")
        if not folder_path:
            return # User cancelled

        if not os.path.exists(folder_path):
             os.makedirs(folder_path)

        # 4. Generate
        success_count = 0
        template_dir = self.pm.get_template_dir()
        
        for t_name in selected_templates:
            t_path = os.path.join(template_dir, t_name)
            if not os.path.exists(t_path):
                continue
            
            try:
                save_name = f"{t_name}" # Original name
                save_path = os.path.join(folder_path, save_name)
                
                ext = os.path.splitext(t_name)[1].lower()
                
                if ext == '.docx':
                    tpl = DocxTemplate(t_path)
                    tpl.render(context)
                    tpl.save(save_path)
                    success_count += 1
                elif ext == '.odt':
                    # Custom ODT Renderer (Clean & Jinja2)
                    t = OdtTemplate(t_path)
                    t.render(context, save_path)
                    success_count += 1

            except Exception as e:
                print(f"Error generating {t_name}: {e}")
                QMessageBox.critical(self, "生成错误", f"模版 {t_name} 生成失败: {e}")

        QMessageBox.information(self, "完成", f"成功生成 {success_count} 个文档！\n保存在: {folder_path}")
        open_file_or_folder(folder_path)
