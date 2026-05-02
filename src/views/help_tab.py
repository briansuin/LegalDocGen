from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QHBoxLayout, QPushButton, QScrollArea
from PyQt6.QtCore import Qt

class HelpTab(QWidget):
    def __init__(self):
        super().__init__()
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Help Content
        help_text = """
        <h3>一、项目部分</h3>
        <p><b>1. 管理项目</b>：在左侧列表右键点击项目可进行重命名或删除。</p>
        <p><b>2. 导入模板</b>：在“模板与输入区设置”中添加模板文件（docx、odt格式），双击打开、编辑模板文件。</p>
        <p><b>3. 定义输入区</b>：在“输入区（表单）”部分设置需要填写的字段（如“名称”、“地址”等）。</p>
        <p><b>4. 字段映射</b>：复制字段的<b>ID</b>（例如 <code>“名称”</code>），然后双击打开模板，将带有大括号的<code>“{{名称}}”</code> 复制到指定的位置，用户完成信息填写后，程序会自动检索该字段并替换。</p>
        <p><b>5. 填写与生成</b>：在“填写内容”标签页输入信息，输入区不能空置，如不需要填写，可以输入"-"或空格。使用"Tab"键快速切换输入区，完成输入切换至底部绿色按钮后使用"Enter"键生成文档。</p>
        <p><b>6. 排序</b>：拖动项目、模板或输入区来调整顺序，系统会自动保存。</p>
        <h3>二、批量生成</h3>
        <p><b>1. 填写表格</b>：新建电子表格（xlsx、ods格式），第一行为标题，按列填写信息，如序号、姓名、性别（先生/女士）。</p>
        <p><b>2. 制作模板</b>：制作文档模板，如邀请函（docx、odt格式），并在需填写信息的位置设置映射字段，如{{姓名}}、{{性别}}。</p>
        <p><b>3. 文件生成设置</b>：在“文件选择”区上传已填写完成的表格与模板，设置“文件名组成列”及“前缀、后缀（如需）”。</p>
        <h3>三、引用库与智能联想</h3>
        <p><b>1. 引用库侧边栏</b>：点击主界面最右侧中间的 <code>&lt;&lt;</code> 按钮即可展开/收起引用库。你可以在这里：</p>
        <p><b>• 导入与导出</b>：支持导入任何包含两列数据以上的表格文件（xls, xlsx, ods, csv等）。表格第一列将会作为树状结构的“大类名称”，第二列则作为实际要插入的“全文内容”。内置搜索框可对内容进行全文快速检索；鼠标双击即可将全文插入到当前表单的光标位置。</p>
        <p><b>2. 键盘智能联想（@唤醒）</b>：</p>
        <p><b>• 极速填充</b>：在填写表单时（如“案由”、“诉讼请求”等输入框），直接在键盘上敲击 <b>@</b>（或Shift+2）键，光标正下方会立即弹出悬浮联想列表。</p>
        <p><b>• 精准检索</b>：在 @ 后接着输入关键词（如 <code>@指南</code> 或 <code>@新颖</code> ），列表会实时过滤出包含该关键词的大类或法条片段。</p>
        <p><b>• 一键上屏</b>：使用键盘的 <b>↑</b> <b>↓</b> 方向键选中目标，回车（Enter）确认，系统会自动将关联的几百字法条全文一键替换到输入框中，极大提高填写效率。</p>
        
        <hr>
        <h3>技术支持</h3> 
        <p><b>孙润波 律师</b> &nbsp;&nbsp; 北京市盈科（青岛）律师事务所</p>
        <p>Wechat: XXXXXXX &nbsp;&nbsp; Email: runbo.sun@gmail.com </p>
        <p style="text-align: right;">2026-02-27</p>
        """
        
        lbl_help = QLabel(help_text)
        lbl_help.setWordWrap(True)
        lbl_help.setAlignment(Qt.AlignmentFlag.AlignTop)
        lbl_help.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        
        # Style
        lbl_help.setStyleSheet("font-size: 12px; line-height: 1.5; padding: 20px;")
        
        # Wrap in QScrollArea
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QScrollArea.Shape.NoFrame)
        scroll_area.setWidget(lbl_help)
        
        layout.addWidget(scroll_area)
