import sys
from PyQt6.QtWidgets import QApplication
from src.models import ProjectManager
from src.views.main_window import MainWindow

def main():
    app = QApplication(sys.argv)
    
    # 1. Initialize Model
    project_manager = ProjectManager()
    
    # 2. Initialize View
    window = MainWindow(project_manager)
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
