import os
import shutil
import keyword
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QCheckBox, QListWidget, QListWidgetItem, 
                             QHBoxLayout, QPushButton, QFrame, 
                             QMessageBox, QFileDialog, QInputDialog, QMenu, QApplication)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QAction
from src.utils import SmartSync, open_file_or_folder

class SettingsTab(QWidget):
    projectChanged = pyqtSignal() # Emitted when template/fields change so Draft tab can update
    statusMessage = pyqtSignal(str) # Emitted to show messages in main window status bar

    def __init__(self, project_manager):
        super().__init__()
        self.pm = project_manager
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # 1. Templates List
        layout.addWidget(QLabel("导入模板:"))
        
        # Select All Checkbox
        self.chk_select_all_tpl = QCheckBox("全选/全不选")
        self.chk_select_all_tpl.setChecked(True)
        self.chk_select_all_tpl.stateChanged.connect(self.toggle_all_templates)
        layout.addWidget(self.chk_select_all_tpl)
        
        self.settings_template_list = QListWidget()
        self.settings_template_list.setDragDropMode(QListWidget.DragDropMode.InternalMove)
        
        # Handle Drop Event Manually
        original_tpl_drop = self.settings_template_list.dropEvent
        def wrapped_tpl_drop(event):
            original_tpl_drop(event)
            self.save_template_order()
        self.settings_template_list.dropEvent = wrapped_tpl_drop
        
        # Context Menu
        self.settings_template_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.settings_template_list.customContextMenuRequested.connect(self.show_template_context_menu)
        
        self.settings_template_list.itemDoubleClicked.connect(self.open_template_file)
        layout.addWidget(self.settings_template_list)
        
        hbox_tpl_btns = QHBoxLayout()
        btn_add_tpl = QPushButton("添加新的模板文件")
        btn_add_tpl.clicked.connect(self.add_template_to_project)
        hbox_tpl_btns.addWidget(btn_add_tpl)
        
        btn_export_tpl = QPushButton("导出模板文件")
        btn_export_tpl.clicked.connect(self.export_templates)
        hbox_tpl_btns.addWidget(btn_export_tpl)
        
        btn_del_tpl = QPushButton("删除选中模板")
        btn_del_tpl.setStyleSheet("color: red;")
        btn_del_tpl.clicked.connect(self.delete_template_file)
        hbox_tpl_btns.addWidget(btn_del_tpl)
        
        layout.addLayout(hbox_tpl_btns)
        
        layout.addWidget(QFrame(frameShape=QFrame.Shape.HLine))

        # 2. Fields List
        layout.addWidget(QLabel("输入区 (表单):"))
        self.settings_field_list = QListWidget()
        self.settings_field_list.setDragDropMode(QListWidget.DragDropMode.InternalMove)
        
        # Handle Drop Event Manually
        original_list_drop = self.settings_field_list.dropEvent
        def wrapped_list_drop(event):
            original_list_drop(event)
            self.save_field_order()
        self.settings_field_list.dropEvent = wrapped_list_drop
        
        self.settings_field_list.itemClicked.connect(self.copy_field_tag)
        layout.addWidget(self.settings_field_list)
        
        hbox_btns = QHBoxLayout()
        btn_add_field = QPushButton("添加新的输入区")
        btn_add_field.clicked.connect(self.add_field_to_project)
        hbox_btns.addWidget(btn_add_field)
        
        btn_edit = QPushButton("编辑选中")
        btn_edit.clicked.connect(self.edit_field)
        hbox_btns.addWidget(btn_edit)

        btn_delete = QPushButton("删除选中")
        btn_delete.setStyleSheet("color: red;")
        btn_delete.clicked.connect(self.delete_field)
        hbox_btns.addWidget(btn_delete)
        
        layout.addLayout(hbox_btns)

    def load_project_data(self):
        # Refresh Lists
        self.settings_template_list.clear()
        self.settings_template_list.clear()
        templates = self.pm.project_data.get('templates', [])
        for t in templates:
            item = QListWidgetItem(t)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Checked)
            self.settings_template_list.addItem(item)
            
        self.settings_field_list.clear() # Clear fields list
        
        raw_fields = self.pm.project_data.get('fields', [])
        
        # Flatten recursive structure if exists
        def flatten_fields(fields_list):
            flat = []
            for f in fields_list:
                # Create a clean copy without children
                new_f = {k: v for k, v in f.items() if k != 'children'}
                flat.append(new_f)
                if 'children' in f and f['children']:
                    flat.extend(flatten_fields(f['children']))
            return flat

        flat_fields = flatten_fields(raw_fields)
        
        # Update project data to flat structure immediately to ensure consistency
        self.pm.project_data['fields'] = flat_fields
        
        for field in flat_fields:
            item = QListWidgetItem(field['label'])
            item.setData(Qt.ItemDataRole.UserRole, field)
            self.settings_field_list.addItem(item)

    # --- ACTIONS ---
    def toggle_all_templates(self, state):
        chk_state = Qt.CheckState(state)
        for i in range(self.settings_template_list.count()):
            item = self.settings_template_list.item(i)
            item.setCheckState(chk_state)

    def save_template_order(self):
        new_order = []
        for i in range(self.settings_template_list.count()):
            new_order.append(self.settings_template_list.item(i).text())
        
        self.pm.project_data['templates'] = new_order
        self.pm.save_current_project()
        # No need to signal projectChanged for template order, but good practice

    def save_field_order(self):
        new_fields = []
        for i in range(self.settings_field_list.count()):
            item = self.settings_field_list.item(i)
            data = item.data(Qt.ItemDataRole.UserRole)
            # Ensure no 'children' key persists
            if 'children' in data:
                del data['children']
            new_fields.append(data)
        
        self.pm.project_data['fields'] = new_fields
        self.pm.save_current_project()
        self.projectChanged.emit()



    def add_template_to_project(self):
        files, _ = QFileDialog.getOpenFileNames(self, "选择模板文件", os.path.expanduser("~"), "Word Files (*.docx)")
        if files:
            target_dir = self.pm.get_template_dir()
            for f in files:
                filename = os.path.basename(f)
                dest = os.path.join(target_dir, filename)
                if filename not in self.pm.project_data['templates']:
                    self.pm.project_data['templates'].append(filename)
                shutil.copy(f, dest)
            self.pm.save_current_project()
            self.load_project_data()

    def export_templates(self):
        items_to_export = []
        for i in range(self.settings_template_list.count()):
            item = self.settings_template_list.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                items_to_export.append(item.text())

        if not items_to_export:
            QMessageBox.warning(self, "警告", "请先勾选要导出的模板。")
            return

        target_dir = QFileDialog.getExistingDirectory(self, "选择导出目标文件夹", os.path.expanduser("~"))
        if not target_dir:
            return

        project_name = self.pm.project_data.get('project_name', 'Exported_Templates')
        # Sanitize project name for filesystem
        safe_project_name = project_name.replace("/", "_").replace("\\", "_").replace(":", "_").replace("*", "").replace("?", "").replace("\"", "").replace("<", "").replace(">", "").replace("|", "").strip()
        export_path = os.path.join(target_dir, safe_project_name)
        
        try:
            os.makedirs(export_path, exist_ok=True)
            
            template_dir = self.pm.get_template_dir()
            count = 0
            for t_name in items_to_export:
                src = os.path.join(template_dir, t_name)
                dst = os.path.join(export_path, t_name)
                if os.path.exists(src):
                    shutil.copy(src, dst)
                    count += 1
            
            QMessageBox.information(self, "导出成功", f"成功导出 {count} 个模板到:\n{export_path}")
        except Exception as e:
            QMessageBox.critical(self, "导出失败", f"导出过程中发生错误:\n{e}")

    def delete_template_file(self):
        items_to_delete = []
        for i in range(self.settings_template_list.count()):
            item = self.settings_template_list.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                items_to_delete.append(item.text())

        if not items_to_delete:
            QMessageBox.warning(self, "警告", "请先勾选要删除的模板。")
            return

        msg = QMessageBox()
        msg.setWindowTitle("确认删除")
        msg.setText(f"您确定要删除选中的 {len(items_to_delete)} 个模板吗？")
        msg.setInformativeText("这将从项目中移除模板，并从磁盘中永久删除文件。")
        msg.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        msg.setDefaultButton(QMessageBox.StandardButton.No)
        
        ret = msg.exec()
        if ret != QMessageBox.StandardButton.Yes:
            return

        target_dir = self.pm.get_template_dir()
        
        for t_name in items_to_delete:
            if t_name in self.pm.project_data['templates']:
                self.pm.project_data['templates'].remove(t_name)
            
            # Always delete file
            t_path = os.path.join(target_dir, t_name)
            try:
                if os.path.exists(t_path):
                    os.remove(t_path)
            except Exception as e:
                print(f"Error deleting file {t_path}: {e}")

        self.pm.save_current_project()
        self.load_project_data()

    def open_template_file(self, item):
        filename = item.text()
        filepath = os.path.join(self.pm.get_template_dir(), filename)
        if os.path.exists(filepath):
            open_file_or_folder(filepath)
        else:
             QMessageBox.warning(self, "错误", "找不到文件！")

    def show_template_context_menu(self, pos):
        item = self.settings_template_list.itemAt(pos)
        if not item: return

        menu = QMenu(self)
        rename_action = QAction("重命名", self)
        rename_action.triggered.connect(lambda: self.rename_template(item))
        menu.addAction(rename_action)

        delete_action = QAction("删除", self)
        delete_action.triggered.connect(lambda: self.delete_template_context(item))
        menu.addAction(delete_action)

        menu.exec(self.settings_template_list.mapToGlobal(pos))

    def rename_template(self, item):
        old_name = item.text()
        project_dir = self.pm.get_template_dir()
        old_path = os.path.join(project_dir, old_name)
        
        if not os.path.exists(old_path):
             QMessageBox.warning(self, "错误", "找不到文件，无法重命名。")
             return

        new_name, ok = QInputDialog.getText(self, "重命名模板", "新文件名:", text=old_name)
        if ok and new_name and new_name != old_name:
            if not new_name.endswith('.docx'):
                new_name += '.docx'
            new_path = os.path.join(project_dir, new_name)
            if os.path.exists(new_path):
                QMessageBox.warning(self, "错误", "该文件名已存在。")
                return
            try:
                os.rename(old_path, new_path)
                if old_name in self.pm.project_data['templates']:
                    idx = self.pm.project_data['templates'].index(old_name)
                    self.pm.project_data['templates'][idx] = new_name
                self.pm.save_current_project()
                self.load_project_data()
            except Exception as e:
                QMessageBox.critical(self, "错误", f"重命名失败: {e}")

    def delete_template_context(self, item):
        t_name = item.text()
        ret = QMessageBox.question(self, "确认删除", f"确定要删除模板: {t_name} 吗？\n将会同时从磁盘删除该文件。",
                                   QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel)
        if ret == QMessageBox.StandardButton.Yes:
             if t_name in self.pm.project_data['templates']:
                 self.pm.project_data['templates'].remove(t_name)
             target_dir = self.pm.get_template_dir()
             t_path = os.path.join(target_dir, t_name)
             if os.path.exists(t_path):
                 os.remove(t_path)
             self.pm.save_current_project()
             self.load_project_data()

    # --- FIELDS ---
    def copy_field_tag(self, item):
        data = item.data(Qt.ItemDataRole.UserRole)
        if data and 'id' in data:
            tag = f"{{{{{data['id']}}}}}"
            QApplication.clipboard().setText(tag)
            self.statusMessage.emit(f"已复制标签: {tag}")

    def find_field(self, fields, target_id):
        for f in fields:
            if f['id'] == target_id:
                return f
        return None

    def add_field_to_project(self):
        name, ok = QInputDialog.getText(self, "新建输入区", "名称 (将作为标签和标签ID):\n(必须以字母或下划线开头，仅包含字母、数字、下划线，不能有空格)")
        if ok and name:
            if not name.isidentifier() or keyword.iskeyword(name):
                 QMessageBox.warning(self, "非法名称", f"名称 '{name}' 不是有效的变量名。\n请确保以字母或下划线开头，且不包含空格或特殊符号。")
                 return
            
            if self.find_field(self.pm.project_data.get('fields', []), name):
                QMessageBox.warning(self, "错误", f"名称 '{name}' 已存在。")
                return
            new_field = {"id": name, "label": name}
            self.pm.project_data.setdefault('fields', []).append(new_field)
            self.pm.save_current_project()
            self.load_project_data()
            self.projectChanged.emit()

    def edit_field(self):
        item = self.settings_field_list.currentItem()
        if not item: return
        data = item.data(Qt.ItemDataRole.UserRole)
        old_id = data['id']
        
        # Since we load flat fields into UI but project_data might still be nested if we didn't save yet?
        # Actually load_project_data flattens into UI, but pm.project_data is RAW.
        # We should ensure pm.project_data is flattened or we search it properly.
        # For simplicity, let's rely on save_field_order being called or just flattening project_data on load?
        # To avoid sync issues, let's flatten project_data in load_project_data properly or ensure we work on a flat list.
        # In load_project_data, I implemented flattening for display. 
        # If I edit, I'm finding in project_data.
        # I should probably just use the data from the item directly or ensure project_data is flat.
        
        # Let's flatten project_data permanently on the first load/save cycle to make this easier.
        # But wait, 'find_field' takes 'fields'.
        # I'll update find_field to just search the list passed.
        
        # If we just force a save of the flat structure during load, it simplifies everything.
        # But changing data on load is aggressive.
        
        # Let's assume for now the user has hit "save" via reordering or we just flattened it.
        # Actually, let's look at my find_field impl effectively acting on flat list.
        # If project_data['fields'] is still nested, find_field (flat version) won't find children.
        # So we MUST flatten project_data['fields'] when we start working in this mode.
        # I will start by forcing a flatten in 'load_project_data' and SAVING it? 
        # Or just use the 'save_field_order' to sync the list back to project_data BEFORE performing operations?
        
        # Simpler approach: 
        # 1. In 'load_project_data', update self.pm.project_data['fields'] to be the flat version.
        # 2. Then proceed.
        
        target_field = self.find_field(self.pm.project_data['fields'], old_id)
        if not target_field:
             # Just in case
             return

        new_name, ok = QInputDialog.getText(self, "编辑", "名称:\n(必须以字母或下划线开头，仅包含字母、数字、下划线)", text=target_field['label'])
        if ok and new_name:
            if not new_name.isidentifier() or keyword.iskeyword(new_name):
                 QMessageBox.warning(self, "非法名称", f"名称 '{new_name}' 不是有效的变量名。\n请确保以字母或下划线开头，且不包含空格或特殊符号。")
                 return
                 
            if new_name != old_id:
                if self.find_field(self.pm.project_data['fields'], new_name):
                    QMessageBox.warning(self, "错误", "名称已存在。")
                    return
                target_field['label'] = new_name
                target_field['id'] = new_name
                
                # Sync logic calling Utils
                changes = 0
                templates = self.pm.project_data.get('templates', [])
                tdir = self.pm.get_template_dir()
                for t in templates:
                    tpath = os.path.join(tdir, t)
                    if SmartSync.sync_template_variable(tpath, old_id, new_name):
                        changes += 1

                self.pm.save_current_project()
                self.load_project_data()
                self.projectChanged.emit()
                if changes > 0:
                    QMessageBox.information(self, "同步", f"已在 {changes} 个模板中重命名变量。")

    def delete_field(self):
        item = self.settings_field_list.currentItem()
        if not item: return
        data = item.data(Qt.ItemDataRole.UserRole)
        target_id = data['id']
        
        result = QMessageBox.question(self, "确认删除", f"删除 '{target_id}'?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if result == QMessageBox.StandardButton.Yes:
            # Remove from UI list first
            row = self.settings_field_list.row(item)
            self.settings_field_list.takeItem(row)
            
            # Save the new order (which effectively deletes the item from project_data)
            self.save_field_order()
            self.load_project_data() # Reload to clear/refresh
            self.projectChanged.emit()
