#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# @Author:wfeng007 小王同学
# @Date:2024-09-24 18:05:01
# @Last Modified by:wfeng007
#

#
# 小王的ai节点,快速提示词快速入口，投入ai吧！ANAN也是只狗狗。。。
# An AI Node of XiaoWang ， jumpin ! AnAn is a dog...
#
#

# pip install PySide6
# 一个提示符操作界面
# 可以快捷键唤起展示的；
# 支持钉在桌面最前端，全局热键换出与隐藏；
# TODO:托盘功能；
#   [ ]:基本托盘；
#   [ ]:托盘中提供：工作目录，关闭按钮；
# TODO 增加工作目录配置与维护，基本文件系统能力。
# 提供基本的提示发送与结果展示界面；
# 可支持多轮交互；
# 可支持富文本范围内容展示；
# 提供可切换的AI LLM/Agent的对接；
# 
#

# import win32gui
import sys, os,time
from typing import Callable
from PySide6.QtWidgets import (
    QApplication,
    QSystemTrayIcon,
    QFrame,
    QWidget,
    QScrollArea,
    QHBoxLayout,
    QVBoxLayout,
    QSizePolicy,
    QLineEdit,
    QPushButton,
    QTextBrowser,
    QLabel,
    QStyleOption,QMenu
)
from PySide6.QtGui import (
    QKeySequence,
    QShortcut,
    QAction,
    QTextDocument,
    QTextCursor,
    QMouseEvent,
    QPainter,
    QColor,
    QIcon,QGuiApplication,
    QImage,QPixmap,
)
from PySide6.QtCore import Qt, QEvent, QObject, QSize,QThread,Signal,Slot
# from PySide6.QtWebEngineWidgets import QWebEngineView

# from PyQt5.QtWidgets import (
#         QApplication, QFrame,QWidget,
#         QHBoxLayout,QVBoxLayout,QSizePolicy,
#         QLineEdit ,QPushButton,
#         QLabel,QShortcut,QAction
#         )
# from PyQt5.QtGui import QKeySequence
# from PyQt5.QtCore import Qt, QEvent,QObject
# from PyQt5.QtWebEngineWidgets import QWebEngineView
# import global_hotkeys as hotkey
from pynput import keyboard


# ai
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate

import time

# 加载环境变量 #openai 的key读取
from dotenv import load_dotenv, find_dotenv

# except (ModuleNotFoundError, ImportError):
#     print(
#         "python库导导入失败。 \n"
#         "")
#     sys.exit(0)

__version__ = "0.1.0"
_ = load_dotenv(find_dotenv())  # 读取本地 .env 文件，里面定义了 OPENAI_API_KEY
 

# 基本config信息，剥离出可配置项
class AnanxwJumpinConfig:     
    MSGSHOWINGPANEL_QSS="""
    QFrame {
        border: 1px solid #ccc;
        border-radius: 5px;
        background-color: #f9f9f9;
    }
    QTextBrowser {
        background-color: #e0e0e0;
        border: 1px solid #ccc;
        border-radius: 3px;
        padding: 5px;
    }
    QTextBrowser[contentOwnerType="ROW_CONTENT_OWNER_TYPE_USER"] {
        background-color: #e0e0e0;
        margin-left: 200px; /* 模拟右对齐，实际最好脚本中用layout实现对齐； */
    }
    QTextBrowser[contentOwnerType="ROW_CONTENT_OWNER_TYPE_AGENT"] {
        background-color: #e6e6fa;
        color: #00008b;
    }
    
    """
    
    MAIN_WINDOWS_QSS ="""
    QWidget#jumpin_main_window {
        /*background-color: #d4f2e7; 这个是特殊背景，用来调试界面样式*/
        background-color: #fff;
        border-radius: 10px;
    }
    """


