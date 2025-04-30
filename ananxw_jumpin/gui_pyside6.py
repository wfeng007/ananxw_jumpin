#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""GUI组件模块"""

import os
import sys
import json
import logging
import traceback
import markdown
from typing import List, Dict, Any, Union, Optional, cast, TYPE_CHECKING, Type, Callable, Tuple, TypeVar, Protocol
from abc import ABC, abstractmethod
from functools import wraps

try:
    from typing import override
except ImportError:
    from typing_extensions import override

from PySide6.QtCore import (
    Qt, QEvent, QObject, QThread, Signal, QTimer, QSize, QPoint,
    QRegularExpression, QMutex, QRunnable, QThreadPool, Slot,
)
from PySide6.QtWidgets import (
    QApplication, QSystemTrayIcon, QFrame, QWidget, QScrollArea,
    QHBoxLayout, QVBoxLayout, QSizePolicy, QLineEdit, QPushButton,
    QTextBrowser, QStyleOption, QMenu, QPlainTextEdit, QLabel, QToolBar,
    QStackedWidget, QButtonGroup, QLayout,
)
from PySide6.QtGui import (
    QKeySequence, QShortcut, QTextDocument, QTextCursor, QMouseEvent,
    QPainter, QIcon, QImage, QPixmap, QTextOption, QSyntaxHighlighter,
    QTextCharFormat, QColor
)

from qfluentwidgets import (
    NavigationInterface, NavigationItemPosition, NavigationAvatarWidget, NavigationTreeWidget,
    NavigationPushButton, MessageBoxBase, SubtitleLabel, LineEdit, CaptionLabel, PushButton,
    BodyLabel, TextWrap, CardWidget, StrongBodyLabel, PlainTextEdit, TextEdit, TextBrowser,
    SegmentedWidget, ComboBox, CheckBox, FlowLayout, InfoBar, InfoBarPosition, EditableComboBox,
    PillPushButton, PrimaryPushButton,
    NavigationWidget, MessageBox, SettingCardGroup, SwitchSettingCard, FolderListSettingCard,
    OptionsSettingCard, PushSettingCard, HyperlinkCard, PrimaryPushSettingCard, ScrollArea,
    ComboBoxSettingCard, ExpandLayout, Theme, CustomColorSettingCard, RadioButton, IconWidget,
    setTheme, setThemeColor, RangeSettingCard, isDarkTheme, ConfigItem, SettingCard, qrouter
)
from qfluentwidgets import FluentIcon as FIF

from pynput import keyboard

from . import __version__
from .comm import AAXW_JUMPIN_LOG_MGR, AAXWJumpinDICUtilz
from .backbone import (
    AAXWJumpinConfig, AAXWDependencyContainer, AAXWAbstractApplet,
    AAXWJumpinHistoriedMemory, AAXWJumpinFileAIMemoryManager,
    AAXWAbstractAIConnOrAgent, AAXWJumpinAppletManager, ConfigurableAIConnOrAgent
)

# 模块日志器
# 本模块，模块日志器
AAXW_JUMPIN_MODULE_LOGGER:logging.Logger=AAXW_JUMPIN_LOG_MGR.getModuleLogger(
    module=sys.modules[__name__])

##
# 界面组件相关
##
#
@AAXW_JUMPIN_LOG_MGR.classLogger()
class AAXWJumpinInputLineEdit(QLineEdit):
    """ 
    主要指令，提示信息，对话信息输入框； 
    """

    AAXW_CLASS_LOGGER:logging.Logger


    def __init__(self, mainWindow, parent=None):
        super().__init__(parent)
        self.mainWindow: AAXWJumpinMainWindow = mainWindow
        
        
        # 初始化鼠标事件，主要完抓握InputEdit移动整体窗口
        self._initMouseProperties()


    # 定制化 PromptInputLineEdit key输入回调
    # TODO: 是否应该将ctrl/alt 按下后再按字母键的这种情况过先过滤掉？防止额外输入本来的快捷操作。
    def keyPressEvent(self, event):

        #对于LineEdit，如果用EventFilter这块无效。
        # if event.key() == Qt.Key_Tab:
        #     self.on_tab_pressed() 
        #     event.ignore()
        
        # 调用父类的 keyPressEvent 处理其他按键事件
        super().keyPressEvent(event)

        # 检查是否按下了上下左右箭头键
        if event.key() == Qt.Key.Key_Up:
            self.onUpPressed()
        elif event.key() == Qt.Key.Key_Down:
            self.onDownPressed()
        elif event.key() == Qt.Key.Key_Left:
            self.onLeftPressed()
        elif event.key() == Qt.Key.Key_Right:
            self.onRightPressed()

    #
    # input相关基本行为封装
    #
    def onUpPressed(self):
        # 在这里实现向上的功能
        self.AAXW_CLASS_LOGGER.debug("向上箭头键被按下")

    def onDownPressed(self):
        # 在这里实现向下的功能
        self.AAXW_CLASS_LOGGER.debug("向下箭头键被按下")

    def onLeftPressed(self):
        # 在这里实现向左的功能
        self.AAXW_CLASS_LOGGER.debug("向左箭头键被按下")

    def onRightPressed(self):
        # 在这里实现向右的功能
        self.AAXW_CLASS_LOGGER.debug("向右箭头键被按下")

    ##
    # TODO:这个鼠标按下移动的功能要优化。输入框有输入文字的局域可能会冲突。需要考虑在实际input外面加个面板，input自适应。
    #   同时，也需要封装一个完整的复合的InputKit包含左右工具按钮组，以及可能的浮动提示框等界面；
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
        self.isDragging = False #抓握拖动状态
        self.dragStartPos = None

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self.isDragging = True
            self.dragStartPos = event.globalPosition().toPoint()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        if self.isDragging:
            if self.dragStartPos:
                delta = event.globalPosition().toPoint() - self.dragStartPos
                self.window().move(self.window().pos() + delta)
                self.dragStartPos = event.globalPosition().toPoint()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self.isDragging = False
            self.dragStartPos = None
        super().mouseReleaseEvent(event)


@AAXW_JUMPIN_LOG_MGR.classLogger()
class AAXWJumpinInputPanel(QWidget):
    AAXW_CLASS_LOGGER:logging.Logger
    
    # sendRequest = Signal(str)



    def __init__(self, mainWindow:'AAXWJumpinMainWindow',parent):
        super().__init__(parent=parent)
        self.mainWindow = mainWindow
        self.init_ui()

    def init_ui(self):
        # 输入用组件套装的容器布局
        # 输入操作面板 水平布局
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        #
        # 定义输入操作面板
        # 左侧功能按钮
        self.funcButtonLeft = QPushButton("Toggle", self)
        # 中间输入框
        self.promptInputEdit = AAXWJumpinInputLineEdit(self.mainWindow, self)
        # 右侧功能按钮
        self.funcButtonRight = QPushButton("⏎", self)

        layout.addWidget(self.funcButtonLeft)
        layout.addWidget(self._createAcrossLine())
        layout.addWidget(self.promptInputEdit)
        layout.addWidget(self._createAcrossLine())
        layout.addWidget(self.funcButtonRight)

        # 使用 AAXWJumpinConfig 中定义的 INPUT_PANEL_STYLE
        self.setStyleSheet(AAXWJumpinConfig.INPUT_PANEL_QSS)

        # 为 promptInputEdit 设置样式
        self.promptInputEdit.setStyleSheet("; ".join([f"{k}: {v}" for k, v in AAXWJumpinConfig.INPUT_EDIT_QSS_DICT.items()]))
        
        # 确保输入面板本身也有背景色
        self.setStyleSheet(f"{AAXWJumpinConfig.INPUT_PANEL_QSS}; background-color: #f9f9f9;")

        #操作信号曹，需要挂到外部；
        self.funcButtonLeft.clicked.connect(self.toggleLeftFunc) #组件默认实现；
        # self.funcButtonRight.clicked.connect(self.rightButtonClicked)
        self.promptInputEdit.returnPressed.connect(self.enterClicked)


    ###
    # 基本行为封装
    ###
    # 左侧
    def toggleLeftFunc(self):
        pass


    # TODO 抽取到controller或applet中
    def enterClicked(self):
        # 处理回车事件
        self.AAXW_CLASS_LOGGER.debug("Enter key pressed!")
        self.funcButtonRight.click()
        pass

    # 右侧
    def rightButtonClicked(self):
        self.AAXW_CLASS_LOGGER.debug("Right button clicked!")



    def _createAcrossLine(self, shape: QFrame.Shape = QFrame.Shape.VLine):
        line = QFrame()
        line.setFrameShape(shape)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        return line


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


#TODO 这个类族是个策略模式，但是感觉是否应该简化？
#           就是支持 AAXWScrollPanel的，至少contentOwnerType 是。contentOwner。
#           Content 就是指内容。实际是否可以改造为create 特定的界面？比如配置界面？
# 相当于type3注入ContentBlock。
class AAXWContentBlockStrategy(ABC):
   
    @abstractmethod
    def createWidget(self, rowId: str, contentOwner: str, contentOwnerType: str,
                    mainWindow: QWidget, strategyWidget:QWidget) -> QWidget:
        pass

    @abstractmethod
    def initContent(self,widget: QWidget,content:str) -> QWidget:
        pass

    @abstractmethod
    def insertContent(self,widget: QWidget,content:str):
        pass

    # @abstractmethod
    # def adjustSize(self,widget: QWidget): #这个有用？
    #     pass

# TODO 需支持plaintext/unknown 以及其他结构。
class AAXWCodeHighlighter(QSyntaxHighlighter):
    def __init__(self, parent=None):
        super().__init__(parent) #type: ignore
        self.highlightingRules = []

        # 设置关键字高亮规则
        keywordFormat = QTextCharFormat()
        keywordFormat.setForeground(QColor("#569CD6"))
        keywords = ["def", "class", "for", "if", "else", "elif", "while", "return", "import", "from", "as", "try", "except", "finally"]
        for word in keywords:
            pattern = QRegularExpression(r'\b' + word + r'\b')
            self.highlightingRules.append((pattern, keywordFormat))

        # 设置字符串高亮规则
        stringFormat = QTextCharFormat()
        stringFormat.setForeground(QColor("#CE9178"))
        self.highlightingRules.append((QRegularExpression("\".*\""), stringFormat))
        self.highlightingRules.append((QRegularExpression("'.*'"), stringFormat))

        # 设置注释高亮规则
        commentFormat = QTextCharFormat()
        commentFormat.setForeground(QColor("#6A9955"))
        self.highlightingRules.append((QRegularExpression("#.*"), commentFormat))

    @override
    def highlightBlock(self, text):
        for pattern, format in self.highlightingRules:
            expression = QRegularExpression(pattern)
            it = expression.globalMatch(text)
            while it.hasNext():
                match = it.next()
                self.setFormat(match.capturedStart(), match.capturedLength(), format)

