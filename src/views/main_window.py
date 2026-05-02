from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QListWidget, QPushButton, QTabWidget, QSplitter,
                             QMenu, QMessageBox, QInputDialog, QDockWidget, QTreeWidget, QTreeWidgetItem, QApplication, QLineEdit)
from PyQt6.QtGui import QAction
from PyQt6.QtCore import Qt, QSettings
from src.views.draft_tab import DraftTab
from src.views.settings_tab import SettingsTab
from src.views.help_tab import HelpTab
from src.views.batch_tab import BatchTab

class MainWindow(QMainWindow):
    def __init__(self, project_manager):
        super().__init__()
        self.pm = project_manager
        
        self.setWindowTitle("盈科文书助手")
        self.setGeometry(100, 100, 1000, 700)
        
        self.last_text_input = None
        QApplication.instance().focusChanged.connect(self.on_focus_changed)

        self.setup_ui()
        self.setup_citation_drawer()
        self.refresh_project_list()
        
        # Restore window size and position
        self.restore_window_state()

        # Auto-load first project if available
        if self.project_list.count() > 0:
            item = self.project_list.item(0)
            self.project_list.setCurrentItem(item)
            self.load_project(item)

        self.statusBar().showMessage("Ready")

    def setup_ui(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout(main_widget)

        # 1. SIDEBAR
        sidebar = QWidget()
        sidebar_layout = QVBoxLayout(sidebar)
        
        lbl_proj = QLabel("📂 我的项目")
        lbl_proj.setStyleSheet("font-weight: bold; font-size: 14px;")
        sidebar_layout.addWidget(lbl_proj)
        
        self.project_list = QListWidget()
        self.project_list.setDragDropMode(QListWidget.DragDropMode.InternalMove)
        self.project_list.setStyleSheet("font-size: 14px;")
        
        # Drop Event for Persistence
        original_proj_drop = self.project_list.dropEvent
        def wrapped_proj_drop(event):
            original_proj_drop(event)
            self.save_project_order()
        self.project_list.dropEvent = wrapped_proj_drop
        
        self.project_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.project_list.customContextMenuRequested.connect(self.show_project_context_menu)
        self.project_list.itemClicked.connect(self.load_project)
        sidebar_layout.addWidget(self.project_list)
        
        btn_new_proj = QPushButton("+ 创建新项目")
        btn_new_proj.setStyleSheet("background-color: #2196F3; color: white; padding: 15px; font-size: 14px; font-weight: bold;")
        btn_new_proj.clicked.connect(self.create_new_project)
        sidebar_layout.addWidget(btn_new_proj)

        # 2. TABS
        self.tabs = QTabWidget()
        # Don't disable all. We want Help (index 2) always enabled.
        # We will disable 0 and 1 explicitly later.

        # Instantiate Tabs
        self.tab_settings = SettingsTab(self.pm)
        # Draft tab needs reference to Settings for "checked templates"
        self.tab_draft = DraftTab(self.pm, self.tab_settings) 
        self.tab_batch = BatchTab()
        self.tab_help = HelpTab()

        self.tabs.addTab(self.tab_draft, "📝 填写内容")
        self.tabs.addTab(self.tab_settings, "⚙️ 模板与输入区设置")
        self.tabs.addTab(self.tab_batch, "📧 批量生成")
        self.tabs.addTab(self.tab_help, "❓ 帮助说明")
        
        # Connect Signals
        self.tab_settings.projectChanged.connect(self.tab_draft.build_form)
        self.tab_settings.statusMessage.connect(lambda msg: self.statusBar().showMessage(msg, 5000))
        
        # Initial State: Disable Draft(0) and Settings(1), Enable Help(2)
        self.tabs.setTabEnabled(0, False)
        self.tabs.setTabEnabled(1, False)
        self.tabs.setTabEnabled(2, True)

        # Style
        self.tabs.setStyleSheet("""
            QTabBar::tab:first {
                font-weight: bold;
                color: #2E7D32; 
                min-width: 150px;
            }
            QTabBar::tab {
                min-width: 120px;
                padding: 8px;
                font-size: 14px;
            }
        """)

        # Splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setObjectName("mainSplitter")
        splitter.addWidget(sidebar)
        splitter.addWidget(self.tabs)
        splitter.setSizes([200, 800])
        # Add a hidden "Expand Drawer" button to the main layout that appears when the dock is hidden
        # We'll make it a thin button between the splitter and the dock widget
        self.btn_toggle_citation = QPushButton(">>")
        self.btn_toggle_citation.setFixedWidth(20)
        self.btn_toggle_citation.setSizePolicy(self.btn_toggle_citation.sizePolicy().Policy.Fixed, self.btn_toggle_citation.sizePolicy().Policy.Expanding)
        self.btn_toggle_citation.setStyleSheet("background-color: #E0E0E0; border: none; font-weight: bold;")
        self.btn_toggle_citation.clicked.connect(self.toggle_citation_drawer)
        
        # We need a layout to hold the splitter, this edge button, and potentially the dock area
        wrapper_layout = QHBoxLayout()
        wrapper_layout.setContentsMargins(0, 0, 0, 0)
        wrapper_layout.setSpacing(0)
        wrapper_layout.addWidget(splitter)
        wrapper_layout.addWidget(self.btn_toggle_citation)
        
        main_layout.addLayout(wrapper_layout)

    def setup_citation_drawer(self):
        self.citation_dock = QDockWidget("引用库", self)
        self.citation_dock.setObjectName("citationDock")
        self.citation_dock.setAllowedAreas(Qt.DockWidgetArea.RightDockWidgetArea | Qt.DockWidgetArea.LeftDockWidgetArea)
        self.citation_dock.setFeatures(QDockWidget.DockWidgetFeature.NoDockWidgetFeatures)
        # Apply style to the MainWindow to ensure DockWidget title inherits it properly
        current_style = self.styleSheet()
        self.setStyleSheet(current_style + """
            QDockWidget {
                font-size: 14px;
                font-weight: normal;
            }
        """)
        
        dock_widget = QWidget()
        dock_layout = QVBoxLayout(dock_widget)
        
        self.citation_search = QLineEdit()
        self.citation_search.setPlaceholderText("搜索...")
        self.citation_search.textChanged.connect(self.filter_snippets)
        dock_layout.addWidget(self.citation_search)
        
        self.citation_tree = QTreeWidget()
        self.citation_tree.setHeaderHidden(True)
        self.citation_tree.itemDoubleClicked.connect(self.insert_snippet)
        dock_layout.addWidget(self.citation_tree)
        
        # Bottom Buttons (Import/Export)
        btn_layout = QHBoxLayout()
        
        self.btn_import_lib = QPushButton("导入")
        self.btn_import_lib.clicked.connect(self.import_citation_lib)
        self.btn_export_lib = QPushButton("导出")
        self.btn_export_lib.clicked.connect(self.export_citation_lib)
        
        # Add to layout in order: Toggle, Import, Export
        btn_layout.addWidget(self.btn_import_lib)
        btn_layout.addWidget(self.btn_export_lib)
        dock_layout.addLayout(btn_layout)
        
        self.citation_dock.setWidget(dock_widget)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.citation_dock)
        
        # Load saved visibility state (default to False/Hidden)
        settings = QSettings("Yingke", "LegalDocGen")
        is_visible = settings.value("citation_drawer_visible", False, type=bool)
        
        if is_visible:
            self.citation_dock.show()
            self.btn_toggle_citation.setText(">>")
        else:
            self.citation_dock.hide()
            self.btn_toggle_citation.setText("<<")
        
        self.load_legal_snippets()

    def toggle_citation_drawer(self):
        settings = QSettings("Yingke", "LegalDocGen")
        if self.citation_dock.isVisible():
            self.citation_dock.hide()
            self.btn_toggle_citation.setText("<<")
            settings.setValue("citation_drawer_visible", False)
        else:
            self.citation_dock.show()
            self.btn_toggle_citation.setText(">>")
            settings.setValue("citation_drawer_visible", True)

    def load_legal_snippets(self):
        self.citation_tree.clear() # Clear existing before loading
        try:
            import pandas as pd
            import os
            from src.utils import CITATION_DIR
            
            citation_dir = CITATION_DIR
            file_path = None
            if os.path.exists(citation_dir) and os.path.isdir(citation_dir):
                for f in os.listdir(citation_dir):
                    if not f.startswith('~$') and f.endswith(('.xlsx', '.xls', '.ods', '.csv')):
                        file_path = os.path.join(citation_dir, f)
                        break
                        
            if not file_path or not os.path.exists(file_path):
                return
                
            # Read without headers so the first row isn't accidentally skipped
            if file_path.endswith('.csv'):
                df = pd.read_csv(file_path, header=None)
            else:
                df = pd.read_excel(file_path, header=None)
            
            # Need at least 2 columns: Abstract (0), Content (1)
            if len(df.columns) < 2:
                return
                
            # Forward-fill empty abstracts (Column 0) so empty rows inherit the previous abstract
            df.iloc[:, 0] = df.iloc[:, 0].ffill()
            
            grouped = df.groupby(df.columns[0])
            citation_dict = {}
            for abstract_name, group in grouped:
                parent_item = QTreeWidgetItem(self.citation_tree, [str(abstract_name)])
                
                for _, row in group.iterrows():
                    content = str(row.iloc[1]) if pd.notna(row.iloc[1]) else ""
                    if not content.strip():
                        continue
                        
                    # Extract the first line to display as the child node name
                    first_line = content.splitlines()[0].strip() if content else "[空内容]"
                    
                    child_item = QTreeWidgetItem(parent_item, [first_line])
                    child_item.setData(0, Qt.ItemDataRole.UserRole, content)
                    # Add tooltip so they can see full text without double clicking if they want
                    child_item.setToolTip(0, content)
                    
                    # Add to dictionary for autocomplete
                    display_name = f"[{abstract_name}] {first_line}"
                    citation_dict[display_name] = content
                    
            self.citation_tree.expandAll()
            
            # Pass data to draft tab for autocomplete
            self.tab_draft.set_citation_data(citation_dict)
            
        except ImportError:
            pass # pandas or openpyxl missing
        except Exception as e:
            print(f"Error loading citation library: {e}")

    def import_citation_lib(self):
        import shutil
        import os
        from PyQt6.QtWidgets import QFileDialog, QMessageBox
        from src.utils import CITATION_DIR
        
        file_path, _ = QFileDialog.getOpenFileName(self, "导入引用库", "", "Table Files (*.xlsx *.xls *.ods *.csv)")
        if file_path:
            try:
                citation_dir = CITATION_DIR
                if not os.path.exists(citation_dir):
                    os.makedirs(citation_dir)
                    
                # Clear existing files in citation directory
                for f in os.listdir(citation_dir):
                    f_path = os.path.join(citation_dir, f)
                    if os.path.isfile(f_path):
                        os.remove(f_path)
                        
                # Copy new file with its original name
                filename = os.path.basename(file_path)
                dest_path = os.path.join(citation_dir, filename)
                shutil.copy2(file_path, dest_path)
                    
                self.load_legal_snippets()
                QMessageBox.information(self, "导入成功", "引用库已成功导入。")
            except Exception as e:
                QMessageBox.critical(self, "导入失败", f"无法导入文件: {e}")

    def export_citation_lib(self):
        import shutil
        import os
        from PyQt6.QtWidgets import QFileDialog, QMessageBox
        from src.utils import CITATION_DIR
        
        citation_dir = CITATION_DIR
        src_path = None
        if os.path.exists(citation_dir) and os.path.isdir(citation_dir):
            for f in os.listdir(citation_dir):
                if not f.startswith('~$') and f.endswith(('.xlsx', '.xls', '.ods', '.csv')):
                    src_path = os.path.join(citation_dir, f)
                    break
                    
        if not src_path:
            QMessageBox.warning(self, "导出失败", "当前没有可导出的引用库文件。")
            return
                
        ext = os.path.splitext(src_path)[1]
        original_filename = os.path.basename(src_path)
        dest_path, _ = QFileDialog.getSaveFileName(self, "导出引用库", original_filename, f"Table Files (*{ext})")
        
        if dest_path:
            try:
                shutil.copy2(src_path, dest_path)
                QMessageBox.information(self, "导出成功", "引用库已成功导出。")
            except Exception as e:
                QMessageBox.critical(self, "导出失败", f"无法导出文件: {e}")

    def on_focus_changed(self, old, new):
        if hasattr(new, 'insert') or hasattr(new, 'insertPlainText'):
            # Do not track our own search box
            if new != getattr(self, 'citation_search', None):
                self.last_text_input = new

    def filter_snippets(self, text):
        search_text = text.lower()
        
        for i in range(self.citation_tree.topLevelItemCount()):
            parent = self.citation_tree.topLevelItem(i)
            parent_match = False
            
            for j in range(parent.childCount()):
                child = parent.child(j)
                if search_text in child.text(0).lower():
                    child.setHidden(False)
                    parent_match = True
                else:
                    child.setHidden(True)
                    
            parent.setHidden(not parent_match and search_text not in parent.text(0).lower())
            if parent_match or search_text in parent.text(0).lower():
                parent.setExpanded(True)

    def insert_snippet(self, item, column):
        content = item.data(0, Qt.ItemDataRole.UserRole)
        if content and self.last_text_input:
            # Re-focus the original input field
            self.last_text_input.setFocus()
            if hasattr(self.last_text_input, 'insert'):
                self.last_text_input.insert(content)
            elif hasattr(self.last_text_input, 'insertPlainText'):
                self.last_text_input.insertPlainText(content)

    # --- PROJECT LIST DELEGATION (Wrapper around Model) ---
    def refresh_project_list(self):
        self.project_list.clear()
        projects = self.pm.get_project_list()
        for p in projects:
            self.project_list.addItem(p)

    def save_project_order(self):
        order = [self.project_list.item(i).text() for i in range(self.project_list.count())]
        self.pm.save_project_order(order)

    def create_new_project(self):
        
        name, ok = QInputDialog.getText(self, "新项目", "项目名称:")
        if ok and name:
            try:
                self.pm.create_project(name)
                self.refresh_project_list()
                QMessageBox.information(self, "成功", "项目已创建。")
            except Exception as e:
                QMessageBox.warning(self, "错误", str(e))

    def load_project(self, item):
        name = item.text()
        self.pm.load_project(name)
        
        # Enable relevant tabs
        self.tabs.setTabEnabled(0, True)
        self.tabs.setTabEnabled(1, True)
        self.tabs.setCurrentIndex(0)
        
        # Refresh UI components
        self.tab_draft.build_form()
        self.tab_settings.load_project_data()

    def restore_window_state(self):
        settings = QSettings("Yingke", "LegalDocGen")
        geometry = settings.value("mainwindow_geometry")
        state = settings.value("mainwindow_state")
        
        if geometry:
            self.restoreGeometry(geometry)
        if state:
            self.restoreState(state)

    def closeEvent(self, event):
        settings = QSettings("Yingke", "LegalDocGen")
        settings.setValue("mainwindow_geometry", self.saveGeometry())
        settings.setValue("mainwindow_state", self.saveState())
        super().closeEvent(event)

    def show_project_context_menu(self, pos):
        item = self.project_list.itemAt(pos)
        if not item: return

        if not item: return

        menu = QMenu(self)
        
        rename_action = QAction("重命名", self)
        rename_action.triggered.connect(lambda: self.rename_project(item))
        menu.addAction(rename_action)

        delete_action = QAction("删除", self)
        delete_action.triggered.connect(lambda: self.delete_project(item))
        menu.addAction(delete_action)

        menu.exec(self.project_list.mapToGlobal(pos))

    def rename_project(self, item):
        old_name = item.text()
        new_name, ok = QInputDialog.getText(self, "重命名", "新名称:", text=old_name)
        if ok and new_name and new_name != old_name:
            try:
                self.pm.rename_project(old_name, new_name)
                self.refresh_project_list()
                if self.pm.current_project_file:
                     # Reload UI just in case
                     pass
            except Exception as e:
                QMessageBox.critical(self, "错误", f"重命名失败: {e}")

    def delete_project(self, item):
        name = item.text()
        ret = QMessageBox.question(self, "确认删除", f"删除项目 '{name}'?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if ret == QMessageBox.StandardButton.Yes:
            try:
                self.pm.delete_project(name)
                self.refresh_project_list()
                
                # Disable tabs if current project was deleted
                # Logic in pm.delete_project handles clearing current_project_file
                if not self.pm.current_project_file:
                    self.tabs.setTabEnabled(0, False)
                    self.tabs.setTabEnabled(1, False)
                    # Switch to help or something? 
                    self.tabs.setCurrentIndex(2)
            except Exception as e:
                QMessageBox.critical(self, "错误", f"删除失败: {e}")