class AAXWSimpleAIConnAgent:
   
    """
    连接LLM/Agent的工具类，支持流式获取响应。
    """

    def __init__(self, api_key: str=None, model_name: str = "gpt-4o-mini"):
        """
        初始化OpenAI连接代理。
        
        :param api_key: OpenAI API密钥。
        :param model_name: 使用的模型名称。
        """
        if api_key is None:
            self.llm = ChatOpenAI(streaming=True, model_name=model_name,temperature=0)
        else:
            self.llm = ChatOpenAI(openai_api_key=api_key, streaming=True, model_name=model_name,temperature=0)
    #
    def send_request(self, prompt: str, func: Callable[[str], None]):
        """
        发送请求到LLM，并通过回调函数处理流式返回的数据。
        
        :param prompt: 提供给LLM的提示文本。
        :param callback: 用于处理每次接收到的部分响应的回调函数。
        """
        templateStr="""
        你的额名字AnAn jumpin是一个AI入口助理;
        请关注用户跟你说的内容，和善的回答用户，与用户要求。
        如果用户说的不明确，请提示用户可以说的更明确。
        请用纯文本来回答，可以在段落后面增加<br/>标签。
        以下是用户说的内容：
        {message}
        """
        template = PromptTemplate.from_template(templateStr)
        
        # for token in self.llm.stream(template.format(message=prompt)):
            
        #     if 'choices' in token and len(token['choices']) > 0 and 'text' in token['choices'][0]:
        #         text = token['choices'][0]['text']
        #         func(text)
        # 在流式模式下，每次迭代都会返回一部分文本
        # 每次返回都执行回调
        for msgChunk in self.llm.stream(template.format(message=prompt)):
            if msgChunk is not None and msgChunk.content != '':
                time.sleep(0.1)
                func(msgChunk.content)
                
# 线程异步处理AI IO任务。
class AIhread(QThread):
    
    #[x]FIXME 这里不应该专递递函数，而是直接在run中执行，需要更新界面的部分才emit出去。
    #newContent,id 对应：ShowingPanel.appendToContentById 等回调
    updateUI = Signal(str,str)  

    def __init__(self,text:str,uiCellId:str,llmagent:AAXWSimpleAIConnAgent):
        super().__init__()
        
        # self.mutex = QMutex()
        self.text:str=text
        self.uiId:str=uiCellId
        self.llmagent:AAXWSimpleAIConnAgent=llmagent
        
    def run(self):
        self.msleep(500)  # 执行前先等界面渲染
        # self.mutex.lock()
        print(f"thread inner str:{self.text} \n")
        self.llmagent.send_request(self.text, self.callUpdateUI)
        # self.mutex.unlock()
        
    def callUpdateUI(self,newContent:str):
        # print(f"streaming, emitL{newContent} id:{self.uiId}")
        
        #
        # 最好强制类型转换。self.uiId:str 或 str(self.uiId)
        # 
        self.updateUI.emit(str(newContent), str(self.uiId)) 
        


##
# 操作钩子，侦听回调；
##
#
# ***blocker这样的过滤器，如果在类中的方法执行，则需要保存为属性。
# 框架wieght.installEventFilter()时，并不会保持这个对象，只是获取其eventFilter方法。
# [ ]:eventFilter 如果只有input需要也可以考虑直接在需要的Input中实现？
class TabBlocker(QObject):
    """
    拦截 Tab 键，并替换为特定的功能；主要作用于InputEdit；
    Tab:
    """

    def __init__(self, mainWindow):
        super().__init__()
        print("TabBlocker 初始化")
        self.manwindow: AAXWJumpinMainWindow = mainWindow

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.KeyPress and event.key() == Qt.Key.Key_Tab:
            print("Tab 键被按下，但被TabBlocker过滤")
            self.manwindow.funcButtonLeft.click()  # 点击左侧按钮
            return True  # 被过滤
        return False

