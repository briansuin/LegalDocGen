from PyQt6.QtWidgets import QListWidget, QListWidgetItem, QApplication, QLineEdit, QTextEdit
from PyQt6.QtCore import Qt, QEvent, QPoint
from PyQt6.QtGui import QKeyEvent, QTextCursor

class SnippetCompleterPopup(QListWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        # Use ToolTip to avoid stealing focus on display, which triggers FocusOut and instantly hides itself
        self.setWindowFlags(Qt.WindowType.ToolTip | Qt.WindowType.FramelessWindowHint | Qt.WindowType.BypassWindowManagerHint)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setStyleSheet("""
            QListWidget {
                border: 1px solid #c0c0c0;
                background-color: white;
                font-size: 14px;
            }
            QListWidget::item {
                padding: 5px;
            }
            QListWidget::item:selected {
                background-color: #2196F3;
                color: white;
            }
        """)
        self.itemClicked.connect(self.on_item_clicked)
        self.hide()

        self.target_widget = None
        self.data_source = {}  # { "first_line": "full text" }
        self.current_query = ""
        
        # Max dimensions
        self.setMaximumHeight(200)
        self.setMinimumWidth(250)

    def set_data(self, data: dict):
        self.data_source = data

    def attach_to(self, widget):
        widget.installEventFilter(self)
        if isinstance(widget, QLineEdit):
            widget.textChanged.connect(lambda text=None, w=widget: self.on_text_changed(w))
        elif isinstance(widget, QTextEdit):
            widget.textChanged.connect(lambda w=widget: self.on_text_changed(w))

    def on_text_changed(self, widget):
        if not widget.hasFocus():
            return
            
        if isinstance(widget, QLineEdit):
            text = widget.text()
            cursor_pos = widget.cursorPosition()
        elif isinstance(widget, QTextEdit):
            text = widget.toPlainText()
            cursor_pos = widget.textCursor().position()
        else:
            return
            
        text_up_to_cursor = text[:cursor_pos]
        last_at_idx = text_up_to_cursor.rfind('@')
        
        if last_at_idx != -1:
            query = text_up_to_cursor[last_at_idx+1:]
            # Stop matching if there is a space, newline, etc.
            if ' ' in query or '\n' in query or '\t' in query:
                if self.isVisible() and self.target_widget == widget:
                    self.hide()
            else:
                self.target_widget = widget
                self.current_query = query
                self.update_list()
                if not self.isVisible() and self.count() > 0:
                    self.show_popup_at_cursor(widget)
        else:
            if self.isVisible() and self.target_widget == widget:
                self.hide()

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.FocusOut:
            if self.isVisible():
                from PyQt6.QtGui import QCursor
                from PyQt6.QtCore import QTimer
                if self.geometry().contains(QCursor.pos()):
                    # Don't hide if clicking on the popup itself (e.g., scrollbar or items)
                    # Restore focus back to the input field asynchronously
                    if self.target_widget:
                        QTimer.singleShot(0, self.target_widget.setFocus)
                    return False
                self.hide()
            return False

        if event.type() == QEvent.Type.KeyPress:
            if not getattr(obj, "isReadOnly", lambda: False)():
                if self.isVisible():
                    key = event.key()
                    if key in (Qt.Key.Key_Up, Qt.Key.Key_Down):
                        # Forward to list widget navigation
                        QApplication.sendEvent(self, event)
                        return True
                    elif key in (Qt.Key.Key_Enter, Qt.Key.Key_Return):
                        self.insert_selected_snippet()
                        return True
                    elif key == Qt.Key.Key_Escape:
                        self.hide()
                        return True

        return super().eventFilter(obj, event)

    def update_list(self):
        self.clear()
        query_lower = self.current_query.lower()
        
        for name, content in self.data_source.items():
            if query_lower in name.lower() or query_lower in content.lower():
                item = QListWidgetItem(name)
                item.setData(Qt.ItemDataRole.UserRole, content)
                item.setToolTip(content)
                self.addItem(item)
                
        if self.count() > 0:
            self.setCurrentRow(0)
            if self.target_widget and not self.isVisible():
                self.show_popup_at_cursor(self.target_widget)
        else:
            self.hide()

    def show_popup_at_cursor(self, widget):
        if not widget:
            return
            
        global_pos = QPoint(0, 0)
        
        if isinstance(widget, QLineEdit):
            cursor_rect = widget.cursorRect()
            global_pos = widget.mapToGlobal(cursor_rect.bottomLeft())
        elif isinstance(widget, QTextEdit):
            cursor_rect = widget.cursorRect()
            # Map the cursor rectangle to the viewport first, then globally
            global_pos = widget.viewport().mapToGlobal(cursor_rect.bottomLeft())
            
        # Adjust position slightly for visual padding
        global_pos.setY(global_pos.y() + 5)
        
        # Calculate width (match target widget width or min width)
        w = max(self.minimumWidth(), widget.width())
        self.setFixedWidth(w)
        
        self.move(global_pos)
        self.show()

    def on_item_clicked(self, item):
        self.insert_selected_snippet(item)

    def insert_selected_snippet(self, item=None):
        if not item:
            item = self.currentItem()
            
        if not item or not self.target_widget:
            self.hide()
            return

        content = item.data(Qt.ItemDataRole.UserRole)
        
        if isinstance(self.target_widget, QLineEdit):
            # QLineEdit does not support multi-line text nicely, replace newlines with spaces
            content = content.replace('\n', ' ').replace('\r', '')
            
            current_text = self.target_widget.text()
            cursor_pos = self.target_widget.cursorPosition()
            
            # Find the @ we just typed
            # Search backwards from cursor for '@'
            start_pos = current_text.rfind('@', 0, cursor_pos)
            
            if start_pos != -1:
                # Delete the '@query' part
                self.target_widget.setText(current_text[:start_pos] + content + current_text[cursor_pos:])
                self.target_widget.setCursorPosition(start_pos + len(content))
        
        elif isinstance(self.target_widget, QTextEdit):
            cursor = self.target_widget.textCursor()
            
            text = self.target_widget.toPlainText()
            cursor_pos = cursor.position()
            
            start_pos = text.rfind('@', 0, cursor_pos)
            if start_pos != -1:
                cursor.setPosition(start_pos, QTextCursor.MoveMode.KeepAnchor)
                cursor.removeSelectedText()
                cursor.insertText(content)
                self.target_widget.setTextCursor(cursor)

        self.hide()
        self.target_widget.setFocus()
