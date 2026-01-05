from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QHBoxLayout, QPushButton
from PyQt6.QtCore import Qt

class HelpTab(QWidget):
    def __init__(self):
        super().__init__()
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Help Content
        help_text = """
        <h2>📚 使用说明</h2>
        <p><b>1. 管理项目</b>：在左侧列表右键点击项目可进行重命名或删除。</p>
        <p><b>2. 导入模板</b>：在“模板与输入区设置”中添加Word模板文件，双击打开、编辑 word 模板文件。</p>
        <p><b>3. 定义输入区</b>：在“输入区（表单）”部分设置需要填写的字段（如“名称”、“地址”等）。</p>
        <p><b>4. 字段映射</b>：您可以复制字段的<b>ID</b>（例如 <code>“名称”</code>），然后双击打开 Word 模板，将带有大括号的<code>“{{名称}}”</code> 复制到指定的位置，用户完成信息填写后，程序会自动检索该字段并替换。</p>
        <p><b>5. 填写与生成</b>：在“填写内容”标签页输入信息，输入区不能空置，如不需要填写，可以输入"-"或空格。使用"Tab"键快速切换输入区，完成输入切换至底部绿色按钮后使用"Enter"键生成文档。</p>
        <p><b>6. 排序</b>：您可以拖动项目、模板或输入区来调整顺序，系统会自动保存。</p>
        <hr>
        <h3>技术支持</h3>
        <p><b>孙润波 律师</b> &nbsp;&nbsp; 北京市盈科（青岛）律师事务所</p>
        <p>Wechat:  &nbsp;&nbsp; Email:  </p>
        <p style="text-align: right;">2026-01-04</p>
        """
        
        lbl_help = QLabel(help_text)
        lbl_help.setWordWrap(True)
        lbl_help.setAlignment(Qt.AlignmentFlag.AlignTop)
        lbl_help.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        
        # Style
        lbl_help.setStyleSheet("font-size: 14px; line-height: 1.5; padding: 20px;")
        
        layout.addWidget(lbl_help)
        layout.addStretch()