class AAXWJumpinInputLineEdit(QLineEdit):
    """ """

    def __init__(self, mainWindow, parent=None):
        super().__init__(parent)
        self.mainWindow: AAXWJumpinMainWindow = mainWindow
        self._initMouseProperties()

    # 定制化 PromptInputLineEdit key输入回调
    def keyPressEvent(self, event):

        # tab
        # self.input_box.hasFocus() and
        if event.key() == Qt.Key_Tab:
            self.on_tab_pressed()
            event.ignore()
        else:
            # 调用父类的 keyPressEvent 处理其他按键事件
            super().keyPressEvent(event)

            # 检查是否按下了上下左右箭头键
            if event.key() == Qt.Key_Up:
                self.on_up_pressed()
            elif event.key() == Qt.Key_Down:
                self.on_down_pressed()
            elif event.key() == Qt.Key_Left:
                self.on_left_pressed()
            elif event.key() == Qt.Key_Right:
                self.on_right_pressed()

    #
    # input相关基本行为封装
    #
    def on_tab_pressed(self):
        # 在这里实现你的功能
        print("Tab 键被按下")
        # 示例：清空文本框内容
        self.mainWindow.funcButtonLeft.click()

    def on_up_pressed(self):
        # 在这里实现向上的功能
        print("向上箭头键被按下")

    def on_down_pressed(self):
        # 在这里实现向下的功能
        print("向下箭头键被按下")

    def on_left_pressed(self):
        # 在这里实现向左的功能
        print("向左箭头键被按下")

    def on_right_pressed(self):
        # 在这里实现向右的功能
        print("向右箭头键被按下")

    ##
    # TODO:这个鼠标按下移动的功能要优化。输入框有输入文字的局域可能会冲突。需要考虑在实际input外面加个面板，input自适应。
    # class AutoWidthLineEdit(QLineEdit):
    #     def __init__(self, parent=None):
    #         super().__init__(parent)
    #         self.textChanged.connect(self.adjustWidth)
    #         self.setAlignment(Qt.AlignLeft) #左对齐

    #     def adjustWidth(self):
    #         fm = QFontMetrics(self.font())
    #         width = fm.boundingRect(self.text()).width() + 10  # 加上一些额外的边距
    #         self.setFixedWidth(width)

    # 鼠标事件的捕获，操作；
    # 单签提供：鼠标按住input可以移动主窗口；
    ##
    def _initMouseProperties(self):
        self.setMouseTracking(True)
        self.is_dragging = False
        self.drag_start_pos = None

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self.is_dragging = True
            self.drag_start_pos = event.globalPosition().toPoint()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        if self.is_dragging:
            if self.drag_start_pos:
                delta = event.globalPosition().toPoint() - self.drag_start_pos
                self.window().move(self.window().pos() + delta)
                self.drag_start_pos = event.globalPosition().toPoint()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self.is_dragging = False
            self.drag_start_pos = None
        super().mouseReleaseEvent(event)

    # def mousePressEvent(self, event):
    #     if event.button() == Qt.LeftButton:
    #         self.is_dragging = True
    #         self.drag_start_pos = event.globalPos()
    #     else:
    #         super().mousePressEvent(event)

    # def mouseMoveEvent(self, event):
    #     if self.is_dragging:
    #         if self.drag_start_pos:
    #             delta = event.globalPos() - self.drag_start_pos
    #             self.window().move(self.window().pos() + delta)
    #             self.drag_start_pos = event.globalPos()
    #     else:
    #         super().mouseMoveEvent(event)

    # def mouseReleaseEvent(self, event):
    #     if event.button() == Qt.LeftButton:
    #         self.is_dragging = False
    #         self.drag_start_pos = None
    #     super().mouseReleaseEvent(event)


class AAXWVBoxLayout(QVBoxLayout):
    """
    定制化layout：
        addWidgetAtTop()可以顶部追加Row；
    """

    def addWidgetAtTop(self, widget):
        """
        在布局的顶部添加一个部件，并展示。
        """
        item_list = [self.takeAt(0) for _ in range(self.count())]

        self.insertWidget(0, widget)
        for item in item_list:
            if item.widget():
                self.addWidget(item.widget())
            else:
                self.addItem(item)


