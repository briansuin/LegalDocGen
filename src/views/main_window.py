from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QListWidget, QPushButton, QTabWidget, QSplitter,
                             QMenu, QMessageBox, QInputDialog)
from PyQt6.QtGui import QAction
from PyQt6.QtCore import Qt
from src.views.draft_tab import DraftTab
from src.views.settings_tab import SettingsTab
from src.views.help_tab import HelpTab

class MainWindow(QMainWindow):
    def __init__(self, project_manager):
        super().__init__()
        self.pm = project_manager
        
        self.setWindowTitle("盈科文书助手")
        self.setGeometry(100, 100, 1000, 700)
        
        self.setup_ui()
        self.refresh_project_list()

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
        self.tab_help = HelpTab()

        self.tabs.addTab(self.tab_draft, "📝 填写内容")
        self.tabs.addTab(self.tab_settings, "⚙️ 模板与输入区设置")
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
        splitter.addWidget(sidebar)
        splitter.addWidget(self.tabs)
        splitter.setSizes([200, 800])
        
        main_layout.addWidget(splitter)

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