class AAXWCodeBlockWidget(QWidget): #QWidget有站位，但是并不绘制出来。
    def __init__(self, code, title="Unkown", parent=None):
        super().__init__(parent)
        self.sizeChangedCallbacks = []
        self.title = title

        self.setStyleSheet("""
            CodeBlockWidget {
                background-color: #1E1E1E;
                border-radius: 5px;
                /* overflow: hidden; qss不支持 */
                /* border: 2px solid #FF00FF;  添加特殊颜色的边框用于调试 */
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 顶部按钮布局
        topWidget = QWidget()
        topWidget.setFixedHeight(30)
        topWidget.setStyleSheet("""
            background-color: #5D5D5D;
            border: none;
            border-top-left-radius: 5px;
            border-top-right-radius: 5px;
            border-bottom-left-radius: 0px;
            border-bottom-right-radius: 0px;
        """)
        topLayout = QHBoxLayout(topWidget)
        topLayout.setContentsMargins(10, 2, 10, 2)

        # 添加标题标签
        self.titleLabel = QLabel(self.title)
        self.titleLabel.setStyleSheet("""
            color: #FFA500; 
            font-family: 'Courier New', monospace;
            font-size: 16px;
            font-weight: bold;
        """) #亮橙色
        topLayout.addWidget(self.titleLabel)

        topLayout.addStretch()
        
        # 创建复制按钮
        copy_button = QPushButton("复制")
        copy_button.setFixedHeight(20)  # 控制高度为30
        copy_button.setStyleSheet(f"""
            background-color: #ED6A5E;
            border: 1px solid #1E1E1E;
            border-radius: 3px;
        """)
        copy_button.clicked.connect(self.copy_to_clipboard)  # 连接点击事件
        topLayout.addWidget(copy_button)

        # 其他按钮
        for color in ['#F4BF4F', '#61C554']:  # 黄、绿按钮
            button = QPushButton()
            button.setFixedSize(20, 20)
            button.setStyleSheet(f"""
                background-color: {color};
                border: 1px solid #1E1E1E;
                border-radius: 3px;
            """)
            topLayout.addWidget(button)
        
        layout.addWidget(topWidget)

        # 修改代码编辑器的设置
        self.codeEdit = QPlainTextEdit()
        self.codeEdit.setReadOnly(True)
        self.codeEdit.setStyleSheet("""
            QPlainTextEdit {
                background-color: #1E1E1E;
                color: #D4D4D4;
                border: none;
                font-family: 'Courier New', monospace;
                font-size: 12px;
                border-radius: 0px;
            }
        """)
        self.codeEdit.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)  # 禁用自动换行
        self.codeEdit.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        #不需要垂直滚动条
        self.codeEdit.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.codeEdit.setPlainText(code)
        layout.addWidget(self.codeEdit)

        # 应用代码高亮
        self.highlighter = AAXWCodeHighlighter(self.codeEdit.document())

        # 底部空白区域
        bottomWidget = QWidget()
        bottomWidget.setFixedHeight(30)
        bottomWidget.setStyleSheet("""
            background-color: #5D5D5D;
            border: none;
            border-top-left-radius: 0px;
            border-top-right-radius: 0px;
            border-bottom-left-radius: 5px;
            border-bottom-right-radius: 5px;
        """)
        layout.addWidget(bottomWidget)

        # self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        # self.codeEdit.textChanged.connect(self.adjustHeight)

        #会基于sizeHint调整；
        self.codeEdit.textChanged.connect(self.adjustSize)
    
    def copy_to_clipboard(self):
        """复制内容到剪贴板并更新按钮状态"""
        clipboard = QApplication.clipboard()
        content_to_copy = self.codeEdit.toPlainText()  # 获取代码编辑器的完整内容
        clipboard.setText(content_to_copy)

        # 更新按钮状态
        button:QPushButton = self.sender()  # 获取触发信号的按钮 #type:ignore
        button.setText("已复制")
        button.setEnabled(False)  # 禁用按钮

        # 3秒后恢复按钮状态
        QTimer.singleShot(1000, lambda: self._restore_button(button))

    def _restore_button(self, button):
        """恢复按钮状态"""
        button.setText("复制")
        button.setEnabled(True)

    def setTitle(self, title):
        self.title = title
        self.titleLabel.setText(title)

    def registerSizeChangedCallbacks(self, callback):
        self.sizeChangedCallbacks.append(callback)
    def _triggerSizeChanged(self):
        for callback in self.sizeChangedCallbacks:
            callback()
    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._triggerSizeChanged()

    def adjustSize(self) -> None:
        # self.setFixedSize(self.sizeHint())
        qs=self.sizeHint()
        self.setFixedHeight(qs.height())


    
    def expectantHeight(self)->int:

        #根据

        # 获取行数
        lineCount = self.codeEdit.blockCount()
        
        # 获取单行高度（假设所有行高度相同）
        metrics = self.codeEdit.fontMetrics()
        lineHeight = metrics.lineSpacing()
        
        # 计算文本内容的总高度
        contentHeight = (lineCount+1) * lineHeight
        
        # 获取顶部和底部区域的高度
        topHeight = 30  # 顶部区域高度
        bottomHeight = 30  # 底部区域高度
        
        # 添加冗余高度
        padding = 20  # 额外的冗余高度
        
        # 计算总高度
        totalHeight = topHeight + contentHeight + bottomHeight + padding
        
        return totalHeight

    def sizeHint(self): #重写 预期尺寸
        width = self.width()
        height = self.expectantHeight()
        return QSize(width, height)
    
@AAXW_JUMPIN_LOG_MGR.classLogger(level=logging.INFO)
class AAXWCompoMarkdownContentBlock(QFrame): #原来是QWidget
    """ 
    复合的内容展示块；
    - 可展示连续输出的的markdown格式内容，特定显示程序块形式的内容。
    """
    AAXW_CLASS_LOGGER:logging.Logger

    MIN_HEIGHT = 50  # 设置一个最小高度

    # 基础QSS样式
    BASE_QSS = """
    /* */
    AAXWCompoMarkdownContentBlock {
        background-color: #f0f0f0;
        border: none ;
        border-radius: 5px;
    }
    AAXWCompoMarkdownContentBlock[contentOwnerType="ROW_CONTENT_OWNER_TYPE_USER"] {
        border: 1px solid #a0a0a0;
        background-color: #d4f2e7; 
        margin-left: 200px; /* 模拟右对齐，实际最好脚本中用layout实现对齐； */
    }
    AAXWCompoMarkdownContentBlock[contentOwnerType="ROW_CONTENT_OWNER_TYPE_USER"] > QTextBrowser {
        background-color: #d4f2e7; 
    }

    """

    # md的基本 CSS 样式
    MARKDOWN_CONTENT_CSS = """
    <style>
        body {
            font-family: "Microsoft YaHei", Arial, sans-serif;
            line-height: 1.1;
            padding: 10px;
        }
        /* ... 其他样式保持不变 ... */
        table {
            border-collapse: collapse;
            width: 100%;
        }
        th, td {
            border: 1px solid #ddd;
            padding: 8px;
            text-align: left;
        }
        th {
            background-color: #f2f2f2;
        }
    </style>
    """
    #
    # 内部类包装TB
    #
    class MarkdownInnerTextBrowser(QTextBrowser):
        
        def __init__(self, parent=None):
            super().__init__(parent)
            self.sizeChangedCallbacks = [] #当尺寸变化时回调

            self.setOpenExternalLinks(True)
            self.setStyleSheet("""
                border: 1px solid #f0f0f0;
                border-radius: 5px;
            """)
            self.setWordWrapMode(QTextOption.WrapMode.WrapAtWordBoundaryOrAnywhere)
            self.setLineWrapMode(QTextBrowser.LineWrapMode.WidgetWidth)
            self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

            # self.setMinimumHeight(30)  # 设置一个最小高度
            # self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
            self.setFixedHeight(50)# 设置一个最小高度

            
            # 连接文档内容变化信号到调整方法
            # self.document().contentsChanged.connect(self.adjustHeight)
            self.document().contentsChanged.connect(self.adjustSize)
        
        def registerSizeChangedCallbacks(self, callback):
            self.sizeChangedCallbacks.append(callback)
        def _triggerSizeChanged(self):
            for callback in self.sizeChangedCallbacks:
                callback()
        def resizeEvent(self, event):
            super().resizeEvent(event)
            self._triggerSizeChanged()
        

        def adjustSize(self) -> None:
            qs=self.sizeHint()
            # self.resize(qs)
            # self.setFixedSize(qs) #宽度会混乱
            self.setFixedHeight(qs.height())

        def _expectantHeight(self)->int:
            # 计算文档的实际高度
            doc_height = self.document().size().height()
            # 添加一些额外的空间，比如为了显示滚动条
            extra_space = 20
            # 设置新的高度
            new_height = doc_height + extra_space
            # 确保高度不小于最小高度
            new_height = max(int(new_height), 50)
            return new_height

        def sizeHint(self):
            # 返回一个基于内容的建议大小
            width = self.viewport().width()
            height = self._expectantHeight()  # 额外的空间
            return QSize(width, int(height))
            
    ## 内部类包装TB end

    def __init__(self, parent=None):
        super().__init__(parent)
        self.contentChangeCallbacks = []
        self.sizeChangedCallbacks = [] #当尺寸变化时回调
        self.currentContent = ""
        self.currentLine = ""
        self.isInCodeBlock = False
        self.initUi()
        # self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.addContent(" ") #初始化当前currentWidget  之后要改写
        

    def initUi(self):
        """初始化UI组件"""
        self.setMinimumHeight(self.MIN_HEIGHT)

        self.layout = QVBoxLayout(self) #type:ignore
        self.layout.setContentsMargins(1, 1, 1, 1)
        self.layout.setSpacing(1)
        
        # 初始化当前显示组件
        self.currentWidget = None
       
        # 应用基础样式
        self.setStyleSheet(self.BASE_QSS)
        
    
    def registerSizeChangedCallbacks(self, callback):
        self.sizeChangedCallbacks.append(callback)
    def _triggerSizeChanged(self):
        for callback in self.sizeChangedCallbacks:
            callback()
    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._triggerSizeChanged()

    
    def registerContentChangeCallback(self, callback):
        #这个是挂载在 内部TB或codeblock等底层展示框中回调；
        #比如：newWidget.codeEdit.textChanged.connect(self._triggerContentChange)
        #     newWidget.document().contentsChanged.connect(self._triggerContentChange)
        self.contentChangeCallbacks.append(callback)

    def _triggerContentChange(self):
        for callback in self.contentChangeCallbacks:
            callback()

    def addContent(self, content):
        """添加内容到显示区域"""

        procContent=content

        # TODO 如果content有回车或多个回车考虑以回车阶段进行循环执行。
        #      STREAM方式一般不是长句；
        #
        # 生成新的self.currentLine 作为指令或判断；
        # procContent为当前正在处理的传入。
        # 查找第一个回车
        newline_index = procContent.find('\n')
        if newline_index == -1:
            # 如果没有回车，全部拼接到currentLine
            # 大部分是这种
            self.currentLine += procContent 
        else:
            # 如果有回车，拼接到第一个回车（包含）
            self.currentLine += procContent[:newline_index + 1]
            # remaining_content = procContent[newline_index + 1:]

        # 根据line去处理当前处理内容
        self._processLine(procContent)
        
        # 如果line最后是回车说明之后是新的一行，充值currentLine
        if '\n' in self.currentLine:
            self.currentLine=""
        # 处理1条line完成；


    def _processLine(self, procContent):

        #命令与分类判断
        line=self.currentLine; 
        # print(f"_processLine line:{line}")
        self.AAXW_CLASS_LOGGER.debug(f"line: {line}")

        """处理单行内容"""
        if line.strip().startswith("```python"):
            self.AAXW_CLASS_LOGGER.debug("发现代码块!!")
            
            # 回溯已展示的 指令部分文本
            self.handleMarkdownContent(
                    procContent=procContent, 
                    isBacktrack=True,backtrackTemplate="```python"
            )
            self.handleCodeBlockStart(procContent)
        elif line.strip() == "```" and self.isInCodeBlock:
            # 回溯已展示的 指令部分文本
            self.appendToCodeBlock(
                    procContent=procContent, 
                    isBacktrack=True,backtrackTemplate="```"
            )
            self.AAXW_CLASS_LOGGER.debug("代码块关闭!!")
            self.handleCodeBlockEnd()
        elif self.isInCodeBlock:
            self.appendToCodeBlock(procContent)
        else:
            # self._checkForSpecialMarkers(line)
            self.handleMarkdownContent(procContent)
            
        # 处理完成后，将当前行添加到currentContent
        # self.currentContent += line


    def handleCodeBlockStart(self, procContent):
        """处理代码块开始"""
        self.isInCodeBlock = True
        code = self.currentLine.split("```python", 1)[1].strip()
        #可优
        title = "```python"
        title = title.split('```', 1)[1] if len(title.split('```', 1)) > 1 else title
        #
        newWidget = AAXWCodeBlockWidget(code,title=title)
        self.layout.addWidget(newWidget)
        self.currentWidget = newWidget
        self.currentContent = ""+code
        self.currentLine= ""+code
        # 
        newWidget.codeEdit.textChanged.connect(self._triggerContentChange)
        newWidget.registerSizeChangedCallbacks(self.adjustSize)

    def handleCodeBlockEnd(self):
        """处理代码块结束"""
        self.isInCodeBlock = False
        newWidget = self.MarkdownInnerTextBrowser()
        self.layout.addWidget(newWidget)
        self.currentWidget = newWidget
        self.currentContent = ""
        self.currentLine= ""
        newWidget.document().contentsChanged.connect(self._triggerContentChange)
        newWidget.registerSizeChangedCallbacks(self.adjustSize)

    def handleMarkdownContent(self, procContent,isBacktrack=False, backtrackTemplate=None):
        """处理Markdown内容"""
        if not isinstance(self.currentWidget, self.MarkdownInnerTextBrowser):
            newWidget = self.MarkdownInnerTextBrowser()
            self.layout.addWidget(newWidget)
            self.currentWidget = newWidget
            self.currentContent = ""
            self.currentLine= ""
            #其实就是当前组件的内容变更时触发动作；
            newWidget.document().contentsChanged.connect(self._triggerContentChange)
            newWidget.registerSizeChangedCallbacks(self.adjustSize)

        self.currentContent += procContent
        if isBacktrack:
            if not backtrackTemplate:raise ValueError(
                "template_str cannot be empty when is_backtrack is True")
            self.currentContent = self.currentContent.rsplit(backtrackTemplate, 1)[0]

        htmlContent = markdown.markdown(self.currentContent, extensions=['extra', 'codehilite'])
        fullHtml = f"{self.MARKDOWN_CONTENT_CSS}<body>{htmlContent}</body>"
        self.currentWidget.setHtml(fullHtml)
        self.currentWidget.moveCursor(QTextCursor.MoveOperation.End)
        self.currentWidget.ensureCursorVisible()

    def appendToCodeBlock(self, procContent, isBacktrack=False, backtrackTemplate=None):
        """向代码块追加内容"""
        if isinstance(self.currentWidget, AAXWCodeBlockWidget):
            self.currentContent += procContent
            if isBacktrack:
                if not backtrackTemplate: raise ValueError(
                    "template_str cannot be empty when is_backtrack is True")
                self.currentContent = self.currentContent.rsplit(backtrackTemplate, 1)[0]
            self.currentWidget.codeEdit.setPlainText(self.currentContent)
            self.currentWidget.codeEdit.moveCursor(QTextCursor.MoveOperation.End)

        else:
            self.AAXW_CLASS_LOGGER.debug("警告：当前不在代码块中，但收到了代码块内容")

    def clear(self):
        """清除所有内容"""
        for i in reversed(range(self.layout.count())): 
            widget = self.layout.itemAt(i).widget()
            if widget is not None:
                widget.deleteLater()
        self.currentWidget = self.MarkdownInnerTextBrowser()
        self.layout.addWidget(self.currentWidget)
        self.isInCodeBlock = False
        self.currentContent = ""
        self.currentLine = ""

    # def adjustHeight(self):
    #     """调整组件高度"""
    #     # 使用 sizeHint() 获取建议的高度
    #     suggested_height = self.sizeHint().height()
    #     # print(f"CompoMarkdownContentBlock.adjustHeight {suggested_height}")
    #     # 设置新的固定高度
    #     self.setFixedHeight(suggested_height)

    def adjustSize(self) -> None:
        # self.resize(self.sizeHint())
        qs=self.sizeHint()
        self.setFixedHeight(qs.height())

    def sizeHint(self):
        # 返回一个基于内容的建议大小
        width = self.width()

        height = 0
        for i in range(self.layout.count()):
            widget = self.layout.itemAt(i).widget()
            if widget:
                height += widget.sizeHint().height()
        height += self.layout.spacing() * (self.layout.count() - 1)
        margins = self.layout.contentsMargins()
        height += margins.top() + margins.bottom()

        return QSize(width, max(height, self.MIN_HEIGHT))

        

# 不放置容器，直接applet等生成，设置给panel
class AAXWJumpinCompoMarkdownContentStrategy(
    AAXWContentBlockStrategy):
    # Markdown 语法提示，可用AI提示词
    MARKDOWN_PROMPT = """
    本对话支持以下 Markdown 语法：
    - 标题：使用 # 号（支持 1-6 级标题）
      例如：# 一级标题
            ## 二级标题
    - 文本：这是普通文本
    - 粗体：**粗体文本**
    - 斜体：*斜体文本*
    - 删除线：~~删除线文本~~
    - 链接：[链接文本](URL)
    - 图片：![替代文本](图片URL)
    - 列表：
      无序列表使用 - 
      有序列表使用 1. 2. 3. 
    - 代码：
      行内代码：`代码`
      代码块：使用 ```语言名 和 ``` 包裹
    - 表格：使用 | 分隔列，使用 - 分隔表头
      例如：
      | 列1 | 列2 | 列3 |
      |-----|-----|-----|
      | A1  | B1  | C1  |
    - 引用：> 引用文本
    - 分割线：---
    - 任务列表：
      - [ ] 未完成任务
      - [x] 已完成任务

    Markdown 语法 注意：
    1. Markdown 中使用单个换行不会产生新段落，如需新段落请使用两个换行。
    2. 部分复杂格式（如表格内的样式）可能无法完全支持。
    3. 代码块会使用特殊的格式和语法高亮显示，当前暂时仅支持python，其他代码格式先用普通文本提供。
    """

    # @staticmethod
    @override
    def createWidget(self,rowId: str, contentOwner: str, contentOwnerType: str, 
                     mainWindow: 'AAXWJumpinMainWindow', strategyWidget: 'AAXWScrollPanel') -> AAXWCompoMarkdownContentBlock:
        
        mdBlock = AAXWCompoMarkdownContentBlock()
        mdBlock.setObjectName(f"{AAXWScrollPanel.ROW_BLOCK_NAME_PREFIX}_{rowId}")
        mdBlock.setProperty("id", rowId)
        mdBlock.setProperty("contentOwner", contentOwner)
        mdBlock.setProperty("contentOwnerType", contentOwnerType)

        #根据contentOwnerType提供不同的展示：
        # mdBlock.

        # 当内容变更时调整控件尺寸，这里主要是高度；
        # 注册内容变化的回调
        # mdBlock.registerContentChangeCallback(
        #     lambda: CompoMarkdownContentStrategy.adjustSize(mdBlock) #
        # )
        # 尺寸变化时回调；
        mdBlock.registerSizeChangedCallbacks(
             lambda: self.onSizeChanged(mdBlock) #
        )

        # 设置属性以便后续操作
        mdBlock.setProperty("mainWindow", mainWindow)
        mdBlock.setProperty("strategyWidget", strategyWidget)

        # 先写入点东西
        mdBlock.addContent(" \n")

        return mdBlock

    # @staticmethod
    @override
    def initContent(self,widget: AAXWCompoMarkdownContentBlock, content: str):

        # widget.clear()
        widget.addContent(content)
        # qs:QSize=widget.currentWidget.sizeHint() #type:ignore

        # 由于主线程有sleep会阻碍重绘，导致曹方法失效；（主要是方法 ）
        # 如果曹方法失效
        # 1秒钟后（保证展示出来后）重绘1次大小
        QTimer.singleShot(1000, widget.currentWidget.adjustSize)#type:ignore
        # 马上调用没用。
        # widget.currentWidget.adjustSize()

    # @staticmethod
    @override
    def insertContent(self,widget: AAXWCompoMarkdownContentBlock, content: str):
        widget.addContent(content)

    # @staticmethod
    def onSizeChanged(self,widget: AAXWCompoMarkdownContentBlock):
        # 为啥一下子高度就满了？
        # 调整主窗口高度
        mainWindow: "AAXWJumpinMainWindow" = widget.property("mainWindow")
        if mainWindow:
            mainWindow.adjustHeight()

    # @staticmethod
    @override
    def adjustSize(self,widget: AAXWCompoMarkdownContentBlock):
        # widget.adjustSize()

        # # 调整主窗口高度
        # mainWindow: "AAXWJumpinMainWindow" = widget.property("mainWindow")
        # if mainWindow:
        #     mainWindow.adjustHeight()
        pass








##
# 界面异步处理相关
##
#资源互斥锁，多线程中使用。
class QTimeoutMutexLocker:
    def __init__(self, mutex: QMutex,_verboseName=None, timeout_ms: int = 3000):
        '''
        互斥锁超时锁
        timeoutMs =-1 表示永久等待
        '''
        self.mutex = mutex
        self.timeout = timeout_ms
        self.locked = False
        self._verboseName=_verboseName
        
    def __enter__(self):
        self.locked = self.mutex.tryLock(self.timeout)
        if self._verboseName and self.locked:
            print(f"QTimeoutMutexLocker:获取锁成功：{self._verboseName}")
        if self._verboseName and not self.locked:
            print(f"QTimeoutMutexLocker:获取锁失败：{self._verboseName}")
        return self.locked
        
    def __exit__(self, *args):
        if self.locked:
            self.mutex.unlock()
            if self._verboseName:
                print(f"QTimeoutMutexLocker:已解锁 {self._verboseName}")

class QThreadSafeResourceRegistry:
    """线程安全资源-锁绑定管理器"""


    class ThreadSafeMethod(Protocol):
        _isThreadSafe: bool
        _resourceId: str
        def __call__(self, *args: Any, **kwargs: Any) -> Any: ...
    
    T = TypeVar('T', bound=Callable)


    def __init__(self):
        """初始化装饰器管理器"""
        self._mutexRegistry: Dict[str, QMutex] = {}
        self._registryMutex = QMutex()  # 保护注册表的互斥锁

    def getMutex(self, resourceId: str) -> QMutex:
        """获取或创建资源的互斥锁"""
        with QTimeoutMutexLocker(self._registryMutex):
            if resourceId not in self._mutexRegistry:
                self._mutexRegistry[resourceId] = QMutex()
            return self._mutexRegistry[resourceId]

    def safeOperation(self, resourceId: str, timeoutMs: int = 3000):
        """创建线程安全的方法装饰器
        主要通过装饰资源的操作方法，对资源进行线程加锁完成线程安全保护。
        """
        def decorator(method: QThreadSafeResourceRegistry.T) -> QThreadSafeResourceRegistry.ThreadSafeMethod:
            # 如果直接内部方法已经有相同的resource_id锁，直接返回原方法
            if (hasattr(method, '_isThreadSafe') and 
                getattr(method, '_resourceId') == resourceId):
                return method # type: ignore
            
            @wraps(method)
            def wrapper(*args: Any, **kwargs: Any) -> Any:
                mutex = self.getMutex(resourceId)
                with QTimeoutMutexLocker(mutex, timeoutMs) as locked:
                    if not locked:
                        raise TimeoutError(f"Unable to acquire lock for {resourceId}, timeout={timeoutMs}ms")
                    return method(*args, **kwargs)
            
            wrapper._isThreadSafe = True  # type: ignore
            wrapper._resourceId = resourceId  # type: ignore
            return wrapper  # type: ignore
        return decorator

    def registerSafeOperation(self, objOrCls, resourceId: str, methodNames: list[str], timeoutMs: int = 3000):
        """为实例或类注册多个需要线程安全的方法"""
        for methodName in methodNames:
            if hasattr(objOrCls, methodName):
                method = getattr(objOrCls, methodName)
                safeMethod = self.safeOperation(resourceId, timeoutMs)(method)
                setattr(objOrCls, methodName, safeMethod)

#模块级统一资源-锁注册
AAXW_JUMPIN_QTSRR=QThreadSafeResourceRegistry()

#线程封装-工作器
class JumpinQRSignalWorker(QRunnable):
    """
    统一的工作线程封装，支持函数式任务和QRunnable代理
    """
    class WorkerSignals(QObject):
        """
        定义工作线程的信号
        """
        ON_FINISHED = Signal()  # 任务完成信号
        ON_EXCEPTION = Signal(tuple)  # 错误信号
        GET_RESULT = Signal(object)  # 结果信号
        PROGRESS = Signal(int)  # 进度信号
        BEFORE_RUNNING = Signal()  # 开始信号
        # STATUS = Signal(str)  # 状态信号


    def __init__(self, task: Union[Callable, QRunnable], *args, **kwargs):
        super().__init__()
        # 信号与管理
        self.signals = JumpinQRSignalWorker.WorkerSignals()
        self.isInterrupted = False
        #
        
        # 判断任务类型
        if isinstance(task, QRunnable):
            self.taskType = "runnable"
            self.runnable = task
        else:
            self.taskType = "function"
            self.fn = task
            self.args = args
            self.kwargs = kwargs

    @override
    def run(self):
        try:
            if not self.isInterrupted:
                self.signals.BEFORE_RUNNING.emit()
                if self.taskType == "runnable":
                    # 执行被代理的runnable的run方法
                    self.runnable.run()
                    self.signals.GET_RESULT.emit(None)
                else:
                    # 执行函数式任务
                    if 'progressSignal' in self.fn.__code__.co_varnames:
                        result = self.fn(
                            progressSignal=self.signals.PROGRESS,
                            *self.args, **self.kwargs
                        )
                    else:
                        result = self.fn(*self.args, **self.kwargs)
                    self.signals.GET_RESULT.emit(result)
        except:
            traceback.print_exc()
            exctype, value = sys.exc_info()[:2]
            self.signals.ON_EXCEPTION.emit((exctype, value, traceback.format_exc()))
        finally:
            self.signals.ON_FINISHED.emit()

    def interrupt(self):
        self.isInterrupted = True
        if self.taskType == "runnable":
            # 如果被代理的runnable实现了kill方法，也调用它
            if hasattr(self.runnable, 'kill'):
                self.runnable.kill() # type:ignore
            elif hasattr(self.runnable, 'interrupt'):
                self.runnable.interrupt() # type:ignore
            elif hasattr(self.runnable, 'stop'):
                self.runnable.stop() # type:ignore
            else:
                print("runnable没有实现用于中断的方法")

class JumpinQRWorkerPool(QObject):
    """
    worker池，用来池化管理Worker的运行。
    """
    POOL_STATUS_CHANGED = Signal(dict)  # 池状态变化信号

    def __init__(self, maxThreads=None,hasMonitor=True):
        super().__init__()
        self.threadPool = QThreadPool()
        if maxThreads:
            self.threadPool.setMaxThreadCount(maxThreads)
        self.activeWorkers = []
        

        #
        self.hasMonitor=hasMonitor
        if self.hasMonitor:
            # 添加监控用定时器
            self.monitorTimer = QTimer()
            self.monitorTimer.setInterval(10000)  # 每10秒更新一次
            self.monitorTimer.timeout.connect(self._updatePoolStatus)

    def createWorker(self, task: Union[Callable, QRunnable], *args, **kwargs):
        """创建工作线程但不启动
        Args:
            task: 可以是函数或QRunnable实例
            *args, **kwargs: 如果task是函数，这些参数会传递给函数
        """
        worker = JumpinQRSignalWorker(task, *args, **kwargs)
        # worker.setAutoDelete(True)
        worker.signals.ON_FINISHED.connect(lambda: self._removeWorker(worker))
        return worker

    def startWorker(self, worker):
        """启动指定的工作线程"""
        self.activeWorkers.append(worker)
        self.threadPool.start(worker)

    def createAndStartWorker(self, task: Union[Callable, QRunnable], *args, **kwargs):
        """直接提交并启动任务（便捷方法）
        Args:
            task: 可以是函数或QRunnable实例
            *args, **kwargs: 如果task是函数，这些参数会传递给函数
        """
        worker = self.createWorker(task, *args, **kwargs)
        self.startWorker(worker)
        return worker

    def _removeWorker(self, worker):
        """移除完成的工作线程"""
        if worker in self.activeWorkers:
            self.activeWorkers.remove(worker)

    
    def startMonitoring(self):
        """开始定时监控线程池状态"""
        self._updatePoolStatus()
        self.monitorTimer.start()

    def stopMonitoring(self):
        """停止监控"""
        self.monitorTimer.stop()
        
    @Slot()
    def _updatePoolStatus(self):
        """更新并发送线程池状态"""
        status = {
            'activeThreadCount': self.threadPool.activeThreadCount(),
            'maxThreadCount': self.threadPool.maxThreadCount(),
            'activeWorkers': len(self.activeWorkers)
        }
        self.POOL_STATUS_CHANGED.emit(status)

    def clearActiveWorkers(self):
        """清空任务队列"""
        worker:JumpinQRSignalWorker=None #type:ignore
        for worker in self.activeWorkers:
            worker.interrupt()
        self.activeWorkers.clear()
        
    def onClose(self):
        self.stopMonitoring()
        self.clearActiveWorkers()
        self.threadPool.clear()

    def waitForDone(self, msecs=-1):
        """等待所有任务完成
        Args:
            msecs: 等待超时时间(毫秒)。默认-1表示无限等待
        Returns:
            bool: 是否所有任务都完成
        """
        #在界面的线程中不要执行，会卡死界面主线程
        return self.threadPool.waitForDone(msecs)
# 界面异步处理相关 end






@AAXW_JUMPIN_LOG_MGR.classLogger()
class AAXWScrollPanel(QFrame):
    """
    垂直方向以列表样式可追加内容的展示面板；
    内容所在Row部件会根据内容调整高度；
    内部聚合了定制的vbxlayout，增加content时默认使用TextBrowser用作Row展示。
    提供了为RowContent追加内容的方式，支持流式获取文本追加到Row中。
    """
    AAXW_CLASS_LOGGER:logging.Logger


    @AAXW_JUMPIN_LOG_MGR.classLogger()
    class TextBrowserStrategy(AAXWContentBlockStrategy): #先当做界面的一个扩展？

        AAXW_CLASS_LOGGER:logging.Logger

        # 用特殊符号最为追加占位标记
        MARKER = "[💬➡️🏁]"
        # @staticmethod
        @override
        def createWidget(self,rowId: str, contentOwner: str, contentOwnerType: str, 
                        mainWindow: 'AAXWJumpinMainWindow', strategyWidget: 'AAXWScrollPanel') -> QTextBrowser:
            
            tb = QTextBrowser()
            tb.setObjectName(f"{AAXWScrollPanel.ROW_BLOCK_NAME_PREFIX}_{rowId}")
            tb.setProperty("id", rowId)
            tb.setProperty("contentOwner", contentOwner)
            tb.setProperty("contentOwnerType", contentOwnerType)
            # 高度先限定，然后根据内部变化，关闭滚动条
            tb.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            tb.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            
            # 明确设置背景颜色
            # if contentOwnerType == "ROW_CONTENT_OWNER_TYPE_USER":
            #     tb.setStyleSheet("background-color: #e0e0e0; color: #000000;")
            # else:
            #     tb.setStyleSheet("background-color: #e6e6fa; color: #00008b;")

            # 关闭自动格式化？
            tb.setAutoFormatting(QTextBrowser.AutoFormattingFlag.AutoNone)
            tb.setLineWrapMode(QTextBrowser.LineWrapMode.WidgetWidth)

            # 设置基本样式；
            doc = QTextDocument()
            tb.setDocument(doc)
            doc.setDefaultStyleSheet("p { white-space: pre-wrap; }")


            # 内容改变改变高度
            tb.document().contentsChanged.connect(lambda: self.adjustSize(tb))

            #初始化空间
            # initial_text = " "
            # doc.setHtml(initial_text)
            # tb.append(TextBrowserStrategy.MARKER)  # 这里增加一个追加内容用的特别Marker
            self.initContent(widget=tb,content=" ")

            # 现在可以使用 main_window 和 panel 进行额外的设置或操作
            tb.setProperty("mainWindow", mainWindow)
            tb.setProperty("strategyWidget", strategyWidget)

            return tb

        # @staticmethod
        @override
        def initContent(self,widget: QTextBrowser, content: str):
            tb=widget
            doc=tb.document()
            #初始化空间
            initial_text = content
            doc.setHtml(initial_text)
            tb.append(self.MARKER)  # 这里增加一个追加内容用的特别Marker

        # @staticmethod
        @override
        def insertContent(self,widget: QTextBrowser, content: str):
            # 使用游标进行查找marker并更新平文
            doc = widget.document()
            cursor = doc.find(self.MARKER)
            if cursor:
                cursor.movePosition(QTextCursor.MoveOperation.PreviousCharacter, 
                                    QTextCursor.MoveMode.MoveAnchor
                )
                cursor.insertHtml(f"{content}")  # 可以追加html但是会过滤掉不符合规范的比如div
                widget.repaint()  # 非线程调用本方法，可能每次都要重绘，否则是完成完后一次性刷新。
            else:
                self.AAXW_CLASS_LOGGER.debug(
                    "not found marker:" + self.MARKER)

        # @staticmethod
        def adjustSize(self,widget: QTextBrowser):
            
            tb:QTextBrowser = widget
            # 获取 QTextBrowser 的文档对象
            doc = tb.document()
            # 获取 QTextBrowser 的内容边距
            margins = tb.contentsMargins()
            #  计算文档高度加上上下边距得到总高度
            # TODO 这里计算的不对，所有tb都需要根据内容来计算高度，获取内容应该。
            expectantHeight:int = int(
                doc.size().height() + margins.top() + margins.bottom() + 10 #预期行高增加1行？
            )  # 多增加点margins

            # 使用fixed的尺寸策略
            # 调整Row tb高度
            if expectantHeight<20: expectantHeight=20
            tb.setFixedHeight(int(expectantHeight))


            #同时调整主窗口高度；
            mainWindow:"AAXWJumpinMainWindow"=tb.property("mainWindow")

            # 
            # mainWindow不为none，刚创建的tb没有mainWindow？
            if mainWindow :mainWindow.adjustHeight()                

    
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


    ROW_BLOCK_NAME_PREFIX = "row_block_name"
    #  区分展示内容行的类型
    ROW_CONTENT_OWNER_TYPE_USER="ROW_CONTENT_OWNER_TYPE_USER"
    ROW_CONTENT_OWNER_TYPE_OTHERS="ROW_CONTENT_OWNER_TYPE_OTHERS"
    ROW_CONTENT_OWNER_TYPE_SYSTEM="ROW_CONTENT_OWNER_TYPE_SYSTEM"

    def __init__(self, mainWindow: "AAXWJumpinMainWindow", qss:str=DEFAULT_STYLE,
                blockStrategy:AAXWContentBlockStrategy=TextBrowserStrategy(),parent=None):
        """
        当前控件展示与布局结构：
        AAXWScrollPanel->QVBoxLayout->QScrollArea->QWidget(scrollWidget)-> TB等
        """
        super().__init__(parent)
        self.mainWindow = mainWindow
        self.setFrameShape(QFrame.Shape.StyledPanel)
        # self.setFrameShadow(QFrame.Raised) #阴影凸起
        self.setStyleSheet(qss)
   

        self.contentBlockStrategy:AAXWContentBlockStrategy = blockStrategy

        # 主要设定可垂直追加的Area+Layout
        # 结构顺序为scroll_area->scroll_widget->scroll_layout
        self.scrollArea = QScrollArea()  # ScrollArea 聊天内容展示区域
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scrollArea.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        #
        self.scrollWidget = QWidget()
        # scrollArea-scrollWidget
        self.scrollArea.setWidget(self.scrollWidget)
        self.scrollLayout: AAXWVBoxLayout = AAXWVBoxLayout(self.scrollWidget)
        self.scrollLayout.setAlignment(Qt.AlignmentFlag.AlignTop)  # 设置加入的部件为顶端对齐

        # 缩小间隔
        self.scrollLayout.setContentsMargins(1, 1, 1, 1)
        self.scrollLayout.setSpacing(3)
        # 使用scroll_layout来添加元素，应用布局；

        # panel层布局
        panelLayout = QVBoxLayout(self)
        panelLayout.addWidget(self.scrollArea)  # 加上scroll_area
        #
        panelLayout.setContentsMargins(1, 1, 1, 1)
        panelLayout.setSpacing(1)
        self.setLayout(panelLayout) #

        # 确保滚动面板有固定背景色
        # self.setStyleSheet(AAXWJumpinConfig.SCROLL_PANEL_QSS)


    def addRowContent(self, content, rowId, contentOwner="unknown", 
                      contentOwnerType=ROW_CONTENT_OWNER_TYPE_SYSTEM, isAtTop=True):
        """
        在scrollLayout上添加一个内容行，默认使用QTextBrowser。
        默认在顶端加入；
        rowId 表示内容行的唯一标识，用于后续查找，组件定位；
        """
        
        widget = self.contentBlockStrategy.createWidget(rowId, contentOwner, contentOwnerType, self.mainWindow, self)
        
        # 加入列表
        if isAtTop:
            self.scrollLayout.addWidgetAtTop(widget)  # 这里每次在头部加layout定制了
        else:
            self.scrollLayout.addWidget(widget)
        
        self.contentBlockStrategy.initContent(widget, content)


    def appendContentByRowId(self, text, rowId: str):
        """
        在指定Rowid的Row中追加内容；
        可用于回调操作时更新指定块内容；
        """
        # 查找对应的 QWidget 并追加内容
        # 用名字查找元素
        widget = self.scrollWidget.findChild(
            QWidget, f"{self.ROW_BLOCK_NAME_PREFIX}_{rowId}"
        )
        #TODO findChild 默认返回的是object，这里类型需要处理一下；
        if widget:
            self.contentBlockStrategy.insertContent(widget, text) #type:ignore
            # self.strategy.adjustSize(widget) #type:ignore
            # self.mainWindow.adjustHeight()
        else:
            self.AAXW_CLASS_LOGGER.debug(f"Not found widget by name: {self.ROW_BLOCK_NAME_PREFIX}_{rowId}")

    def clearContent(self):
        """清理滚动面板中的所有内容，会销毁内部组件所有控件。"""
        for i in reversed(range(self.scrollLayout.count())): 
            widget = self.scrollLayout.itemAt(i).widget()
            if widget is not None:
                widget.deleteLater()  # 删除小部件
        self.scrollLayout.update()  # 更新布局以反映更改

    # 
    # Panel的内部基于scroll-widget增加组件后的期望尺寸；
    def expectantHeight(self):
        # 关键点是Panel，scrollArea的实际大小与 self
        # .scrollArea.widget() 提供的大小即内部期望的大小是不一样的。
        # 默认Panel或scrollArea是根据外部来设置大小的。
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

    # def scrollWidgetSize(self):
    #     return self.scrollArea.widget().size()

    pass  # AAXWScrollPanel end







class AAXWFollowerWindow(QWidget):
    """
    工具窗口，可以相对于参考widget固定位置，并根据参考位置调整尺寸
    """
    
    # 定义位置常量
    TOP = "top"
    BOTTOM = "bottom"
    LEFT = "left"
    RIGHT = "right"
    
    # 未指定边的默认尺寸
    DEFAULT_SIZE = 100
    
    def __init__(self, refWidget: QWidget, refPosition: str, mainWindow: QWidget, parent=None):
        """
        初始化工具窗口
        :param refWidget: 参考Widget
        :param refPosition: 相对位置 ('top', 'bottom', 'left', 'right')
        :param mainWindow: 主窗口引用
        :param parent: 父Widget
        """
        super().__init__(parent=parent)
        self.refWidget = refWidget
        self.refPosition = refPosition.lower()
        self.mainWindow = mainWindow
        self.spacing = 5  # 与参考widget的间距
        
        # 设置窗口属性
        self.setWindowFlags(Qt.WindowType.Tool | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # 根据参考位置调整尺寸
        self.adjustSize()
        
        # 初始化UI
        self._initUI()
        
        # 都不用在外侧用moveEvent去注册了。
        # 这里直接用refwidget去install了移动监听动作了。eventFilter方法。
        # 安装事件过滤器来监听参考widget的移动和尺寸变化
        self.refWidget.installEventFilter(self)
        
    def _initUI(self):
        """初始化UI组件"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        
        # contentWidget作为实际显示的容器
        self.contentWidget = QWidget(self)
        self.contentWidget.setObjectName("followerWindow")
        self.contentWidget.setStyleSheet("""
            #followerWindow {
                /* background-color: #f0f0f0; */
                background-color: lightblue;
                border: 1px solid #ccc;
                border-radius: 10px;
            }
        """)
        # contentWidget使用单层布局
        self.contentLayout = QVBoxLayout(self.contentWidget)
        self.contentLayout.setContentsMargins(5, 5, 5, 5)
        #
        layout.addWidget(self.contentWidget)
        
    def setCentralWidget(self, widget: QWidget):
        """
        设置内容组件 
        注意本窗口不维护central widget的整体生命周期。
        只是放入并展示。
        """
        # 先移除当前显示的widget
        self.removeCentralWidget()
        
        # 添加并显示新的widget
        if widget is not None:
            self.contentLayout.addWidget(widget)
            widget.show()  # 确保widget是可见的
    
    def removeCentralWidget(self):
        """
        移除当前显示的widget但不删除它；
        centralWidget 由放置进来的applet或插件维护。
        """
        for i in reversed(range(self.contentLayout.count())): 
            item = self.contentLayout.itemAt(i)
            if item.widget():
                widget = item.widget()
                self.contentLayout.removeItem(item)
                widget.hide()           # 隐藏当前widget
                widget.setParent(None)  # 解除父子关系但保持widget存在

    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        """监听参考widget的移动和尺寸变化事件"""
        if watched == self.refWidget:
            if event.type() in [QEvent.Type.Move, QEvent.Type.Resize]:
                self.adjustSize()
                self.updatePosition()
        return super().eventFilter(watched, event)

    def adjustSize(self):
        """根据参考widget的位置调整尺寸"""
        if not self.refWidget:
            return
            
        ref_size = self.refWidget.size()
        
        if self.refPosition in [self.TOP, self.BOTTOM]:
            # 上/下位置时，宽度与参考widget相同，高度使用默认值
            self.setFixedSize(ref_size.width(), self.DEFAULT_SIZE)
        elif self.refPosition in [self.LEFT, self.RIGHT]:
            # 左/右位置时，高度与参考widget相同，宽度使用默认值
            self.setFixedSize(self.DEFAULT_SIZE, ref_size.height())
            
    def updatePosition(self):
        """更新工具窗口位置"""
        if not self.refWidget:
            return
            
        ref_geo = self.refWidget.geometry()
        ref_pos = self.refWidget.mapToGlobal(QPoint(0, 0))
        
        # 计算新位置
        new_pos = QPoint()
        
        if self.refPosition == self.TOP:
            new_pos.setX(ref_pos.x() + (ref_geo.width() - self.width()) // 2)
            new_pos.setY(ref_pos.y() - self.height() - self.spacing)
        
        elif self.refPosition == self.BOTTOM:
            new_pos.setX(ref_pos.x() + (ref_geo.width() - self.width()) // 2)
            new_pos.setY(ref_pos.y() + ref_geo.height() + self.spacing)
        
        elif self.refPosition == self.LEFT:
            new_pos.setX(ref_pos.x() - self.width() - self.spacing)
            new_pos.setY(ref_pos.y() + (ref_geo.height() - self.height()) // 2)
        
        elif self.refPosition == self.RIGHT:
            new_pos.setX(ref_pos.x() + ref_geo.width() + self.spacing)
            new_pos.setY(ref_pos.y() + (ref_geo.height() - self.height()) // 2)
            
        # 
        # 当前逻辑，可以移动到屏幕外部；
        #
        # 确保窗口不会超出屏幕边界（这个在特定情况也有用。）
        # screen_geo = QApplication.primaryScreen().geometry()
        # new_pos.setX(max(0, min(new_pos.x(), screen_geo.width() - self.width())))
        # new_pos.setY(max(0, min(new_pos.y(), screen_geo.height() - self.height())))
        #
        
        self.move(new_pos)

    def toggleVisibility(self):
        """切换显示/隐藏状态"""
        AAXW_JUMPIN_MODULE_LOGGER.info("toggle_visibility!")
        if self.isVisible():
            self.hide()
        else:
            self.show()
            self.adjustSize()
            self.updatePosition()
            
    # def showEvent(self, event: QShowEvent):
    #     """显示时更新位置"""
    #     super().showEvent(event)
    #     self.update_position()


class AAXWFramelessWindow(QWidget):
    def __init__(self,parent):
        super().__init__(parent=parent)
        self._init_frameless_ui()

    DEFAULT_QSS="""
    AAXWFramelessWindow#ananxw_frameless_window {
        background-color: #fff;
        border-radius: 10px;
    }
    """

    def _init_frameless_ui(self):
        # self.setWindowTitle("ANAN!")
        # self.setObjectName("ananxw_frame_window")

        self.setWindowTitle("ANAN")
        self.setObjectName("ananxw_main_window")
        self.setStyleSheet(self.DEFAULT_QSS)
        # self.setStyleSheet(AAXWJumpinConfig.MAIN_WINDOWS_QSS)
        self.setFrameless()
        

    def setFrameless(self):
        self.setWindowFlags(self.windowFlags()| Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        ...

    #直接绘制窗口背景
    # 这里是画了圆角透明主窗口。
    # TODO 之后还是改为主窗口中加1个widget作为伪主窗口的面板，基于此定制以及绘制异形主窗口。
    #      暂时使用重绘简单实现。
    def paintEvent(self, event):    
        #为主窗口 绘制圆角 这里只取了qss的背景色
        
        # qss获取
        opt:QStyleOption = QStyleOption() 
        opt.initFrom(self) #加载自己对应qss

        # 获取 QSS 中定义的背景颜色
        # bg_color = opt.palette.window().color() #python层可能有类型问题
        bg_color = self.palette().color(self.backgroundRole()) #
        ##
        
        #绘制
        painter = QPainter(self) 
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = self.rect()
        # painter.setBrush(QColor(255, 255, 255)) 
        painter.setBrush(bg_color) 
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(rect, 20, 20) #圆角

@AAXW_JUMPIN_LOG_MGR.classLogger()
class AAXWJumpinThreadSafeMsgShowingPanel(AAXWScrollPanel):
    """
    消息展示面板代理类
    通过继承原始面板类来实现代理
    """
    AAXW_CLASS_LOGGER:logging.Logger

    THREAD_SAFE_RESOURCE_ID='AAXWJumpinThreadSafeMsgShowingPanel'

    def __init__(self, mainWindow, qss, parent=None):
        super().__init__(mainWindow=mainWindow, qss=qss, parent=parent)
        self.resourceId = f"msg_panel_{id(self)}"
        
        # 注册需要线程安全保护的方法
        # AAXW_JUMPIN_QTSRR.registerSafeOperation(
        #     self,
        #     self.resourceId,
        #     ['addRowContent', 'appendContentByRowId', 'clearContent']
        # )
    AAXW_JUMPIN_QTSRR.safeOperation(resourceId=THREAD_SAFE_RESOURCE_ID)
    def addRowContent(self, content: str, rowId: str, contentOwner: str, 
                     contentOwnerType: str, isAtTop: bool = True) -> None:
        # 在父类方法调用前后可以添加额外的处理逻辑
        return super().addRowContent(content, rowId, contentOwner, 
                                   contentOwnerType, isAtTop)
    
    # TODO 该方法加锁消耗可能会比较大。streaming方式可能是1个字符1个字符更新到界面的。
    AAXW_JUMPIN_QTSRR.safeOperation(resourceId=THREAD_SAFE_RESOURCE_ID)
    def appendContentByRowId(self, content: str, rowId: str) -> None:
        return super().appendContentByRowId(content, rowId)
    
    AAXW_JUMPIN_QTSRR.safeOperation(resourceId=THREAD_SAFE_RESOURCE_ID,timeoutMs=60*100)
    def clearContent(self) -> None:
        return super().clearContent()


# 
class LLMProviderForm(QWidget):
    """LLM模型提供商配置表单"""
    
    def __init__(self, dependencyContainer:AAXWDependencyContainer ,jumpinConfig:AAXWJumpinConfig,title:str,parent:QWidget=None):
        super().__init__(parent=parent)
        self.jumpinConfig:AAXWJumpinConfig = jumpinConfig
        self.dependencyContainer=dependencyContainer
        
        # 创建主布局
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(10)  # 设置合适的间距
        self.layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # 添加组标题
        self.titleLabel = None
        if title:
            self.titleLabel = SubtitleLabel(title)
            self.layout.addWidget(self.titleLabel)
        
        # 创建分段控件和堆叠窗口
        self.segmentedWidget = SegmentedWidget(self)
        self.stackedWidget = QStackedWidget(self)
        
        # 创建标签页
        self.openaiTab = self.createOpenAITab()
        self.ollamaTab = self.createOllamaTab()
        
        # 添加标签页到堆叠窗口
        self.stackedWidget.addWidget(self.openaiTab)
        self.stackedWidget.addWidget(self.ollamaTab)
        
        # 添加选项到分段控件
        self.segmentedWidget.addItem(text="OpenAI", routeKey="openai")
        self.segmentedWidget.addItem(text="Ollama", routeKey="ollama")
        
        # 连接信号 - 使用currentItemChanged信号和自定义处理函数
        self.segmentedWidget.currentItemChanged.connect(self.onProviderChanged)
        
        # 添加到布局
        self.layout.addWidget(self.segmentedWidget)
        self.layout.addWidget(self.stackedWidget)
        
        # 默认选择第一个选项
        self.segmentedWidget.setCurrentItem("openai")
        self.stackedWidget.setCurrentWidget(self.openaiTab)

        # self.segmentedWidget.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)
        # self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        self.setMaximumHeight(300)
        # self.setMinimumHeight(150)
        # 设置尺寸策略，防止过大的留白
        # self.stackedWidget.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)
        # 设置最大高度限制，防止过大的留白
        
    
    def onProviderChanged(self, routeKey):
        """处理提供商切换的方法"""
        # 根据routeKey设置stackedWidget的当前索引
        if routeKey == "openai":
            self.stackedWidget.setCurrentWidget(self.openaiTab)
        elif routeKey == "ollama":
            self.stackedWidget.setCurrentWidget(self.ollamaTab)
    
    def createOpenAITab(self):
        """创建OpenAI配置选项卡"""
        container = QWidget()
        layout = QVBoxLayout(container)
        # layout.setContentsMargins(10, 10, 10, 10)
        # layout.setSpacing(8)  # 设置合适的间距
        # container.setMinimumHeight(100)
        # container.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)
        
        # API密钥
        apiKeyLabel = BodyLabel("API密钥:")
        self.apiKeyEdit = LineEdit()
        self.apiKeyEdit.setPlaceholderText("输入您的OpenAI API Key")
        self.apiKeyEdit.setText(self.jumpinConfig.openaiProvider.apiKey)
        self.apiKeyEdit.setClearButtonEnabled(True)
        self.apiKeyEdit.setEchoMode(QLineEdit.EchoMode.Password)
        
        # 基础URL
        baseUrlLabel = BodyLabel("基础URL:")
        self.baseUrlEdit = LineEdit()
        self.baseUrlEdit.setPlaceholderText("输入API基础URL（可选）")
        self.baseUrlEdit.setText(self.jumpinConfig.openaiProvider.baseUrl)
        self.baseUrlEdit.setClearButtonEnabled(True)
        
        # 模型选择
        modelLabel = BodyLabel("模型:")
        self.modelComboBox = ComboBox()
        # models = ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-3.5-turbo"]
        models = self.jumpinConfig.openaiProvider.candidateModels()
        self.modelComboBox.addItems(models)
        
        # 设置默认模型
        defaultModel = self.jumpinConfig.openaiProvider.defaultModelName
        index = self.modelComboBox.findText(defaultModel)
        if index >= 0:
            self.modelComboBox.setCurrentIndex(index)
        
        # 保存按钮
        self.saveOpenAIButton = PrimaryPushButton("保存设置")
        self.saveOpenAIButton.clicked.connect(self.saveOpenAISettings)
        
        # 添加组件到布局
        layout.addWidget(apiKeyLabel)
        layout.addWidget(self.apiKeyEdit)
        layout.addWidget(baseUrlLabel)
        layout.addWidget(self.baseUrlEdit)
        layout.addWidget(modelLabel)
        layout.addWidget(self.modelComboBox)
        layout.addWidget(self.saveOpenAIButton)
        # 移除这行代码，它会导致下方留白
        # layout.addStretch(1)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        return container
    
    def createOllamaTab(self):
        """创建Ollama配置选项卡"""
        container = QWidget()
        layout = QVBoxLayout(container)
        # layout.setContentsMargins(10, 10, 10, 10)
        # layout.setSpacing(8)  # 设置合适的间距
        
        # 服务地址
        serviceUrlLabel = BodyLabel("服务地址:")
        self.serviceUrlEdit = LineEdit()
        self.serviceUrlEdit.setPlaceholderText("例如: http://localhost:11434")
        self.serviceUrlEdit.setText(self.jumpinConfig.ollamaProvider.serviceUrl)
        self.serviceUrlEdit.setClearButtonEnabled(True)
        
        # 模型选择
        modelLabel = BodyLabel("模型:")
        self.ollamaModelComboBox = ComboBox()
        ollamaModels = ["llama3.1", "llama3", "llama2", "qwen2.5:1.5b", "qwen2.5:0.5b", "deepseek"]
        self.ollamaModelComboBox.addItems(ollamaModels)
        
        # 设置默认模型
        defaultOllamaModel = self.jumpinConfig.ollamaProvider.defaultModelName
        index = self.ollamaModelComboBox.findText(defaultOllamaModel)
        if index >= 0:
            self.ollamaModelComboBox.setCurrentIndex(index)
        
        # 保存按钮
        self.saveOllamaButton = PrimaryPushButton("保存设置")
        self.saveOllamaButton.clicked.connect(self.saveOllamaSettings)
        
        # 添加组件到布局
        layout.addWidget(serviceUrlLabel)
        layout.addWidget(self.serviceUrlEdit)
        layout.addWidget(modelLabel)
        layout.addWidget(self.ollamaModelComboBox)
        layout.addWidget(self.saveOllamaButton)
        # 移除这行代码，它会导致下方留白
        # layout.addStretch(1)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        return container
    
    def saveOpenAISettings(self):
        """保存OpenAI设置"""
        # 获取输入值
        apiKey = self.apiKeyEdit.text().strip()
        baseUrl = self.baseUrlEdit.text().strip()
        modelName = self.modelComboBox.currentText()
        
        # 更新配置并保存
        # 设置默认提供商为OpenAI
        openaiConfig = {
            "apiKey": apiKey,
            "baseUrl": baseUrl,
            "modelName": modelName
        }
        
        # 调用更新方法，更新LLM配置
        self.jumpinConfig.updateLLMConfig(
            provider="openai", 
            openaiConfig=openaiConfig,
            llmModel=modelName  # 添加这一行，确保llmModel也被更新
        )


        self.jumpinConfig.saveConfigToYaml()
        
        # 重新加载配置以确保一致性
        self.jumpinConfig.reloadConfig()
        
        # 输出当前LLM配置到日志
        self.jumpinConfig.logLLMConfig()

        # 重新初始化configurableAIConnOrAgent
        configurableAIConnOrAgent:ConfigurableAIConnOrAgent =self.dependencyContainer.getAANode("configurableAIConnOrAgent")
        configurableAIConnOrAgent._initializeInnerInstance()
        
        # 显示成功消息
        InfoBar.success(
            title='成功',
            content="OpenAI设置已保存",
            orient=Qt.Orientation.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=2000,
            parent=self
        )

    def saveOllamaSettings(self):
        """保存Ollama设置"""
        # 获取输入值
        serviceUrl = self.serviceUrlEdit.text().strip()
        modelName = self.ollamaModelComboBox.currentText()
        
        # 更新配置并保存
        # 设置默认提供商为Ollama
        ollamaConfig = {
            "serviceUrl": serviceUrl,
            "modelName": modelName
        }
        
        # 调用更新方法，更新LLM配置
        self.jumpinConfig.updateLLMConfig(
            provider="ollama", 
            ollamaConfig=ollamaConfig,
            llmModel=modelName  # 添加这一行，确保llmModel也被更新
        )
        
        # 保存配置到文件
        self.jumpinConfig.saveConfigToYaml()
        
        # 重新加载配置以确保一致性
        self.jumpinConfig.reloadConfig()
        
        # 输出当前LLM配置到日志
        self.jumpinConfig.logLLMConfig()

        # 重新初始化configurableAIConnOrAgent
        configurableAIConnOrAgent:ConfigurableAIConnOrAgent =self.dependencyContainer.getAANode("configurableAIConnOrAgent")
        configurableAIConnOrAgent._initializeInnerInstance()
        
        # 显示成功消息
        InfoBar.success(
            title='成功',
            content="Ollama设置已保存",
            orient=Qt.Orientation.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=2000,
            parent=self
        )

@AAXW_JUMPIN_LOG_MGR.classLogger()
class AAXWJumpinSettingPanel(ScrollArea):
    """ Setting interface """
    AAXW_CLASS_LOGGER:logging.Logger

    def __init__(self, dependencyContainer:AAXWDependencyContainer,
                 jumpinConfig:AAXWJumpinConfig,parent=None):
        super().__init__(parent=parent)
        self.jumpinConfig:AAXWJumpinConfig=jumpinConfig
        self.dependencyContainer=dependencyContainer
        self.scrollWidget = QWidget()
        self.expandLayout = ExpandLayout(self.scrollWidget)
        
        # setting label
        self.settingLabel = QLabel("设置", self)
        # 设置字体更大并加粗
        font = self.settingLabel.font()
        font.setPointSize(16)  # 增大字体
        font.setBold(True)     # 加粗字体
        self.settingLabel.setFont(font)

        # 基本设置组
        self.basicSettingGroup = SettingCardGroup(
            "基本设置信息", self.scrollWidget)

        self.appNameCard = SettingCard(
            icon=FIF.FOLDER,
            title="应用名称",
            content=self.jumpinConfig.appName,
            # 上面 设定为 Field-Value对显示
        )

        self.versionCard = SettingCard(
            icon=FIF.CODE,
            title="版本信息",
            content=self.jumpinConfig.appVersion,
        )

        self.workDirCard = SettingCard(
            icon=FIF.FOLDER,
            title="工作目录",
            content=self.jumpinConfig.appWorkDir,
        )

        # 添加到基本设置组
        self.basicSettingGroup.addSettingCard(self.appNameCard)
        self.basicSettingGroup.addSettingCard(self.versionCard)
        self.basicSettingGroup.addSettingCard(self.workDirCard)
        
        # 创建LLM模型配置表单
        self.llmProviderForm = LLMProviderForm(
            dependencyContainer=self.dependencyContainer,
            jumpinConfig=self.jumpinConfig,
            title=None) #type:ignore
        
        # 创建LLM模型设置组
        self.modelSettingGroup = SettingCardGroup(
            "LLM模型设置", self.scrollWidget)
        
        # 直接添加LLMProviderForm到模型设置组
        self.modelSettingGroup.addSettingCard(self.llmProviderForm)
        
        # 其他设置组
        self.otherSettingGroup = SettingCardGroup(
            "其他设置", self.scrollWidget)

        self.downloadFolderCard = PrimaryPushSettingCard(
            icon=FIF.DOWNLOAD,
            title='关于',
            content="",
            text='前往GitHub'
        )
        self.downloadFolderCard.clicked.connect(self.__onDownloadFolderCardClicked)

        # 添加到其他设置组
        self.otherSettingGroup.addSettingCard(self.downloadFolderCard)

        self.__initWidget()
        self.__initLayout()
        self.__connectSignalToSlot()

    def __onDownloadFolderCardClicked(self):
        """ download folder card clicked slot """
        # 打开GitHub页面或其他相关操作
        pass

    def __initWidget(self):
        """初始化控件属性"""
        # self.resize(1000, 800)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        # 这里是空出上部空间，因为设置标签字体更大并加粗，所以空出50
        self.setViewportMargins(0, 50, 0, 20)  # 原来是80，现在改为50，减小上部区域高度
        self.setWidget(self.scrollWidget)
        self.setWidgetResizable(True)
        self.setObjectName('settingInterface')
        
        # 初始化样式表
        self.scrollWidget.setObjectName('scrollWidget')
        self.settingLabel.setObjectName('settingLabel')
        
        # 添加样式表以进一步自定义标签外观
        self.settingLabel.setStyleSheet("""
            QLabel#settingLabel {
                color: #303030;
                margin-bottom: 5px;
            }
        """)

    def __initLayout(self):
        """初始化布局"""
        self.settingLabel.move(36, 15)  # 原来是30，现在改为15，减小上部空间

        # 将设置组添加到布局中
        self.expandLayout.setSpacing(28)
        self.expandLayout.setContentsMargins(36, 10, 36, 0)
        self.expandLayout.addWidget(self.basicSettingGroup)
        self.expandLayout.addWidget(self.modelSettingGroup)  # 添加LLM模型设置组
        self.expandLayout.addWidget(self.otherSettingGroup)

    def __connectSignalToSlot(self):
        """连接信号和槽"""
        # 在此处添加需要的信号连接
        pass

class JumpinNavigationWidget(NavigationPushButton):
    """简单的导航组件，区分左右键点击"""
    
    leftClicked = Signal()  # 左键点击信号 这个原始信号不太一样原来是有个bool参数的。

    def __init__(self, icon, text: str, isSelectable: bool = True, parent=None):
        super().__init__(icon=icon, text=text, isSelectable=isSelectable, parent=parent)
        
    def mouseReleaseEvent(self, e):
        """重写鼠标释放事件"""
        if e.button() == Qt.MouseButton.LeftButton:
            self.leftClicked.emit()
        super().mouseReleaseEvent(e)

class JumpinNavigationInterface(NavigationInterface):
    """扩展的导航界面"""

    def __init__(
            self, parent=None, showMenuButton=True, showReturnButton=False, collapsible=True):
        super().__init__(
            parent=parent, 
            showMenuButton=showMenuButton, 
            showReturnButton=showReturnButton, 
            collapsible=collapsible)
        self.contextMenus = {}

    def insertItemWithContextMenu(self, 
            index: int,
            routeKey: str, 
            icon: Union[str, QIcon, FIF], 
            text: str, 
            onClick: Callable = None, 
            menuItems: list[tuple[str,Callable]] = None,
            selectable=True, 
            position=NavigationItemPosition.TOP, 
            tooltip: str = None,
            parentRouteKey: str = None
        ):
        """插入带右键菜单的导航项
        
        Args:
            index: 插入位置
            routeKey: 唯一标识键
            icon: 图标
            text: 显示文本
            onClick: 左键点击回调
            menuItems: 右键菜单项列表,格式为[(text, callback),...]
                callback有1个bool参数会尝试传入
            selectable: 是否可选中
            position: 插入位置类型
            tooltip: 提示文本
            parentRouteKey: 父节点routeKey
        """
        navItem = JumpinNavigationWidget(icon, text, selectable, self)
        if onClick:
            navItem.leftClicked.connect(onClick)
            
        self.insertWidget(index, routeKey, navItem, None, position, tooltip, parentRouteKey)
        
        if menuItems:
            menu = QMenu(self)
            for text, callback in menuItems:
                action = menu.addAction(text)
                action.triggered.connect(callback) #triggered(bool) 有1个bool参数
            
            self.contextMenus[routeKey] = menu
            navItem.customContextMenuRequested.connect(
                lambda pos, key=routeKey: self._showContextMenu(pos, key)
            )
            navItem.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        
        return navItem

    def addItemWithContextMenu(self, 
            routeKey: str, 
            icon: Union[str, QIcon, FIF], 
            text: str, 
            onClick: Callable = None, 
            menuItems: list[tuple[str,Callable]] = None,
            selectable=True, 
            position=NavigationItemPosition.TOP, 
            tooltip: str = None,
            parentRouteKey: str = None
        ):
        """添加带右键菜单的导航项(包装insertItemWithContextMenu)
        
        Args:
            routeKey: 唯一标识键
            icon: 图标
            text: 显示文本
            onClick: 左键点击回调
            menuItems: 右键菜单项列表,格式为[(text, callback),...]
            selectable: 是否可选中
            position: 插入位置类型
            tooltip: 提示文本
            parentRouteKey: 父节点routeKey
        """
        return self.insertItemWithContextMenu(
            index=-1,
            routeKey=routeKey,
            icon=icon, 
            text=text,
            onClick=onClick,
            menuItems=menuItems,
            selectable=selectable,
            position=position,
            tooltip=tooltip,
            parentRouteKey=parentRouteKey
        )

    def removeWidget(self, routeKey: str):
        """重写移除方法,确保清理相关的右键菜单"""
        if routeKey in self.contextMenus:
            menu = self.contextMenus.pop(routeKey)
            menu.deleteLater()
            
        super().removeWidget(routeKey)

    def _showContextMenu(self, pos, routeKey: str):
        """显示右键菜单"""
        if routeKey in self.contextMenus:
            menu = self.contextMenus[routeKey]
            widget = self.widget(routeKey)
            if widget:
                menu.exec(widget.mapToGlobal(pos))

    def clearContextMenus(self):
        """清理所有右键菜单"""
        for menu in self.contextMenus.values():
            menu.deleteLater()
        self.contextMenus.clear()

    def __del__(self):
        """析构时确保清理菜单"""
        self.clearContextMenus()
        



@AAXW_JUMPIN_LOG_MGR.classLogger()
class AAXWJumpinMainWindow(AAXWFramelessWindow):
    """
    主窗口:
        包含所有组件关联：
        - 导航栏
        - 输入面板
        - 消息展示面板
    """
    AAXW_CLASS_LOGGER:logging.Logger

    MAX_HEIGHT = 550
    def __init__(self,parent=None):
        super().__init__(parent=parent)
        self.movedCallbacks=[]

        # 初始化(界面操作相关)异步运行线程池
        self.qworkerpool=JumpinQRWorkerPool(maxThreads=10)
        
        # 设置基本窗口属性
        self.setWindowTitle("ANAN Jumpin!")
        self.setObjectName("jumpin_main_window")
        self.setStyleSheet(AAXWJumpinConfig.MAIN_WINDOWS_QSS)

        
        # 主垂直布局
        self.mainVBoxLayout = QVBoxLayout(self)
        self.mainVBoxLayout.setContentsMargins(10, 10, 10, 10)
        self.mainVBoxLayout.setSpacing(0)

        # 输入面板
        self.inputPanel = AAXWJumpinInputPanel(self,self)
        self.mainVBoxLayout.addWidget(self.inputPanel)
        self.mainVBoxLayout.addWidget(self._createAcrossLine(QFrame.Shape.HLine))

        
        # self.setWindowFlags(self.windowFlags()| Qt.WindowType.WindowStaysOnTopHint)
    
        # 内容区域容器
        self.contentContainer = QWidget(self)
        self.contentHBoxLayout = QHBoxLayout(self.contentContainer)
        self.mainVBoxLayout.addWidget(self.contentContainer)

        # 导航栏
        # self.navigationInterface = NavigationInterface(self, showMenuButton=True)
        self.navigationInterface = JumpinNavigationInterface(self,showMenuButton=True)
        
        # 初始化可切换的页面
        self.mainStackedFrame = QStackedWidget(self)

        # 使用线程安全的消息展示面板
        self.msgShowingPanel = AAXWJumpinThreadSafeMsgShowingPanel(
            mainWindow=self,
            qss=AAXWJumpinConfig.MSGSHOWINGPANEL_QSS,
            parent=self.mainStackedFrame
        )
        self.mainStackedFrame.addWidget(self.msgShowingPanel)
        


        # 默认显示消息展示面板
        self.mainStackedFrame.setCurrentWidget(self.msgShowingPanel)
        # initialize content layout
        self.initContentLayout()
        # 初始化导航栏
        self.initNavigation()

        # 初始化window
        self.initWindow()

        # 工具窗口
        self.topToolsMessageWindow = AAXWFollowerWindow(
            refWidget=self,
            refPosition=AAXWFollowerWindow.TOP,
            mainWindow=self,
            parent=self
        )
        self.leftToolsMessageWindow = AAXWFollowerWindow(
            refWidget=self,
            refPosition=AAXWFollowerWindow.LEFT,
            mainWindow=self,
            parent=self
        )
        
        self.inputPanel.promptInputEdit.setFocus()

        self.installAppHotKey()

        # 转容器关联；
        self.jumpinConfig:AAXWJumpinConfig = None #type:ignore
        self.diContainer:AAXWDependencyContainer = None #type:ignore

    def initContentLayout(self):
        self.contentHBoxLayout.setSpacing(0)
        self.contentHBoxLayout.setContentsMargins(0, 0, 0, 0)
        self.contentHBoxLayout.addWidget(self.navigationInterface)
        
        # 修改为使用mainStackedFrame
        self.contentHBoxLayout.addWidget(self.mainStackedFrame)
        self.contentHBoxLayout.setStretchFactor(self.mainStackedFrame, 1)
        #

    def initNavigation(self):
        """初始化导航栏项目"""
        self.navigationInterface.setExpandWidth(210)
        
        # 初始化导航与菜单项
        # 添加导航项
        self.navigationInterface.addItem(
            routeKey='new_interaction',
            icon=FIF.ADD,
            selectable=False,
            text='新互动',
            onClick=lambda: self.AAXW_CLASS_LOGGER.warning('新互动 clicked'),
            position=NavigationItemPosition.TOP,
            tooltip='新互动',
        )

        self.navigationInterface.addSeparator(NavigationItemPosition.TOP)


        # self.navigationInterface.addItem(
        #     routeKey='history',
        #     icon=FIF.CHAT,
        #     selectable=False,
        #     text='历史信息',
        #     onClick=lambda: print('历史信息 clicked'),
        #     position=NavigationItemPosition.SCROLL,
        #     tooltip='历史信息',
        # )
        
        self.navigationInterface.addItem(
            routeKey='all_history',
            icon=FIF.CHAT,
            selectable=False,
            text='查看所有历史',
            onClick=lambda: self.AAXW_CLASS_LOGGER.warning('历史信息 clicked'),
            position=NavigationItemPosition.SCROLL,
            tooltip='查看所有历史',
        )

        self.navigationInterface.addSeparator(NavigationItemPosition.SCROLL)


        self.navigationInterface.addItem(
            routeKey='aiagent_applet',
            icon=FIF.CHAT,
            selectable=False,
            text='伙伴与应用',
            onClick=lambda: self.AAXW_CLASS_LOGGER.warning('伙伴与应用 clicked'),
            position=NavigationItemPosition.SCROLL,
            tooltip='伙伴与应用',
        )

        # for i in range(1, 5):
        #     self.navigationInterface.addItem(
        #         routeKey=f'aiagent_applet_{i}',
        #         selectable=False,
        #         icon=FIF.FOLDER,
        #         text=f'伙伴与应用 {i}',
        #         onClick=lambda: self.AAXW_CLASS_LOGGER.warning(f'伙伴与应用 {i} clicked'),
        #         tooltip=f'伙伴与应用 {i}',
        #         # position=NavigationItemPosition.SCROLL
        #         parentRouteKey='aiagent_applet',
        #     )


        self.navigationInterface.addSeparator(NavigationItemPosition.BOTTOM)

        # self.navigationInterface.addItem(
        #     routeKey='plugins',
        #     icon=FIF.SETTING,
        #     text='插件管理',
        #     onClick=lambda: print('插件管理 clicked'),
        #     position=NavigationItemPosition.BOTTOM,
        #     tooltip='插件管理',
        # )

        # self.navigationInterface.addWidget(
        #     routeKey='brief_introduce',
        #     widget=NavigationAvatarWidget('ANAN', 'anan.png'), #
        #     onClick=self.showFirefMessageBox,
        #     position=NavigationItemPosition.BOTTOM,
        # )

        self.navigationInterface.addItem(
            routeKey='settings',
            icon=FIF.SETTING,
            text='设置',
            onClick=self.showSettingPanel,
            position=NavigationItemPosition.BOTTOM,
            tooltip='设置(含LLM模型配置)',
        )

        #默认展开导航栏
        self.navigationInterface.setMinimumExpandWidth(400)
        self.navigationInterface.expand(useAni=False)


    def initWindow(self):
        # self.resize(650, 500)
        # self.setWindowIcon(QIcon('fw_ex_res/logo.png'))
        # self.setWindowTitle('PyQt-Fluent-Widgets')
        # self.titleBar.setAttribute(Qt.WA_StyledBackground)

        self.setMinimumSize(700, 300)
        self.setMaximumSize(700, self.MAX_HEIGHT)
        
        # 设置窗口大小策略
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)
          # 初始高度 200 像素
        self.resize(self.width(), 350) 

        # desktop = QApplication.screens()[0].availableGeometry()
        # w, h = desktop.width(), desktop.height()
        # self.move(w//2 - self.width()//2, h//2 - self.height()//2)

        # self.setQss()


    def initAppRes(self):

        # 已有config
        # 设置面板加入展示堆 
        self.settingPanel = AAXWJumpinSettingPanel(
            dependencyContainer=self.diContainer,
            jumpinConfig=self.jumpinConfig,
            parent=self)
        self.mainStackedFrame.addWidget(self.settingPanel)
        
        # 初始化
        pass

    @Slot()
    def showSettingPanel(self):
        # 显示设置面板
        self.AAXW_CLASS_LOGGER.info('Settings clicked')
        self.mainStackedFrame.setCurrentWidget(self.settingPanel)
    
    @Slot()
    def showMsgShowingPanel(self):
        # 显示消息展示面板
        self.mainStackedFrame.setCurrentWidget(self.msgShowingPanel)

    # def showFirefMessageBox(self):
    #     w = MessageBox(
    #         title='ANAN欢迎您🥰',
    #         content='ANAN Jumpin 欢迎您-超级个体🚀!',
    #         parent=self
    #     )
    #     w.yesButton.setText('你也好')
    #     w.cancelButton.setText('下次一定说"你也好"')

    #     if w.exec():
    #         # QDesktopServices.openUrl(QUrl("https://xxxxx"))
    #         self.AAXW_CLASS_LOGGER.info("messagebox:你也好")

    #本来让topToolsWindow来注册的，不过用了evetFilter了。暂时没用这里。
    def registerMovedCallbacks(self, callback):
        self.movedCallbacks.append(callback)
    def _triggerMoved(self):
        for callback in self.movedCallbacks:
            callback()
    def moveEvent(self, event):
        super().moveEvent(event)
        self._triggerMoved()

    #   
    # ui初始化 end
    ##

    ##
    # 装载关联快捷键
    # 或特殊按键处理器
    ##
    def installAppHotKey(self):
        # 一般快捷键

        # 关闭（临时） install installEventFilter
        shortcut = QShortcut(QKeySequence("Alt+c"), self)  # 这里已经关联self
        shortcut.activated.connect(self.closeWindow)  # 不要加括号，指向方法；

        # top tools message window/panel show/hide
        # 使用标准快捷键格式 "Ctrl+Alt+Key" 或 "Ctrl+Key"
        # QKeySequence 需要完整的快捷键组合
        topShowOrhideSc = QShortcut(QKeySequence("Alt+1"), self)  # 添加一个具体按键T
        topShowOrhideSc.activated.connect(self.toggleVisiSubWindows)

    #
    ##
    # 装载关联快捷键
    # 特殊按键处理器
    # end
    ##

    def toggleVisiSubWindows(self):
        self.topToolsMessageWindow.toggleVisibility()
        # self.leftToolsMessageWindow.toggleVisibility()

    # 
    # 切换隐藏
    def toggleHidden(self):
        if not self.isHidden():
 
            self.setStaysOnTop(isToOn=False)
            self.hide()
        else:
            # self.setVisible(True)
            self.setStaysOnTop(isToOn=True)
            self.show()
            self.inputPanel.promptInputEdit.setFocus()
            # self.raise_() # 

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

    #
    # 根据内部部件大小调整主窗口自身大小；还是本来就有这个设置？
    def adjustHeight(self):
        # print(f"showing panel  height :{self.msgShowingPanel.height()}")

        # 获取当前显示的widget
        currentWidget = self.mainStackedFrame.currentWidget()
    
        if isinstance(currentWidget, AAXWScrollPanel):
            newHeight = (
                self.sizeHint().height()
                - currentWidget.sizeHint().height() 
                + currentWidget.expectantHeight()
            )
        else:
            # 如果不是ScrollPanel,使用默认高度
            newHeight = self.sizeHint().height()

        if newHeight > self.MAX_HEIGHT: 
            newHeight = self.MAX_HEIGHT

        self.resize(self.width(), newHeight)
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


# 全局快捷键 运行器
# 这个错误是因为在非主线程中操作了 Qt 
# 的计时器相关功能。在 Qt 中，Timer 必须在创建它的线程中启动和停止。
# 这个问题通常出现在使用全局快捷键或后台线程时。

# 继承 QObject 使用信号方式才能在非界面线程或全局快捷键操作界面
@AAXW_JUMPIN_LOG_MGR.classLogger()
class AAXWGlobalShortcut(QObject):  #继承了QObject可能就被纳入界面主线程了？
    AAXW_CLASS_LOGGER:logging.Logger
    
    # 定义信号 使用信号方式操作主窗口。
    toggleWindowSignal = Signal()

    def __init__(self, mainWindow: AAXWJumpinMainWindow):
        super().__init__()
        self.mainWindow = mainWindow
        self.hotkey = keyboard.GlobalHotKeys({"<alt>+z": self.on_activate})
        # 连接信号到主窗口的切换方法
        self.toggleWindowSignal.connect(self.mainWindow.toggleHidden)

    def on_activate(self):
        # 发送信号而不是直接调用
        self.toggleWindowSignal.emit()
        self.AAXW_CLASS_LOGGER.info("全局快捷键<alt>+z被触发")

    def start(self):
        self.hotkey.start()

    def stop(self):
        self.hotkey.stop()

@AAXW_JUMPIN_LOG_MGR.classLogger()
class AAXWJumpinTrayKit(QSystemTrayIcon):
    AAXW_CLASS_LOGGER:logging.Logger
    
    def __init__(self, main_window:AAXWJumpinMainWindow):
        super().__init__()
        
        
        self.setToolTip("AAXW Jumpin!")
        
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
        self.AAXW_CLASS_LOGGER.info("托盘菜单已初始化!")
        
        self.mainWindow:AAXWJumpinMainWindow = main_window
        
    
    def toggleHiddenMainWindow(self):
        self.mainWindow.toggleHidden()

    def closeMainWindow(self):
        #这里是不是应该关闭窗口外同时关闭app：app.quit()
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
            self.AAXW_CLASS_LOGGER.warning(f"指定的目录不存在：{directory_path}")

    def _get32QImg(self, image_path):
        """
        加载并处理图标图片，返回处理后的 QImage
        """
        try:
            # 使用 PIL 处理图片，可以避免 ICC profile 警告
            from PIL import Image
            
            # 打开并转换图片
            with Image.open(image_path) as img:
                # 移除 ICC profile
                if 'icc_profile' in img.info:
                    img = img.convert('RGBA')
                
                # 调整大小
                img = img.resize((32, 32), Image.Resampling.LANCZOS)
                
                # 转换为 QImage
                img_data = img.tobytes('raw', 'RGBA')
                qimg = QImage(img_data, img.width, img.height, QImage.Format.Format_RGBA8888)
                
                return qimg
                
        except ImportError:
            # 如果没有 PIL，回退到原始的 QImage 处理方式
            qimage = QImage(image_path)
            scaled_qimage = qimage.scaled(32, 32, 
                Qt.AspectRatioMode.KeepAspectRatio, 
                Qt.TransformationMode.SmoothTransformation)
            return scaled_qimage