class AAXWScrollPanel(QFrame):  # 暂时先外面套一层QFrame
    """
    垂直方向以列表样式，可追加内容的展示面板；
    内容所在Row部件会根据内容调整高度；
    内部聚合了vbxlayout，增加content时默认使用TextBrowser用作Row展示。
    提供了为RowContent追加内容的方式，支持流式获取文本追加到Row中。
    """
    
    DEFAULT_STYLE = """ 
    QTextBrowser {
        background-color: #a0a0a0;
        border: 1px solid #ccc;
        border-radius: 5px;
        padding: 5px;
    }
    QFrame {
        border: 1px solid #ccc;
        border-radius: 5px;
        background-color: #f9f9f9;
    }
    """

    # }

    def __init__(self, mainWindow: "AAXWJumpinMainWindow", qss:str=DEFAULT_STYLE ,parent=None):
        """
        当前控件展示与布局结构：
        AAXWScrollPanel->QVBoxLayout->QScrollArea->QWidget(scrollWidget)-> TB等
        """
        super().__init__(parent)
        self.mainWindow = mainWindow
        self.setFrameShape(QFrame.StyledPanel)
        # self.setFrameShadow(QFrame.Raised) #阴影凸起
        self.setStyleSheet(qss)

        # 主要设定可垂直追加的Area+Layout
        # 结构顺序为scroll_area->scroll_widget->scroll_layout
        self.scrollArea = QScrollArea()  # ScrollArea 聊天内容展示区域
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scrollArea.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scrollWidget = (
            QWidget()
        )  # 其实scrollWidget就是断开与内部的联动，转而hint复合外层？
        # scrollArea-scrollWidget
        self.scrollArea.setWidget(self.scrollWidget)
        self.scrollLayout: AAXWVBoxLayout = AAXWVBoxLayout(self.scrollWidget)
        # self.scrollLayout = QVBoxLayout(self.scrollWidget)
        self.scrollLayout.setAlignment(Qt.AlignTop)  # 设置加入的部件为顶端对齐

        # 可直接控制scroll_widget来控制尺寸等？
        # 使用scroll_layout来添加元素，应用布局；

        # 外部widget添加布局
        layout = QVBoxLayout(self)
        layout.addWidget(self.scrollArea)  # 加上外部的scroll_area

    # 用特殊符号最为追加站位标记
    MARKER = "[💬➡️🏁]"
    ROW_BLOCK_NAME_PREFIX = "row_block_name"
    # 区分展示内容行的类型
    ROW_CONTENT_OWNER_TYPE_USER="ROW_CONTENT_OWNER_TYPE_USER"
    ROW_CONTENT_OWNER_TYPE_AGENT="ROW_CONTENT_OWNER_TYPE_AGENT"
    ROW_CONTENT_OWNER_TYPE_SYSTEM="ROW_CONTENT_OWNER_TYPE_SYSTEM"
    
    def addRowContent(self, content, rowId, contentOwner="unknown", 
                      contentOwnerType=ROW_CONTENT_OWNER_TYPE_SYSTEM ,isAtTop=True):
        """
        在scrollLayout上添加一个内容行，默认使用QTextBrowser。
        默认在顶端加入；
        """

        # 添加 QTextBrowser 并设置 objectName 和自定义属性 id
        tb = QTextBrowser()
        tb.setObjectName(
            f"{self.ROW_BLOCK_NAME_PREFIX}_{rowId}"
        )  # message row background
        tb.setProperty("id", rowId)
        tb.setProperty("contentOwner", contentOwner)
        tb.setProperty("contentOwnerType", contentOwnerType)
        # 高度先限定，然后根据内部变化
        tb.setVerticalScrollBarPolicy(
            Qt.ScrollBarAlwaysOff
        )  # 可以暂时设置为不出现tb级别滚轮
        tb.setHorizontalScrollBarPolicy(
            Qt.ScrollBarAlwaysOff
        )  # 可以暂时设置为不出现tb级别滚轮
        # tb.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        #
        # 默认文本等内容
        # 使用TextDocument来写入内容。
        doc = QTextDocument()
        tb.setDocument(doc)

        # TODO 初始化tb大小等

        ###
        # 连接文档内容变化信号与调整大小的槽函数
        ###
        tb.document().contentsChanged.connect(lambda: self._adjustRowBlockSize(tb))
        #
        
        # 设置文本变更调整;
        initial_text = content
        doc.setHtml(initial_text)
        tb.append(self.MARKER)  # 这里增加一个追加内容用的特别Marker
        #


        # 一般写法 self.scroll_layout.addWidget(tb)
        if isAtTop:
            self.scrollLayout.addWidgetAtTop(tb)  # 这里每次在头部加layout定制了
        else:
            self.scrollLayout.addWidget(tb)

    #  支持流式写入内容
    def appendToContentById(self, text, rowId: str):
        """
        在指定Rowid的Row中追加内容
        """
        # 查找对应的 QTextBrowser 并追加内容
        tb: QTextBrowser = self.scrollWidget.findChild( #TODO 这个搜索子控件的写法是否要优化？
            QTextBrowser, f"{self.ROW_BLOCK_NAME_PREFIX}_{rowId}"
        )  # 用名字查找元素
        if tb is not None:
            current_text = tb.toHtml()
            # print("-" * 20)
            # print(current_text)
            # 问题# tb.setHtml(current_text + text) #会重新解析html，写如text并按照原有内容的html样式融入。
            # 问题# tb.append(text) #会遵循之前的html，跟current_text + text效果类似

            # 使用游标进行查找marker并更新平文
            doc = tb.document()
            cursor: QTextCursor = doc.find(self.MARKER)
            if cursor:
                cursor.movePosition(
                    QTextCursor.MoveOperation.PreviousCharacter,
                    QTextCursor.MoveMode.MoveAnchor,
                )
                # cursor.insertText(text) #这个是按照平文方式来写，会把标签转义为转义字符形式。
                cursor.insertHtml(
                    f"{text}"
                )  # 可以追加html但是会过滤掉不符合规范的比如div
                tb.repaint()#非线程调用本方法，可能每次都要重绘，否则是完成完后一次性刷新。
            else:
                print("not found marker:" + self.MARKER)
        else:
            print("not found tb by name:" + f"{self.ROW_BLOCK_NAME_PREFIX}_{rowId}")

    # 
    # Panel的内部基于scroll-widget增加组件后的期望尺寸；
    def expectantHeight(self):

        # 关键点是Panel，scrollArea的实际大小与 self.scrollArea.widget() 提供的大小即内部期望的大小是不一样的。
        # 默认Panel或scrollArea是根据外部来设定大小的。
        sws = self.scrollArea.widget().size()
        total_height = 0

        # TODO: 简单大致计算一下margin，实际在外层vboxlayout中增加的部件都要计算
        rmargins = self.scrollLayout.contentsMargins()
        total_height += rmargins.top() + rmargins.bottom()
        smargins = self.layout().contentsMargins()
        total_height += smargins.top() + smargins.bottom()
        #

        total_height += sws.height()
        # print(f"expectantHeight:{total_height}")
        return total_height
        pass

    def scrollWidgetSize(self):
        return self.scrollArea.widget().size()

    # 定义调整 QTextBrowser 大小的槽函数
    def _adjustRowBlockSize(self, changedTextBrowser):

        # 重新计算内部尺寸 #从上往下重新触发绘制计算，保证Hint等计算适当。
        # self.updateGeometry() #似乎没效果

        # 在主窗口的中心 widget（容器 widget）中查找 QTextBrowser
        # 实际可以参考 这个查找代码：text_browser = self.centralWidget().findChild(QTextBrowser)
        tb:QTextBrowser = changedTextBrowser
        # 获取 QTextBrowser 的文档对象
        doc = tb.document()
        # 获取 QTextBrowser 的内容边距
        margins = tb.contentsMargins()
        #  计算文档高度加上上下边距得到总高度
        # TODO 这里计算的不对，所有tb都需要根据内容来计算高度，获取内容应该。
        expectantHeight = (
            doc.size().height() + margins.top() + margins.bottom() + 10 #预期行高增加1行？
        )  # 多增加点margins

        # 设置 QTextBrowser 高度对应到size策略
        # 设置 QTextBrowser 的最小高度为计算得到的总高度
        # text_browser.setMinimumHeight(height)
        # 设置 QTextBrowser 的最大高度也为计算得到的总高度
        # text_browser.setMaximumHeight(height)

        # fixed对应fixed策略
        # 调整Row tb高度
        if expectantHeight<20: expectantHeight=20
        tb.setFixedHeight(expectantHeight)
        self.mainWindow.adjustHeight()

    #
    # 事件过滤器，需要时可以install到外部大窗口上。
    # 默认可能也不用，防止外部窗口也上下拉动。
    def eventFilter(self, obj, event):
        if obj is self and event.type() == QEvent.Type.Resize:
            # 调整 QTextBrowser 的大小
            self._adjustRowBlockSize() #会调整所有tb的大小。这里用的是setFixedHeight
            return True
        return super().eventFilter(obj, event)

    # def addWidget(self,qw:Widgt):
    #     super().add

    pass  # AAXWScrollPanel


class AAXWJumpinMainWindow(QWidget):
    """
    主窗口:
        包含所有组件关联：
    """
    
    MAX_HEIGHT = 500
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.installTabBlocker()
        self.installAppHotKey()
        self.llmagent=AAXWSimpleAIConnAgent()
    

    
    def init_ui(self):
        
        self.setObjectName("jumpin_main_window")
        self.setStyleSheet(AnanxwJumpinConfig.MAIN_WINDOWS_QSS)
        # self.repaint()
        
        # 界面主布局，垂直上下布局；
        mainVBoxLayout = QVBoxLayout()  

        # 输入用组件套装的容器布局
        # 输入操作面板 水平布局
        inputKitLayout = QHBoxLayout()
        inputKitLayout.setContentsMargins(5, 5, 5, 5)  # 设置外边距
        inputKitLayout.setSpacing(5)  # 设置组件之间的间距

        # 组件定义

        #
        # 定义输入操作面板
        # 左侧功能按钮
        self.funcButtonLeft = QPushButton("Toggle", self)
        self.funcButtonLeft.clicked.connect(self.toggleLeftFunc)

        # 中间输入框
        self.promptInputEdit = AAXWJumpinInputLineEdit(self)
        self.promptInputEdit.setPlaceholderText("输入提示或指令")
        self.promptInputEdit.setStyleSheet("border: 1px solid gray; padding: 5px;")
        self.promptInputEdit.returnPressed.connect(self.enterClicked)  # 绑定回车事件

        # 右侧功能按钮
        self.funcButtonRight = QPushButton("⏎", self)
        self.funcButtonRight.clicked.connect(self.rightButtonClicked)

        # 展示面板
        # 创建 QWebEngineView
        # self.showingPanelWebView = QWebEngineView(parent=self) #跟影藏动作冲突？ visble
        msgShowingPanel=AnanxwJumpinConfig.MSGSHOWINGPANEL_QSS
        self.msgShowingPanel = AAXWScrollPanel(mainWindow=self, qss=msgShowingPanel,parent=self)
        
        #
        # 组件到主布局
        inputKitLayout.addWidget(self.funcButtonLeft)
        # 竖线分割线
        # main_layout.addStretch()
        inputKitLayout.addWidget(self._createAcrossLine())
        # promptKitLayout.addLayout(self.input_layout)
        inputKitLayout.addWidget(self.promptInputEdit)
        inputKitLayout.addWidget(self._createAcrossLine())
        inputKitLayout.addWidget(self.funcButtonRight)

        # 设置窗口的布局
        mainVBoxLayout.addLayout(inputKitLayout)
        mainVBoxLayout.addWidget(self._createAcrossLine(QFrame.Shape.HLine))
        mainVBoxLayout.addWidget(self.msgShowingPanel)  # showing panel
        self.setLayout(mainVBoxLayout)

        # 主窗口设置
        self.setWindowTitle("快捷键唤起输入框")
        # self.setGeometry(300, 300, 600, 120)
        self.setMinimumSize(600, 120)  # 限定大小
        self.setMaximumSize(600, self.MAX_HEIGHT)
        # self.setWindowFlags(Qt.WindowType.Tool | Qt.WindowType.FramelessWindowHint)
        self.setWindowFlags(self.windowFlags()|Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        # self.setWindowFlags( Qt.WindowType.Dialog)
        # self.setWindowFlags(Qt.WindowStaysOnTopHint) #多次唤起会卡住，需要关闭。
        # self.setWindowModality(Qt.WindowModality.ApplicationModal)

        # 设置窗口大小策略
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)

        # 初始高度为 200 像素
        # self.setFixedHeight(200) #这个应该跟随整元素吧。 不设置高度限制？设置为不能人工设定高度即可？
        # self.showingPanelWebView.setFixedHeight(200) #

        # 初始焦点在input上
        self.promptInputEdit.setFocus()

        # self.showText()
    #
    # TODO 之后还是改为主窗口中加1个widget作为伪主窗口的面板，基于此定制以及绘制异形主窗口。
    #      暂时使用重绘简单实现。
    def paintEvent(self, event):    
        #为主窗口 绘制圆角 这里只取了qss的背景色
        
        # qss获取
        opt = QStyleOption()
        opt.initFrom(self) #加载自己对应qss
        # 获取 QSS 中定义的背景颜色
        bg_color = opt.palette.window().color()
        ##
        
        #绘制
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        rect = self.rect()
        # painter.setBrush(QColor(255, 255, 255)) 
        painter.setBrush(bg_color) 
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(rect, 20, 20)
    #   
    # ui初始化 end
    ##

    ##
    # 装载关联快捷键
    # 或特殊按键处理器
    ##
    def installAppHotKey(self):
        # 创建一般快捷键

        # 一般快捷键关闭（临时） install installEventFilter
        shortcut = QShortcut(QKeySequence("Alt+c"), self)  # 这里已经关联self
        shortcut.activated.connect(self.closeWindow)  # 不要加括号，指向方法；


    def installTabBlocker(self):
        #
        self.blocker = TabBlocker(self)
        self.promptInputEdit.installEventFilter(self.blocker)

    #
    # 关联安装全局过滤器GlobalHotkeyFilter 监听事件
    #
    ##
    # 装载关联快捷键
    # 或特殊按键处理器
    # end
    ##

    ###
    # 主界面或主要控件，基本行为封装
    # input行为除外；
    ###
    def toggleLeftFunc(self):
        # 切换显示文本还是Unicode字符
        if self.funcButtonLeft.text() == "Toggle":
            self.showUnicode()
        else:
            self.showText()

    def showText(self):
        # 显示空文本
        self.funcButtonLeft.setText("Toggle")

    def showUnicode(self):
        # 显示Unicode字符笑脸
        self.funcButtonLeft.setText("😊")

    def enterClicked(self):
        # 处理回车事件
        print("Enter key pressed!")
        self.funcButtonRight.click()

    
    def rightButtonClicked(self):
        print("Right button clicked!")

        text = self.promptInputEdit.text()
        rid = int(time.time() * 1000)
        self.msgShowingPanel.addRowContent(
            content=text, rowId=rid, contentOwner="user_xiaowang",
            contentOwnerType=AAXWScrollPanel.ROW_CONTENT_OWNER_TYPE_USER,
        )
        
        rrid = int(time.time() * 1000)
        self.msgShowingPanel.addRowContent(
            content="", rowId=rrid, contentOwner="assistant_aaxw",
            contentOwnerType=AAXWScrollPanel.ROW_CONTENT_OWNER_TYPE_AGENT,
        )
        
        #
        #生成异步处理AI操作的线程
        #注入要用来执行的ai引擎以及 问题文本+ ui组件id
        #FIXME 执行时需要基于资源，暂时锁定输入框；
        #TODO 多重提交，多线程处理还没很好的做，会崩溃；
        self.thread = AIhread(text,rrid,self.llmagent)
        # 绑定界面更新的回调方法
        self.thread.updateUI.connect(self.msgShowingPanel.appendToContentById) 
        # 启动
        self.thread.start()
        #
        
        #同步方式调用: 界面会hang住。
        # self.llmagent.send_request(text, 
        #             lambda content:self.msgShowingPanel.appendToContentById(content,rrid ))
        #
        
        self.promptInputEdit.clear()
        self._logInput()

    def _logInput(self):
        # 打印输入框中的内容
        print(f"Input: {self.promptInputEdit.text()}")

    def toggleHidden(self):
        if not self.isHidden():
 
            self.setStaysOnTop(isToOn=False)
            self.hide()
        else:
            # self.setVisible(True)
            self.setStaysOnTop(isToOn=True)
            self.show()
            self.promptInputEdit.setFocus()
            # self.raise_() # 
            # self.activateWindow() #也会有点影像

            # self.promptInputEdit.setFocus()


    ##
    # 切换钉在最前台 功能
    ##  
    def toggleStaysOnTop(self):
        if self.windowFlags() & Qt.WindowType.WindowStaysOnTopHint:
            self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowStaysOnTopHint)
        else:
            self.setWindowFlags(
                self.windowFlags() | Qt.WindowType.WindowStaysOnTopHint
            )
    def setStaysOnTop(self,isToOn=True):
        #设置on 且 还没有flag
        if isToOn and (self.windowFlags() & Qt.WindowType.WindowStaysOnTopHint) == 0:
            self.setWindowFlags(
                self.windowFlags() | Qt.WindowType.WindowStaysOnTopHint
            )
            return True
        #设置off 且 已有flag
        elif not isToOn and self.windowFlags() & Qt.WindowType.WindowStaysOnTopHint:
            self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowStaysOnTopHint)
            return True
        return False
    # 钉在最前台功能结束
    #
    
    
    
    # 关闭窗口方法
    def closeWindow(self):
        self.close()

    # def show_window(self):
    #     self.show()

    #
    #       根据内部部件大小调整主窗口自身大小；还是本来就有这个设置？
    def adjustHeight(self):

        # print(f"showing panel  height :{self.msgShowingPanel.height()}")

        newHeight = (
            self.sizeHint().height()
            - self.msgShowingPanel.sizeHint().height() + self.msgShowingPanel.expectantHeight()
        )

        if newHeight > self.MAX_HEIGHT: newHeight = self.MAX_HEIGHT
        # print(f"adjustHeight new:{newHeight}")
        # print(f"showing panel H :{self.msgShowingPanel.sizeHint()}")
        # print(f"showing panel - scroll H :{self.msgShowingPanel.scrollArea.sizeHint()}")
        # print(f"showing panel - scroll-widget sizeHint :{self.msgShowingPanel.scrollArea.widget().sizeHint()}")
        # print(f"showing panel - scroll-widget Size :{self.msgShowingPanel.scrollArea.widget().size()}")
        # print(f"showing panel - scroll-widget-vboxlayout H :{self.msgShowingPanel.scrollArea.widget().layout().sizeHint()}")

        self.resize(self.width(), newHeight)
        # self.setFixedHeight(newHeight)
        pass

    # TODO: 修改为类静态方法即可。
    def _createAcrossLine(self, shape: QFrame.Shape = QFrame.Shape.VLine):
        # 垂直线 VL 水平线 HL
        assert shape in [
            QFrame.Shape.VLine,
            QFrame.Shape.HLine,
        ], "shape 必须是 QFrame.Shape.VLine 或 QFrame.Shape.HLine"
        line = QFrame()
        line.setFrameShape(shape)  # 设置为垂直线
        line.setFrameShadow(QFrame.Shadow.Sunken)  # 设置阴影效果
        return line


class AAXWGlobalShortcut:
    # 全局快捷键 运行器
    def __init__(self, mainWindow: AAXWJumpinMainWindow):
        self.mainWindow: AAXWJumpinMainWindow = mainWindow
        self.hotkey = keyboard.GlobalHotKeys({"<alt>+z": self.on_activate})

    def on_activate(self):
        print("全局快捷键<alt>+z被触发")
        self.mainWindow.toggleHidden()

    def start(self):
        self.hotkey.start()
        # self.widget.show()
        # sys.exit(self.app.exec())

    def stop(self):
        self.hotkey.stop()

class AAXWJumpinTrayKit(QSystemTrayIcon):
    def __init__(self, main_window:AAXWJumpinMainWindow):
        super().__init__()
        
        self.setToolTip("ANANXW Jumpin!")
        
        # self.setIcon(QIcon("icon.png"))
        qimg:QImage=self._get32QImg("./icon.png")
        pixmap = QPixmap.fromImage(qimg) #QIcon 可接受QPixmap；用QImage有问题。
        self.setIcon( QIcon(pixmap))
        
        self.menu = QMenu()
        self.show_main_action = self.menu.addAction("切换展示主界面(ALT+Z)")
        self.close_main_action = self.menu.addAction("关闭ANANXW(ALT+C)")
        self.setContextMenu(self.menu)
        self.show_main_action.triggered.connect(self.toggleHiddenMainWindow)
        self.close_main_action.triggered.connect(self.closeMainWindow)
        
        # 添加打开指定目录的菜单选项
        self.open_directory_action = self.menu.addAction("工作目录")
        self.open_directory_action.triggered.connect(self.open_directory)
        
        self.mainWindow:AAXWJumpinMainWindow = main_window
        
    
    def toggleHiddenMainWindow(self):
        self.mainWindow.toggleHidden()

    def closeMainWindow(self):
        #这里是不是应该关闭窗口外同时关闭app：app.quit()
        #FIXME 如果主窗口是hidden状态，则不能退出，或者偶尔不能退出。
        self.mainWindow.closeWindow()
        
        
    
    def open_directory(self):
        # 这里指定要打开的目录路径
        # directory_path = "./"
        # 打开当前程序所在目录
        current_directory = os.path.dirname(os.path.abspath(sys.argv[0]))
        directory_path=current_directory
        if os.path.exists(directory_path):
            os.startfile(directory_path)
        else:
            print(f"指定的目录不存在：{directory_path}")
    
        
    def _get32QImg(self,image_path):
        
        #
        # 直接用QImage  改变尺寸 scaled_qimage = qimage.scaled(32, 32)
        #
        # # 使用 QImage 从文件读入
        qimage = QImage(image_path)
        # 改变尺寸
        scaled_qimage = qimage.scaled(8, 8)
        qimg=scaled_qimage
        return qimg
    



def main():
    try:
        app = QApplication(sys.argv)
        window = AAXWJumpinMainWindow()
        tray=AAXWJumpinTrayKit(window)
        gst = AAXWGlobalShortcut(window)
        gst.start()
        tray.show()
        window.show()
        window.raise_()
        sys.exit(app.exec())
    except Exception as e:  # 如果不用处理e 可以简化为except Exception: 或 except: 即可
        print("except")
        print("Exception:", e)
    finally:
        gst.stop()


if __name__ == "__main__":
    main()
    pass


##
# 遗留代码，待删除；
##
...