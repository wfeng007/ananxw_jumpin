#!/usr/bin/env python
# -*- coding: utf-8 -*-
## License and Notice:
# This file is part of ananxw_jumpin.
# ananxw_jumpin is licensed under the Apache2.0(the License); you may not use 
# this file except in compliance with the License. See LICENSE file for details.
# For the full license text, see the LICENSE file in the root directory.
# 
# For more copyright, warranty disclaimer, and third - party component information,
# see the NOTICE file in the root directory.
##
# @Author:wfeng007
# @Date:2024-11-04 00:35:30
# @Last Modified by:wfeng007
#
#
# 额外的内置插件。提供样例可简单使用。
#
import sys,os,time
from datetime import datetime  # Add this import
import logging
from typing  import Union, List, Dict, Any

try:
    from typing import override #python 3.12+ #type:ignore
except ImportError:
    from typing_extensions import override #python 3.8+

from PySide6.QtCore import (
    Qt, QEvent, QObject, QPoint,QThread,Signal,
)
from PySide6.QtWidgets import (
    QFrame, QWidget, QVBoxLayout, QPushButton, 
    QLabel, QToolBar,QSizePolicy, QHBoxLayout, 
    QLineEdit,QApplication, QListWidget, QListWidgetItem,
    QFileDialog,
)
# from langchain.embeddings import BCEmbeddingEmbeddings
import urllib.parse
import urllib.request
import json
import shutil


from langchain_community.chat_message_histories.file import FileChatMessageHistory
from langchain.prompts import PromptTemplate
from langchain.schema import (
        BaseMessage,
        AIMessage,  # 等价于OpenAI接口中的assistant role
        HumanMessage,  # 等价于OpenAI接口中的user role
        SystemMessage  # 等价于OpenAI接口中的system role
    )
from langchain.memory import ConversationBufferMemory
from langchain_openai import ChatOpenAI,OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain_community.document_loaders import PyMuPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders.word_document import UnstructuredWordDocumentLoader
# from langchain import Document
from langchain_core.documents import Document


# from langchain_chroma import Chroma



if __name__ == "__main__":
    # 获取当前文件的父目录的父目录（即 projectlab/）
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)  # 插入到路径最前面

#
# 在必须用 ananxw_jumpin.ananxw_jumpin_allin1f 这个方式来导入。
# （与已存在sys.modules的ananxw_jumpin_allin1f的key一致）
# 否则插件可能因为在判断AAXWAbstractBasePlugin的子类时匹配不到。
from ananxw_jumpin.ananxw_jumpin_allin1f import AAXW_JUMPIN_LOG_MGR
from ananxw_jumpin.ananxw_jumpin_allin1f import (
    AAXWAbstractApplet,AAXWDependencyContainer,
    AAXWAbstractBasePlugin,AAXWJumpinMainWindow,AAXWJumpinAppletManager,
    AAXWJumpinConfig,AAXWOllamaAIConnOrAgent,AAXWSimpleAIConnOrAgent,
    AAXWJumpinCompoMarkdownContentStrategy,
    AAXWScrollPanel,AIThread,AAXWAbstractAIConnOrAgent,
)

AAXW_JUMPIN_MODULE_LOGGER:logging.Logger=AAXW_JUMPIN_LOG_MGR.getModuleLogger(
    sys.modules[__name__])

AAXW_JUMPIN_MODULE_LOGGER.info(f"module {__name__} is running...")


##
# 1个ollama使用与简单管理的例子。
##
@AAXW_JUMPIN_LOG_MGR.classLogger(level=logging.DEBUG)
class EditableButton(QWidget):
    """
    可编辑按钮控件
    在按钮模式和编辑模式之间切换的组合控件
    """
    AAXW_CLASS_LOGGER:logging.Logger

    ##
    # 这是另一个焦点控制的方式，定制edit。可能更好。
    # class FocusLineEdit(QLineEdit):
    #     def focusOutEvent(self, event):
    #         super().focusOutEvent(event)
    #         self.parent()._showButtonMode()
    ##

    # 定义信号：当编辑完成并提交时触发
    submitted = Signal(str)  # 参数为编辑的文本内容
    editingCanceled = Signal()  # 新信号：当编辑被取消时触发（ESC或失去焦点）
    
    def __init__(self, 
            button_text: str = "", 
            placeholder_text: str = "", parent: QWidget = None  #type:ignore
        ):
        super().__init__(parent)
        self._initUI(button_text, placeholder_text)
    
    def _initUI(self, button_text: str, placeholder_text: str):
        # 创建水平布局
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # 创建按钮
        self.button = QPushButton(button_text, self)
        self.button.clicked.connect(self._showEditMode)
        
        # 创建输入框
        self.lineEdit = QLineEdit(self)
        self.lineEdit.setPlaceholderText(placeholder_text)
        self.lineEdit.hide()  # 初始隐藏
        self.lineEdit.returnPressed.connect(self._handleSubmit)
        #应用级别操作控制
        QApplication.instance().focusChanged.connect(self._handleFocusChange)
        self.lineEdit.installEventFilter(self)
        
        # 设置固定大小策略，防止挤压其他按钮
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        
        # 确保按钮有合适的初始大小
        self.button.adjustSize()
        button_size = self.button.sizeHint()
        
        # 设置输入框和按钮使用相同的大小
        self.setFixedWidth(button_size.width())
        self.lineEdit.setFixedWidth(button_size.width())
        
        # 添加到布局
        layout.addWidget(self.button)
        layout.addWidget(self.lineEdit)
    
    def eventFilter(self, obj: QObject, event: QEvent) -> bool:
        """处理特殊按键事件"""
        if obj == self.lineEdit and event.type() == QEvent.Type.KeyPress:
            if event.key() == Qt.Key.Key_Escape:
                self._showButtonMode()
                return True
        return super().eventFilter(obj, event)
    
    def _showEditMode(self):
        """切换到编辑模式"""
        button_width = self.button.width()  # 获取当前按钮宽度
        self.button.hide()
        self.lineEdit.setFixedWidth(button_width)  # 确保输入框宽度与按钮相同
        self.lineEdit.show()
        self.lineEdit.setFocus()
    
    def _showButtonMode(self):
        """切换到按钮模式"""
        self.lineEdit.hide()
        self.button.show()
        self.lineEdit.clear()
        # 发送编辑取消信号
        self.editingCanceled.emit()
    
    def _handleSubmit(self):
        """处理回车提交"""
        text = self.lineEdit.text().strip()
        if text:
            self.submitted.emit(text)
            self._showButtonMode()
    
    def setEnabled(self, enabled: bool):
        """设置控件启用状态"""
        super().setEnabled(enabled)
        self.button.setEnabled(enabled)
        self.lineEdit.setEnabled(enabled)
    
    #这个是安装到应用级别去使用的。
    def _handleFocusChange(self, old, new):
        """处理焦点变化"""
        # 添加调试日志
        # self.AAXW_CLASS_LOGGER.debug(f"Focus changed - Old: {old}, New: {new}")
        
        if old == self.lineEdit:
            if new is None:
                self.AAXW_CLASS_LOGGER.debug(
                    f"Focus moved outside application;Focus changed - Old: {old}, New: {new}")
            else:
                self.AAXW_CLASS_LOGGER.debug(
                    f"Focus moved to: {new.__class__.__name__};" +
                    f"Focus changed - Old: {old}, New: {new}"
                )
            self._showButtonMode()


@AAXW_JUMPIN_LOG_MGR.classLogger()
class OllamaDownloadModelThread(QThread):
    """Ollama模型下载线程"""
    AAXW_CLASS_LOGGER:logging.Logger
    
    # 定义信号：用于更新下载状态和进度
    updateStatus = Signal(str, dict)  # (status_msg, status_data)
    downloadFinished = Signal(bool)   # True表示成功，False表示失败
    
    def __init__(self, model_name: str, ollama_agent: AAXWOllamaAIConnOrAgent):
        super().__init__()
        self.model_name = model_name
        self.ollama_agent = ollama_agent
        self.last_update_time = 0  # 上次更新时间
        self.update_interval = 2.0  # 更新间隔（秒）
    
    def run(self):
        try:
            success = self.ollama_agent.downloadModel(
                self.model_name,
                self._statusCallback
            )
            self.downloadFinished.emit(success)
        except Exception as e:
            self.AAXW_CLASS_LOGGER.error(f"Download thread error: {str(e)}")
            self.downloadFinished.emit(False)
    
    def _statusCallback(self, status_msg: str, status_data: Dict[str, Any]):
        """
        状态回调函数，控制更新频率
        Args:
            status_msg (str): 状态消息
            status_data (Dict[str, Any]): 状态数据
        """
        self.AAXW_CLASS_LOGGER.debug(f"_statusCallback - status_msg: {status_msg}")
        current_time = time.time()
        # 检查是否达到更新间隔或是否是第一次更新
        if (current_time - self.last_update_time) >= self.update_interval or self.last_update_time == 0:
            self.updateStatus.emit(status_msg, status_data)
            self.last_update_time = current_time

@AAXW_JUMPIN_LOG_MGR.classLogger(level=logging.DEBUG)
class AAXWJumpinOllamaSimpleApplet(AAXWAbstractApplet):
    """Ollama使用及简单管理"""
    AAXW_CLASS_LOGGER:logging.Logger
    
    
    def __init__(self):
        self.name = "jumpinOllamaSimpleApplet"
        self.title = "OLAM"
        self.dependencyContainer:AAXWDependencyContainer=None #type:ignore
        self.jumpinConfig:'AAXWJumpinConfig'= None #type:ignore
        self.mainWindow:'AAXWJumpinMainWindow'=None #type:ignore

        self.backupContentBlockStrategy:AAXWContentBlockStrategy=None #type:ignore
        # self.toolsFrame=None
        
    @override
    def getName(self) -> str:
        return self.name
        
    @override 
    def getTitle(self) -> str:
        return self.title
    
    def getDesc(self) -> str:
        if AAXWJumpinOllamaSimpleApplet.__doc__:
            return AAXWJumpinOllamaSimpleApplet.__doc__ #type:ignore
        else:
            return ""

    def _getAvailableModels(self) -> Union[List[str], None]:
        """
        获取可用的Ollama模型列表
        Returns:
            List[str]: 成功时返回模型名称列表
            None: 获取失败时返回None
        """
        try:
            return self.ollamaAIConnOrAgent.listModels()
        except Exception as e:
            self.AAXW_CLASS_LOGGER.error(f"获取模型列表失败: {str(e)}")
            return None

    # 创建1个工具菜单组件-对应本applet；（界面）
    def _createToolsMessagePanel(self):
        """创建工具面板"""
        # 创建主Frame
        toolsframe = QFrame()
        toolsframe.setObjectName("toolsframe")
        toolsframe.setStyleSheet("""
            QFrame#toolsframe {
                background-color: #f0f0f0;
                border: 1px solid #ccc;
                border-radius: 5px;
            }
        """)
        layout = QVBoxLayout(toolsframe)
        
        # 创建顶部说明区域（水平布局）
        topLayout = QHBoxLayout()
        
        # 添加文本说明，设置ObjectName
        self.descLabel = QLabel(self.getDesc())
        self.descLabel.setObjectName("ollama_desc_label")
        topLayout.addWidget(self.descLabel)
        
        # 创建当前模型标签并靠右对齐
        self.currentModelLabel = QLabel(f"当前模型: {self.ollamaAIConnOrAgent.modelName}")
        self.currentModelLabel.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.currentModelLabel.setStyleSheet("padding-right: 10px;")
        topLayout.addWidget(self.currentModelLabel)
        
        layout.addLayout(topLayout)
        
        # 添加分割线
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(line)
        
        # 创建工具栏
        toolbar = QToolBar()
        
        # 创建下载模型按钮
        self.downloadButton = EditableButton("📥请下载模型", "输入模型名称")
        self.downloadButton.submitted.connect(self._handleDownloadModel)
        # 添加新的信号连接
        toolbar.addWidget(self.downloadButton)
        
        # 获取可用的Ollama模型列表
        models = self._getAvailableModels()
        if models and len(models) > 0:
            for model in models:
                button = QPushButton(model)
                button.clicked.connect(lambda checked, m=model: self._updateModel(m))
                toolbar.addWidget(button)
        elif models is None:
            # 获取模型列表失败
            errorButton = QPushButton("获取模型列表失败")
            errorButton.setEnabled(False)
            toolbar.addWidget(errorButton)
        else:
            # 模型列表为空
            errorButton = QPushButton("无可用模型")
            errorButton.setEnabled(False)
            toolbar.addWidget(errorButton)
        
        layout.addWidget(toolbar)
        return toolsframe

    def _handleDownloadModel(self, model_name: str):
        """
        处理模型下载请求
        Args:
            model_name (str): 要下载的模型名称
        """
        # 保存原始描述文本
        self.original_desc = self.getDesc()
        
        # 禁用下载按钮
        self.downloadButton.setEnabled(False)
        
        # 创建并启动下载线程
        self.downloadThread = OllamaDownloadModelThread(model_name, self.ollamaAIConnOrAgent)
        self.downloadThread.updateStatus.connect(self._updateDownloadStatus)
        self.downloadThread.downloadFinished.connect(self._handleDownloadFinished)
        self.downloadThread.start()

    def _updateDownloadStatus(self, status_msg: str, status_data: Dict[str, Any]):
        """
        更新下载状态显示
        Args:
            status_msg (str): 状态消息
            status_data (Dict[str, Any]): 状态数据
        """
        self.AAXW_CLASS_LOGGER.debug(f"_updateDownloadStatus - status_msg: {status_msg}")
        
        # 构建进度显示文本
        if status_data.get("total"):
            completed = status_data.get("completed", 0)
            total = status_data.get("total")
            progress = (completed / total) * 100
            status_text = f"下载中... {progress:.1f}% - {status_msg}"
        else:
            status_text = f"下载中... {status_msg}"
        
        # 通过ObjectName查找并更新描述标签
        desc_label = self.toolsFrame.findChild(QLabel, "ollama_desc_label")
        if desc_label:
            desc_label.setText(status_text)

    def _handleDownloadFinished(self, success: bool):
        """
        处理下载完成事件
        Args:
            success (bool): 下载是否成功
        """
        # 恢复下载按钮状态
        self.downloadButton.setEnabled(True)
        
        # 通过ObjectName查找并恢复描述标签
        desc_label = self.toolsFrame.findChild(QLabel, "ollama_desc_label")
        if desc_label:
            desc_label.setText(self.original_desc)
        
        # 重新加载模型列表
        self._refreshModelButtons()
        
        # 记录日志
        if success:
            self.AAXW_CLASS_LOGGER.info("模型下载成功")
        else:
            self.AAXW_CLASS_LOGGER.error("模型下载失败")

    def _refreshModelButtons(self):
        """刷新模型按钮列表"""
        # 获取工具栏
        toolbar = None
        for widget in self.toolsFrame.findChildren(QToolBar):
            toolbar = widget
            break
        
        if not toolbar:
            return
        
        # 清空工具栏
        toolbar.clear()
        
        # 首先添加下载按钮
        self.downloadButton = EditableButton("📥请下载模型", "输入模型名称")
        self.downloadButton.submitted.connect(self._handleDownloadModel)
        toolbar.addWidget(self.downloadButton)
        
        # 获取并添加新的模型按钮
        models = self._getAvailableModels()
        if models and len(models) > 0:
            for model in models:
                button = QPushButton(model)
                button.clicked.connect(lambda checked, m=model: self._updateModel(m))
                toolbar.addWidget(button)
        elif models is None:
            errorButton = QPushButton("获取模型列表失败")
            errorButton.setEnabled(False)
            toolbar.addWidget(errorButton)
        else:
            errorButton = QPushButton("无可用模型")
            errorButton.setEnabled(False)
            toolbar.addWidget(errorButton)

    def _updateModel(self, model_name: str):
        """
        更新当前使用的模型
        Args:
            model_name (str): 模型名称
        """
        self.ollamaAIConnOrAgent.modelName = model_name
        self.currentModelLabel.setText(f"当前模型: {model_name}")
        self.AAXW_CLASS_LOGGER.info(f"切换到模型: {model_name}")

    @override
    def onAdd(self):

        #加入管理时获取细节资源,内置简单ai访问器（Openai）
        # ai  （后台类资源默认应该都有）
        self.ollamaAIConnOrAgent:AAXWOllamaAIConnOrAgent=self.dependencyContainer.getAANode(
            "ollamaAIConnOrAgent")
       
        self.toolsFrame=self._createToolsMessagePanel()
        self.AAXW_CLASS_LOGGER.info(f"{self.name} Applet被添加")
        pass

    @override
    def onActivate(self):

        # 主要展示界面 界面可能变化，所以接货的时候获取界面内容；
        self.showingPanel=self.mainWindow.msgShowingPanel #用于展示的
        

        # 展示策略关联给 self.showingPanel
        self.backupContentBlockStrategy=self.showingPanel.contentBlockStrategy
        self.showingPanel.contentBlockStrategy=AAXWJumpinCompoMarkdownContentStrategy()

        #  将输入触发逻辑关联给inputkit
        #
        self.mainWindow.inputPanel.funcButtonRight.clicked.connect(self.doInputCommitAction)
        # self.mainWindow.inputPanel.promptInputEdit.returnPressed.connect(self.doInputCommitAction)


        #按钮标志与基本按钮曹关联
        self.mainWindow.inputPanel.funcButtonLeft.setText(self.getTitle())

        #加上工具组件
        self.mainWindow.topToolsMessageWindow.setCentralWidget(self.toolsFrame)  #type:ignore
        self.AAXW_CLASS_LOGGER.info(f"{self.name} Applet被激活")
        pass

    def doInputCommitAction(self):
        self.AAXW_CLASS_LOGGER.debug("Right button clicked!")
        text = self.mainWindow.inputPanel.promptInputEdit.text()

         # 用户输入容消息气泡与内容初始化
        rid = int(time.time() * 1000)
        self.mainWindow.msgShowingPanel.addRowContent(
            content=text, rowId=rid, contentOwner="user_xiaowang",
            contentOwnerType=AAXWScrollPanel.ROW_CONTENT_OWNER_TYPE_USER,
        )
        # self.msgShowingPanel.repaint() #重绘然后然后再等待？
        
        # 等待0.5秒
        # 使用QThread让当前主界面线程等待0.5秒 #TODO 主要为了生成rowid，没必要等待。
        QThread.msleep(500) 
        # 反馈内容消息气泡与内容初始化
        rrid = int(time.time() * 1000)
        self.mainWindow.msgShowingPanel.addRowContent(
            content="", rowId=rrid, contentOwner="assistant_aaxw",
            contentOwnerType=AAXWScrollPanel.ROW_CONTENT_OWNER_TYPE_OTHERS,
        )

        #
        #生成异步处理AI操作的线程
        #注入要用来执行的ai引擎以及 问题文本+ ui组件id
        #FIXME 执行时需要基于资源，暂时锁定输入框；
        #           多重提交，多线程处理还没很好的做，会崩溃；
        self.aiThread = AIThread(text, str(rrid), self.ollamaAIConnOrAgent)
        self.aiThread.updateUI.connect(self.mainWindow.msgShowingPanel.appendContentByRowId)
        self.aiThread.start()
       
        self._logInput()
        self.mainWindow.inputPanel.promptInputEdit.clear()
        ...
    
    def _logInput(self):
        # 打印输入框中的内容
        self.AAXW_CLASS_LOGGER.debug(f"Input: {self.mainWindow.inputPanel.promptInputEdit.text()}")


    @override
    def onInactivate(self):

        #
        self.showingPanel.contentBlockStrategy=self.backupContentBlockStrategy
        self.backupContentBlockStrategy=None #type:ignore


        #去除 槽函数
        self.mainWindow.inputPanel.funcButtonRight.clicked.disconnect(self.doInputCommitAction)
        self.mainWindow.inputPanel.promptInputEdit.returnPressed.disconnect(self.doInputCommitAction)
        self.aiThread=None

        #清理工具组件引用；
        self.mainWindow.topToolsMessageWindow.removeCentralWidget() 
        #
        self.AAXW_CLASS_LOGGER.info(f"{self.name} Applet被停用")
        pass

    @override
    def onRemove(self):
        self.ollamaAIConnOrAgent=None #type:ignore
        if self.toolsFrame:
            self.toolsFrame.deleteLater()
            self.toolsFrame = None
        self.AAXW_CLASS_LOGGER.info(f"{self.name} Applet被移除")
        pass


@AAXW_JUMPIN_LOG_MGR.classLogger()
class AAXWJumpinOllamaBuiltinPlugin(AAXWAbstractBasePlugin):
    AAXW_CLASS_LOGGER:logging.Logger

    def __init__(self) -> None:
        super().__init__()
        #plugin-mgr 会注入
        self.dependencyContainer:AAXWDependencyContainer = None #type:ignore
        self.jumpinConfig:'AAXWJumpinConfig' = None #type:ignore
        self.mainWindow:'AAXWJumpinMainWindow' = None #type:ignore
        self.jumpinAppletManager:AAXWJumpinAppletManager = None #type:ignore

    @override
    def onInstall(self):
        self.ollamaApplet=AAXWJumpinOllamaSimpleApplet()
        self.AAXW_CLASS_LOGGER.info(f"{self.__class__.__name__}.onInstall()")
        pass

    @override
    def enable(self):
        # AppletManager 本身会注入资源
        self.jumpinAppletManager.addApplet(self.ollamaApplet) 
        self.AAXW_CLASS_LOGGER.info(f"{self.__class__.__name__}.enable()")
        pass

    @override
    def disable(self):
        #去除applet的维护；
        self.jumpinAppletManager.removeAppletByInstance(self.ollamaApplet) 
        self.AAXW_CLASS_LOGGER.info(f"{self.__class__.__name__}.disable()")
        pass

    @override
    def onUninstall(self):
        self.AAXW_CLASS_LOGGER.info(f"{self.__class__.__name__}.onUninstall()")
        pass
    pass






##
# 多轮对话，交互或记忆功能及其持久化的管理器，插件与applet例子。
# chat history plugin and applet example
##

#列出指定目录对话历史（或记录）列表；
#载入项的历史记录，成为Memory/session或可进行互动操作的访问-操作器；（内部挂用LLMconn-或外层 agent进行互动操作。）
#新建一个互动Session；
@AAXW_JUMPIN_LOG_MGR.classLogger()
class HistoriedMemory:
    """封装单个对话的历史和内存"""
    AAXW_CLASS_LOGGER: logging.Logger
    
    def __init__(self, chat_id: str, memories_store_dir: str):
        self.chat_id = chat_id
        self.chat_history_path = os.path.join(memories_store_dir, f"{chat_id}_history.json")
        #如果文件不存在，自己会创建1个新的文件。
        self.message_history = FileChatMessageHistory(self.chat_history_path)
        self.memory = ConversationBufferMemory()
        
        # 加载之前的对话历史
        self.load()

    def load(self):
        """从文件中读取之前的对话历史"""
        try:
            # # 检查聊天历史文件是否存在
            # if not os.path.exists(self.chat_history_path):
            #     # 如果文件不存在，创建一个新的空文件
            #     with open(self.chat_history_path, 'w') as f:
            #         f.write('[]')  # 初始化为空的 JSON 数组

            # 加载消息
            messages: List[BaseMessage] = self.message_history.messages
            self.memory.chat_memory.add_messages(messages)
            self.AAXW_CLASS_LOGGER.info(f"加载的消息: {messages}")
        except Exception as e:
            self.AAXW_CLASS_LOGGER.warning(f"加载历史消息时发生错误: {e}")

    def save(self, message: Union[AIMessage,HumanMessage,SystemMessage]):
        """保存对话历史记录"""
        try:
            # 添加消息到内存
            self.memory.chat_memory.add_message(message)
            # 持久化写入文件
            self.message_history.add_message(message)
        except Exception as e:
            self.AAXW_CLASS_LOGGER.warning(f"保存消息时发生错误: {e}")

    def getMemory(self):
        """获取当前内存状态"""
        return self.memory.load_memory_variables({})

    def rename(self, new_chat_id: str):
        """重命名聊天历史文件并更新实例指向新的文件"""
        new_chat_history_path = os.path.join(os.path.dirname(self.chat_history_path), f"{new_chat_id}_history.json")
        
        # 检查新文件是否已存在
        if os.path.exists(new_chat_history_path):
            self.AAXW_CLASS_LOGGER.info(f"聊天历史 {new_chat_id} 已存在，无法重命名。")
            return False
        
        # 重命名文件
        os.rename(self.chat_history_path, new_chat_history_path)
        
        # 更新实例的属性
        self.chat_id = new_chat_id
        self.chat_history_path = new_chat_history_path
        self.message_history = FileChatMessageHistory(self.chat_history_path)  # 重新初始化 FileChatMessageHistory
        
        self.AAXW_CLASS_LOGGER.info(f"聊天历史已重命名为: {new_chat_id}")
        return True

@AAXW_JUMPIN_LOG_MGR.classLogger()
class FileAIMemoryManager:
    """管理多个AI(LLM) 交互或记忆功能及其持久化的管理器"""
    AAXW_CLASS_LOGGER: logging.Logger

    def __init__(self, config: AAXWJumpinConfig):
        self.config = config
        self.storeDirName = "memories"
        self.memoriesStoreDir = os.path.join(self.config.appWorkDir, self.storeDirName)
        # self._initRes()

    def initRes(self):
        """初始化存储目录"""
        self.AAXW_CLASS_LOGGER.info(f"检测到的记忆存储目录: {self.memoriesStoreDir}")
        if not os.path.exists(self.memoriesStoreDir):
            os.makedirs(self.memoriesStoreDir)

    def listMemories(self) -> List[str]:
        """列出所有聊天历史的ID"""
        return [f[
            :-len('_history.json')
        ] for f in os.listdir(self.memoriesStoreDir) if f.endswith('_history.json')]

    def loadOrCreateMemories(self, chat_id: str = None) -> HistoriedMemory: #type:ignore
        """加载指定聊天历史"""
        chId=chat_id if chat_id else self._newName() 
            
        chat_history_path = os.path.join(self.memoriesStoreDir, f"{chId}_history.json")
        print(f"准备加载或创建 {chId} 对应文件。")
        return HistoriedMemory(chId, self.memoriesStoreDir)
    
    def _newName(self) ->str :
        """Generate a new name based on time"""
        return f"interact{datetime.now().strftime('%Y%m%d%H%M%S')}"



@AAXW_JUMPIN_LOG_MGR.classLogger()
class AAXWJumpinChatHistoryExpApplet(AAXWAbstractApplet):
    """对话历史保存Applet样例"""
    AAXW_CLASS_LOGGER: logging.Logger

    def __init__(self):
        self.name = "jumpinChatHistoryApplet"
        self.title = "CHIS"
        self.dependencyContainer: AAXWDependencyContainer = None  # type: ignore
        self.jumpinConfig: 'AAXWJumpinConfig' = None  # type: ignore
        self.mainWindow: 'AAXWJumpinMainWindow' = None  # type: ignore
        

    @override
    def getName(self) -> str:
        return self.name

    @override
    def getTitle(self) -> str:
        return self.title
    
    def getDesc(self) -> str:
        return self.__class__.__doc__ if self.__class__.__doc__ else "..."
        # if self.__class__.__doc__:
        #     return self.__class__.__doc__ #type:ignore
        # else:
        #     return ""

    def _toggleLeftWindows(self): 
        """保存聊天历史到本地文件"""
        # 
        self.AAXW_CLASS_LOGGER.info("打开/关闭历史记录列表")
        self.mainWindow.leftToolsMessageWindow.toggleVisibility()


    # 创建1个工具菜单组件-对应本applet；（界面）
    def _createToolsMessagePanel(self):
        """创建工具面板"""
        # 创建主Frame
        toolsframe = QFrame()
        toolsframe.setObjectName("chat_history_toolsframe")
        toolsframe.setStyleSheet("""
            QFrame#chat_history_toolsframe {
                background-color: #f0f0f0;
                border: 1px solid #ccc;
                border-radius: 5px;
            }
        """)
        layout = QVBoxLayout(toolsframe)


        # 添加文本说明，设置ObjectName
        self.descLabel = QLabel(self.getDesc())
        self.descLabel.setObjectName("desc_label")
        layout.addWidget(self.descLabel)
        
        # 添加分割线
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(line)


        # 创建工具栏
        toolbar = QToolBar()
        
        # 创建保存聊天历史按钮
        left_win_button = QPushButton("<<<")
        left_win_button.clicked.connect(self._toggleLeftWindows)
        toolbar.addWidget(left_win_button)

        layout.addWidget(toolbar)
        return toolsframe

       
    def _createHistoriedMemoriesPanel(self) -> QListWidget:
        """创建一个用于展示历史聊天或记忆记录的面板"""
        # 创建 QListWidget 用于展示历史记录
        self.memories_list_widget = QListWidget()

        # 调用刷新方法来填充历史记录
        self._refreshMemoriesList()

        return self.memories_list_widget


    def on_item_clicked(self, item: QListWidgetItem):
        """处理点击事件"""
        if item.text() == "--New 新增--":
            self.create_new_memory()
        else:
            chat_id = item.text()  # 获取被点击项的文本内容
            self.load_memory(chat_id)  # 调用加载方法





    def _refreshMemoriesList(self):
        """刷新历史记录列表"""
        # 先断开之前的连接
        self.memories_list_widget.itemClicked.disconnect(self.on_item_clicked)

        self.memories_list_widget.clear()  # 清空当前列表

        # 添加默认项
        default_item = QListWidgetItem("--New 新增--")
        self.memories_list_widget.addItem(default_item)

        # 重新连接信号
        self.memories_list_widget.itemClicked.connect(self.on_item_clicked)

        # 获取最新的历史记录
        mems = self.historiedMemoryManager.listMemories()
        for record in mems:
            # 创建 QListWidgetItem，直接设置文本为聊天名称或 ID
            list_item = QListWidgetItem(record)  # 这里的 record 应该是聊天名称或 ID
            self.memories_list_widget.addItem(list_item)


    @override
    def onAdd(self):

        self.simpleAIConnOrAgent:AAXWSimpleAIConnOrAgent=self.dependencyContainer.getAANode(
            "simpleAIConnOrAgent")

        self.currentHistoriedMemory:HistoriedMemory=None #type:ignore
        
        self.historiedMemoryManager=FileAIMemoryManager(self.jumpinConfig)
        self.historiedMemoryManager.initRes()
        #
        self.toolsFrame=self._createToolsMessagePanel()
        self.memoryListFrame=self._createHistoriedMemoriesPanel()
        self.AAXW_CLASS_LOGGER.info(f"{self.name} Applet被添加")
        pass

    @override
    def onRemove(self):
        if self.memoryListFrame:
            self.memoryListFrame.deleteLater()
            self.memoryListFrame = None
    
        if self.toolsFrame:
            self.toolsFrame.deleteLater()
            self.toolsFrame = None

        self.AAXW_CLASS_LOGGER.info(f"{self.name} Applet被移除")
        pass


    @override
    def onActivate(self):
        # 
        
        
        # 主要展示界面 界面可能变化，所以接货的时候获取界面内容；
        self.showingPanel=self.mainWindow.msgShowingPanel #用于展示的
        

        # 展示策略关联给 self.showingPanel
        self.backupContentBlockStrategy=self.showingPanel.contentBlockStrategy
        self.showingPanel.contentBlockStrategy=AAXWJumpinCompoMarkdownContentStrategy()

        #  将输入触发逻辑关联给inputkit
        #
        self.mainWindow.inputPanel.funcButtonRight.clicked.connect(self.doInputCommitAction)


        #按钮标志与基本按钮曹关联
        self.mainWindow.inputPanel.funcButtonLeft.setText(self.getTitle())

        #加上工具组件
        self.mainWindow.topToolsMessageWindow.setCentralWidget(self.toolsFrame)  #type:ignore

        #加上左侧列表 
        self.mainWindow.leftToolsMessageWindow.setCentralWidget(self.memoryListFrame) #type:ignore
        self.AAXW_CLASS_LOGGER.info(f"{self.name} Applet被激活")
        pass

    @override
    def onInactivate(self):
        #
        self.showingPanel.contentBlockStrategy=self.backupContentBlockStrategy #type:ignore 
        self.backupContentBlockStrategy=None #type:ignore


        #去除 槽函数
        self.mainWindow.inputPanel.funcButtonRight.clicked.disconnect(self.doInputCommitAction)
        self.aiThread=None

        #
        self.mainWindow.leftToolsMessageWindow.removeCentralWidget()

        #清理工具组件引用；
        self.mainWindow.topToolsMessageWindow.removeCentralWidget() 
        #
        self.AAXW_CLASS_LOGGER.info(f"{self.name} Applet被停用")
        pass

    def create_new_memory(self):
        """创建新的对话和记忆"""
        self.AAXW_CLASS_LOGGER.info("创建新的对话和记忆")
        #创建1个新的chat/memo 并且作为当前chat/memo
        self.currentHistoriedMemory=self.historiedMemoryManager.loadOrCreateMemories()
        #刷新列表展示
        self._refreshMemoriesList()

    def load_memory(self, chat_id: str):
        """加载指定的聊天历史或记忆"""
        self.AAXW_CLASS_LOGGER.info(f"加载聊天历史: {chat_id}")
        
        self.currentHistoriedMemory = self.historiedMemoryManager.loadOrCreateMemories(chat_id)
        
        #清理
        self.mainWindow.msgShowingPanel.clearContent()
        
        # 使用类似steaming方式逐步更新界面；模拟AIThread处理。即可。
        # 创建并启动加载历史消息的线程
        # self.loadMemoryThread = self.LoadMemoryThread(self.currentHistoriedMemory)
        # self.loadMemoryThread.addRowContentSignal.connect(self.addRowContent)  # 连接添加行内容信号
        # self.loadMemoryThread.appendContentSignal.connect(self.appendContent)    # 连接追加内容信号
        # self.loadMemoryThread.start()  # 启动线程

        # 同步方式 不容易崩溃？
        self._mockAIUpdateUI()

    def addRowContent(self, content: str, rowId: str, contentOwner: str,contentOwnerType:str):
        """添加行内容的槽函数"""
        self.mainWindow.msgShowingPanel.addRowContent(
            content=content, rowId=rowId, contentOwner=contentOwner, 
            contentOwnerType=contentOwnerType
        )

    def appendContent(self, content: str, rowId: str):
        """追加内容的槽函数"""
        self.mainWindow.msgShowingPanel.appendContentByRowId(content, rowId=rowId)
        # 同步更新界面会阻塞界面- 参考_mockAIUpdateUI方法。
       

    @AAXW_JUMPIN_LOG_MGR.classLogger()
    class LoadMemoryThread(QThread):
        """用于加载历史消息并更新UI的线程"""
        AAXW_CLASS_LOGGER: logging.Logger
        addRowContentSignal = Signal(str, str, str,str)  # (内容, rowId, contentOwner,contentOwnerType)
        appendContentSignal = Signal(str, str)        # (内容, rowId)

        def __init__(self, memory: HistoriedMemory):
            super().__init__()
            self.memory = memory

        def run(self):
            """线程运行方法"""
            messages = self.memory.message_history.messages
            for msg in messages:
                rowId = str(datetime.now().timestamp())
                if isinstance(msg, HumanMessage):
                    user_content = msg.content
                    self.addRowContentSignal.emit(user_content, rowId, "user",
                        AAXWScrollPanel.ROW_CONTENT_OWNER_TYPE_USER)  # 通过信号更新用户消息
                elif isinstance(msg, AIMessage):
                    self.addRowContentSignal.emit("", rowId,"ai",
                        AAXWScrollPanel.ROW_CONTENT_OWNER_TYPE_OTHERS)  # 发送占位符
                    self.msleep(300)  # 模拟延迟
                    ai_content = msg.content
                    ai_content = str(ai_content)
                    for chunk in ai_content.splitlines(keepends=True):
                        self.appendContentSignal.emit(chunk, rowId)  # 通过信号更新AI消息
                        self.msleep(100)
                self.msleep(300)  # 模拟延迟

    def _mockAIUpdateUI(self):
        """模拟更新UI的方法，循环读取消息并更新界面"""
        messages = self.currentHistoriedMemory.message_history.messages

        # 遍历消息并更新UI
        for msg in messages:
            if isinstance(msg, HumanMessage):
                # 处理用户消息
                user_content = msg.content
                # 使用 addRowContent 方法添加用户消息
                self.mainWindow.msgShowingPanel.addRowContent(user_content, rowId=str(datetime.now().timestamp()), contentOwner="user", contentOwnerType=self.mainWindow.msgShowingPanel.ROW_CONTENT_OWNER_TYPE_USER)
            
            elif isinstance(msg, AIMessage):
                # 处理AI消息
                ai_content = msg.content
                # 生成一个唯一的 rowId
                rowId = str(datetime.now().timestamp())
                # 添加一个空内容行作为占位符
                self.mainWindow.msgShowingPanel.addRowContent("", rowId=rowId, contentOwner="ai", contentOwnerType=self.mainWindow.msgShowingPanel.ROW_CONTENT_OWNER_TYPE_OTHERS)

                # 确保 ai_content 是字符串类型
                ai_content = str(ai_content)  # 添加此行以确保类型正确
                # 模拟流式更新AI消息
                for chunk in ai_content.splitlines(keepends=True):  # 保留换行符
                    # 使用 appendContentByRowId 方法追加AI消息
                    self.mainWindow.msgShowingPanel.appendContentByRowId(chunk, rowId=rowId)
                    time.sleep(0.05)  # 模拟延迟，给用户更好的体验

            time.sleep(0.1)  # 模拟延迟，给用户更好的体验

    def doInputCommitAction(self):
        self.AAXW_CLASS_LOGGER.debug("Right button clicked!")
        text = self.mainWindow.inputPanel.promptInputEdit.text()

         # 用户输入容消息气泡与内容初始化
        rid = int(time.time() * 1000)
        self.mainWindow.msgShowingPanel.addRowContent(
            content=text, rowId=rid, contentOwner="user_xiaowang",
            contentOwnerType=AAXWScrollPanel.ROW_CONTENT_OWNER_TYPE_USER,
        )
        # self.msgShowingPanel.repaint() #重绘然后然后再等待？
        
        # 等待0.5秒
        # 使用QThread让当前主界面线程等待0.5秒 #TODO 主要为了生成rowid，没必要等待。
        QThread.msleep(500) 
        # 反馈内容消息气泡与内容初始化
        rrid = int(time.time() * 1000)
        self.mainWindow.msgShowingPanel.addRowContent(
            content="", rowId=rrid, contentOwner="assistant_aaxw",
            contentOwnerType=AAXWScrollPanel.ROW_CONTENT_OWNER_TYPE_OTHERS,
        )

        #
        #生成异步处理AI操作的线程
        #注入要用来执行的ai引擎以及 问题文本+ ui组件id
        #FIXME 执行时需要基于资源，暂时锁定输入框；
        #           多重提交，多线程处理还没很好的做，会崩溃；

        # 暂时使用当前HistoriedMemory
        if self.currentHistoriedMemory is None:
            self.currentHistoriedMemory=self.historiedMemoryManager.loadOrCreateMemories()
            #刷新列表展示
            self._refreshMemoriesList() #需要信号发送去执行；这里是doInputCommitAction本身是槽函数
            
            
            

        self.aiThread = self.MemoAIThread(
            text, str(rrid), self.simpleAIConnOrAgent, self.currentHistoriedMemory)
        self.aiThread.updateUI.connect(self.mainWindow.msgShowingPanel.appendContentByRowId)
        self.aiThread.start()
       
        self.mainWindow.inputPanel.promptInputEdit.clear()

        ...

    @AAXW_JUMPIN_LOG_MGR.classLogger()#level=logging.INFO
    class MemoAIThread(AIThread):
        AAXW_CLASS_LOGGER: logging.Logger

        PROMPT_TEMPLE=PromptTemplate(
            input_variables=["chat_history", "question"],
            template="根据之前的对话历史:'{chat_history}'; 回答相关问题:{question}"
        )

        #newContent,id 对应：ShowingPanel.appendToContentById 回调
        updateUI = Signal(str,str)  

        def __init__(self,text:str,uiCellId:str,llmagent:AAXWAbstractAIConnOrAgent,
                hMemo:HistoriedMemory):
            #

            super().__init__(text=text,uiCellId=uiCellId,llmagent=llmagent)
            self.hMemo=hMemo
            self.wholeResponse=""
            
        
            
        def run(self):
            self.msleep(500)  # 执行前先等界面渲染
            exec_e=None
            prompted=self.text
            try:
                #onstart
                #这里应该增加合并 历史信息到指定模版位置
                if self.text:

                    #获取历史信息,并基于历史memo/chat构建提示词；
                    hMsgs=self.hMemo.memory.chat_memory.messages
                    chat_history_str = "\n".join([str(msg.content) for msg in hMsgs])
                    prompted=self.PROMPT_TEMPLE.format(
                        chat_history=chat_history_str, question=self.text)
                    human_message = HumanMessage(content=self.text)

                    #只记录 question/当前命令（不包含构建的完整prompt）
                    self.hMemo.save(human_message)
                else:
                    return #直接结束没有提问题内容
                self.AAXW_CLASS_LOGGER.debug(f"将向LLM发送完整提示词: {prompted}")
                self.llmagent.requestAndCallback(prompted, self.onResponse)
            except Exception as e:
                self.AAXW_CLASS_LOGGER.error(f"An exception occurred: {str(e)}")
                exec_e=e
                # raise e
            finally:
                #onfinish
                if exec_e is None and self.wholeResponse: #没有异常才写入库
                    ai_message = AIMessage(content=self.wholeResponse)
                    self.hMemo.save(ai_message)
                pass

        def onResponse(self,str):
            self.wholeResponse += str
            self.callUpdateUI(str)
         

@AAXW_JUMPIN_LOG_MGR.classLogger()
class AAXWJumpinChatHistoryExpPlugin(AAXWAbstractBasePlugin):
    AAXW_CLASS_LOGGER: logging.Logger

    def __init__(self) -> None:
        super().__init__()
        self.dependencyContainer: AAXWDependencyContainer = None  # type: ignore
        self.jumpinConfig: 'AAXWJumpinConfig' = None  # type: ignore
        self.mainWindow: 'AAXWJumpinMainWindow' = None  # type: ignore
        self.jumpinAppletManager: AAXWJumpinAppletManager = None  # type: ignore

    @override
    def onInstall(self):
        self.chatHistoryApplet = AAXWJumpinChatHistoryExpApplet()
        self.AAXW_CLASS_LOGGER.info(f"{self.__class__.__name__}.onInstall()")
        pass

    @override
    def enable(self):
        self.jumpinAppletManager.addApplet(self.chatHistoryApplet)
        self.AAXW_CLASS_LOGGER.info(f"{self.__class__.__name__}.enable()")
        pass

    @override
    def disable(self):
        self.jumpinAppletManager.removeAppletByInstance(self.chatHistoryApplet)
        self.AAXW_CLASS_LOGGER.info(f"{self.__class__.__name__}.disable()")
        pass

    @override
    def onUninstall(self):
        self.AAXW_CLASS_LOGGER.info(f"{self.__class__.__name__}.onUninstall()")
        pass






##
# 代知识库实现案例；
# RAG基础实现之一；
##

# 简单知识库实现， chroma，openai-embedding，pypdf
# TODO 增加metadata 写入辨别来源。
@AAXW_JUMPIN_LOG_MGR.classLogger()
class FileChromaKBS:
    '''文件，chroma方式存储的知识库系统(KBS)。用于RAG等AI相关功能的知识保存与检索。'''
    AAXW_CLASS_LOGGER: logging.Logger

    def __init__(self):
        self.jumpinConfig: AAXWJumpinConfig = None  # type: ignore
        self.chromaDbDirNmae = "chroma_db"
        self.kbsStoreDirName = "kbs_store"

        pass


    def initRes(self):
        """初始化知识库资源"""

        self.chromaDbDir = os.path.join(
            self.jumpinConfig.appWorkDir, self.chromaDbDirNmae)
        self.kbsStoreDir = os.path.join(
            self.jumpinConfig.appWorkDir, self.kbsStoreDirName)
        
        if not os.path.exists(self.kbsStoreDir):
            os.makedirs(self.kbsStoreDir)
        if not os.path.exists(self.kbsStoreDir):
            os.makedirs(self.kbsStoreDir)

        # text-embedding-ada-002
        self.embeddings = OpenAIEmbeddings(model="text-embedding-ada-002")
        self.vectorstore:Chroma = Chroma(
            persist_directory=self.chromaDbDir , 
            embedding_function=self.embeddings #embedding模型指定
        )
        self.AAXW_CLASS_LOGGER.info(
            f"已初始化知识库资源。文件目录: {self.kbsStoreDir}，chroma库位置:{self.chromaDbDir}")

    
    # def _connStoreAndDb(self):

    def addDocument(self, filePath: str, collectionName: str = None) -> bool: #type:ignore
        """
        添加文档到知识库
        Args:
            file_path (str): 源文件路径
            collection_name (str): 集合名称，默认为None，使用默认collection
        Returns:
            bool: 是否成功添加
        """
        try:
            # 获取文件名和扩展名
            file_name = os.path.basename(filePath)
            file_ext = os.path.splitext(file_name)[1].lower()[1:]  # 移除点号
            
            # 检查文件类型
            supported_extensions = {'pdf', 'doc', 'docx'}
            if file_ext not in supported_extensions:
                self.AAXW_CLASS_LOGGER.error(f"不支持的文件类型: {file_ext}")
                return False
                
            # 复制文件到存储目录
            target_path = os.path.join(self.kbsStoreDir, file_name)
            
            if os.path.exists(target_path):
                self.AAXW_CLASS_LOGGER.warning(f"文件已存在并将被覆盖: {target_path}")
            shutil.copy2(filePath, target_path)
            
            # 使用默认或指定的 collection
            if collectionName:
                vectorstore = Chroma(
                    collection_name=collectionName,
                    persist_directory=self.chromaDbDir,
                    embedding_function=self.embeddings
                )
            else:
                vectorstore = self.vectorstore
            
            
            # 根据文件类型选择加载器
            try:
                if file_ext == "pdf":
                    loader = PyMuPDFLoader(target_path)
                elif file_ext in ["doc", "docx"]:
                    loader = UnstructuredWordDocumentLoader(target_path)
                else:
                    raise NotImplementedError(f"文件扩展名 {file_ext} 不支持")
                    
                raw_docs = loader.load()
                
            except Exception as e:
                self.AAXW_CLASS_LOGGER.error(f"加载文档失败: {str(e)}")
                if os.path.exists(target_path):
                    os.remove(target_path)
                return False
            
            if not raw_docs:
                self.AAXW_CLASS_LOGGER.warning("文档内容为空")
                return False
            
            # 切分文档，并为每个片段添加元数据
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=200,
                chunk_overlap=100,
                length_function=len,
                add_start_index=True,
            )
            documents: List[Document] = text_splitter.split_documents(raw_docs)
            
            # 为每个文档片段添加元数据
            for doc in documents:
                doc.metadata.update({
                    "source_file": file_name,
                    "file_path": target_path,
                    "file_type": file_ext,
                    "collection": self.vectorstore._collection_name, #TODO 需要更合理的获取
                    "chunk_size": 200,
                    "chunk_overlap": 100
                })
            
            if not documents:
                self.AAXW_CLASS_LOGGER.error("文档切分失败")
                return False
            
            # 添加到向量存储
            vectorstore.add_documents(documents)
            
            self.AAXW_CLASS_LOGGER.info(f"成功添加文档到集合 {collectionName or 'default'}: {file_name}")
            return True
            
        except Exception as e:
            self.AAXW_CLASS_LOGGER.error(f"添加文档到集合 {collectionName or 'default'} 失败: {str(e)}")
            if os.path.exists(target_path):
                os.remove(target_path)
            return False


    def search(self, query: str, k: int = 3, collection_name: str = None) -> List[Document]: #type:ignore
        """
        在知识库中搜索相关内容
        Args:
            query (str): 搜索查询文本
            k (int): 返回的最相关文档数量，默认为3
            collection_name (str): 集合名称，默认为None，使用默认collection
        Returns:
            List[Document]: 相关文档列表，如果出错返回空列表
        Note:
            - 获取文档元数据：每个Document对象包含metadata属性，可以通过doc.metadata访问。
            - 元数据通常在addDocument函数中添加，例如文件名、文件路径等。
            doc.metadata结构：
            {
                        "source_file": xxx,
                        "file_path": xxx,
                        "file_type": xxx,
                        "collection": xxx,
                        "chunk_size": xxx,
                        "chunk_overlap": xxx
            }
        """
        try:
            # 使用默认或指定的 collection
            if collection_name:
                vectorstore = Chroma(
                    collection_name=collection_name,
                    persist_directory=self.chromaDbDir,
                    embedding_function=self.embeddings
                )
            else:
                vectorstore = self.vectorstore

            # 使用向量存储的相似度搜索
            docs = vectorstore.similarity_search(
                query=query,
                k=k
            )
            
            self.AAXW_CLASS_LOGGER.info(f"在集合 {collection_name or 'default'} 中搜索成功，找到 {len(docs)} 条相关内容")
            return docs
            
        except Exception as e:
            self.AAXW_CLASS_LOGGER.error(f"在集合 {collection_name or 'default'} 中搜索失败: {str(e)}")
            return []
    
    def removeDocument(self):
        ...

    def _reloadDocument(self):
        ...
    
    def documentMeta(self):
        ...

    def listDocuments(self):
        ...

    def _reloadKBS(self):
            ...

#
@AAXW_JUMPIN_LOG_MGR.classLogger()
class AAXWJumpinKBSApplet(AAXWAbstractApplet):
    """1个知识库的使用样例"""
    AAXW_CLASS_LOGGER: logging.Logger

    def __init__(self):
        self.name = "jumpinKBSApplet"  # 修正名称
        self.title = "KBS"
        self.dependencyContainer: AAXWDependencyContainer = None  # type: ignore
        self.jumpinConfig: 'AAXWJumpinConfig' = None  # type: ignore
        self.mainWindow: 'AAXWJumpinMainWindow' = None  # type: ignore
        self.aiThread = None  # 添加AI线程属性

    @override
    def getName(self) -> str:
        return self.name

    @override
    def getTitle(self) -> str:
        return self.title
    
    def getDesc(self) -> str:
        return self.__class__.__doc__ if self.__class__.__doc__ else "..."
        # if self.__class__.__doc__:
        #     return self.__class__.__doc__ #type:ignore
        # else:
        #     return ""

    def _createToolsMessagePanel(self):
        """创建工具面板"""
        # 创建主Frame
        toolsframe = QFrame()
        toolsframe.setObjectName("kbs_toolsframe")
        toolsframe.setStyleSheet("""
            QFrame#kbs_toolsframe {
                background-color: #f0f0f0;
                border: 1px solid #ccc;
                border-radius: 5px;
            }
        """)
        layout = QVBoxLayout(toolsframe)
        
        # 创建顶部说明区域（水平布局）
        topLayout = QHBoxLayout()
        
        # 添加文本说明，设置ObjectName
        self.descLabel = QLabel(self.getDesc())
        self.descLabel.setObjectName("kbs_desc_label")
        topLayout.addWidget(self.descLabel)
        
        # 创建状态标签并靠右对齐
        self.statusLabel = QLabel("就绪")
        self.statusLabel.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.statusLabel.setStyleSheet("padding-right: 10px;")
        topLayout.addWidget(self.statusLabel)
        
        layout.addLayout(topLayout)
        
        # 添加分割线
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(line)
        
        # 创建工具栏
        toolbar = QToolBar()
        
        # 创建上传文件按钮
        uploadButton = QPushButton("📄 上传材料")
        uploadButton.clicked.connect(self._handleUploadFile)
        toolbar.addWidget(uploadButton)
        
        # 创建第二个按钮
        button2 = QPushButton("按钮2")
        button2.clicked.connect(lambda: self.AAXW_CLASS_LOGGER.info("按钮2被点击"))
        toolbar.addWidget(button2)
        
        # 创建第三个按钮
        button3 = QPushButton("按钮3")
        button3.clicked.connect(lambda: self.AAXW_CLASS_LOGGER.info("按钮3被点击"))
        toolbar.addWidget(button3)
        
        layout.addWidget(toolbar)
        return toolsframe

    #FIXME 改为异步处理上传与灌库。需要增加过程或进度获取，得到类似streaming的效果
    #FIXME 上传时需要锁定界面特定功能。
    def _handleUploadFile(self):
        """处理文件上传"""
       
        
        # 打开文件选择对话框
        file_path, _ = QFileDialog.getOpenFileName(
            self.mainWindow,
            "选择文件",
            "",
            "文档文件 (*.pdf *.doc *.docx)"
        )
        
        if file_path:
            self.AAXW_CLASS_LOGGER.info(f"选择的文件: {file_path}")
            self.statusLabel.setText("正在处理文件...")
            
            try:
                # 调用知识库的添加文档方法
                success = self.kbs.addDocument(file_path)
                
                if success:
                    self.statusLabel.setText("文件添加成功")
                    self.AAXW_CLASS_LOGGER.info(f"文件 {file_path} 已成功添加到知识库")
                else:
                    self.statusLabel.setText("文件添加失败")
                    self.AAXW_CLASS_LOGGER.error(f"文件 {file_path} 添加失败")
            
            except Exception as e:
                self.statusLabel.setText("处理出错")
                self.AAXW_CLASS_LOGGER.error(f"处理文件时发生错误: {str(e)}")

    @override
    def onAdd(self):
        # 获取AI代理
        self.simpleAIConnOrAgent: AAXWSimpleAIConnOrAgent = self.dependencyContainer.getAANode(
            "simpleAIConnOrAgent")
        
        # TODO之后初始化知识库系统
        # applet初始化时就初始化 kbs知识库系统。
        self.kbs = FileChromaKBS()
        self.kbs.jumpinConfig = self.jumpinConfig
        self.kbs.initRes()
        #

        
        self.toolsFrame = self._createToolsMessagePanel()
        self.AAXW_CLASS_LOGGER.info(f"{self.name} Applet被添加")
       # 创建1个工具菜单组件-对应本applet；（界面）

    @override
    def onActivate(self):
        # 主要展示界面 界面可能变化，所以接货的时候获取界面内容；
        self.showingPanel=self.mainWindow.msgShowingPanel #用于展示的
        

        # 展示策略关联给 self.showingPanel
        self.backupContentBlockStrategy=self.showingPanel.contentBlockStrategy
        self.showingPanel.contentBlockStrategy=AAXWJumpinCompoMarkdownContentStrategy()

        #  将输入触发逻辑关联给inputkit
        #
        self.mainWindow.inputPanel.funcButtonRight.clicked.connect(self.doInputCommitAction)

        #按钮标志与基本按钮曹关联
        self.mainWindow.inputPanel.funcButtonLeft.setText(self.getTitle())

        #加上工具组件
        self.mainWindow.topToolsMessageWindow.setCentralWidget(self.toolsFrame)  #type:ignore
        self.AAXW_CLASS_LOGGER.info(f"{self.name} Applet被激活")

    
    @AAXW_JUMPIN_LOG_MGR.classLogger(level=logging.DEBUG)
    class KBSAIThread(AIThread):
        AAXW_CLASS_LOGGER: logging.Logger

        PROMPT_TEMPLE=PromptTemplate(
            input_variables=["chat_history", "question", "knowledge"],
            template="根据之前的对话历史:'{chat_history}'; 结合以下知识:'{knowledge}'; 请以中文，回答如下相关问题:{question}"
        )

        updateUI = Signal(str,str)  

        def __init__(self, text: str, uiCellId: str, llmagent: AAXWAbstractAIConnOrAgent, kbs: FileChromaKBS):
            super().__init__(text=text, uiCellId=uiCellId, llmagent=llmagent)
            self.kbs = kbs
            self.wholeResponse = ""

        def run(self):
            self.msleep(500)  # 执行前先等界面渲染
            exec_e = None
            prompted = self.text
            try:
                if self.text:
                    # 从知识库中搜索相关内容
                    docs = self.kbs.search(query=self.text, k=3)
                    knowledge = "\n".join([doc.page_content for doc in docs])

                    # 构建提示词
                    prompted = self.PROMPT_TEMPLE.format(
                        chat_history="",  # 如果有历史记录，可以在此处添加
                        question=self.text,
                        knowledge=knowledge
                    )
                    self.AAXW_CLASS_LOGGER.debug(f"将向LLM发送完整提示词: {prompted}")
                    self.llmagent.requestAndCallback(prompted, self.onResponse)
                else:
                    return  # 直接结束没有提问题内容
            except Exception as e:
                self.AAXW_CLASS_LOGGER.error(f"An exception occurred: {str(e)}")
                exec_e = e
            finally:
                if exec_e is None and self.wholeResponse:  # 没有异常才写入库
                    # ai_message = AIMessage(content=self.wholeResponse)
                    # 这里加入无异常的finally处理。
                    pass

                pass

        def onResponse(self, str):
            self.wholeResponse += str
            self.callUpdateUI(str)

    def doInputCommitAction(self):
        """处理输入提交动作"""
        self.AAXW_CLASS_LOGGER.debug("Right button clicked!")
        text = self.mainWindow.inputPanel.promptInputEdit.text()

        # 用户输入消息气泡初始化
        rid = int(time.time() * 1000)
        self.mainWindow.msgShowingPanel.addRowContent(
            content=text, 
            rowId=rid, 
            contentOwner="user_xiaowang",
            contentOwnerType=AAXWScrollPanel.ROW_CONTENT_OWNER_TYPE_USER,
        )
        
        # 等待界面渲染
        QThread.msleep(500)
        
        # AI响应消息气泡初始化
        rrid = int(time.time() * 1000)
        self.mainWindow.msgShowingPanel.addRowContent(
            content="", 
            rowId=rrid, 
            contentOwner="assistant_aaxw",
            contentOwnerType=AAXWScrollPanel.ROW_CONTENT_OWNER_TYPE_OTHERS,
        )

        # 创建并启动AI处理线程
        self.aiThread = self.KBSAIThread(text, str(rrid), self.simpleAIConnOrAgent, self.kbs)
        self.aiThread.updateUI.connect(self.mainWindow.msgShowingPanel.appendContentByRowId)
        self.aiThread.start()
       
        self._logInput()
        self.mainWindow.inputPanel.promptInputEdit.clear()

    def _logInput(self):
        """记录输入内容"""
        self.AAXW_CLASS_LOGGER.debug(
            f"Input: {self.mainWindow.inputPanel.promptInputEdit.text()}")

    @override
    def onInactivate(self):
        #
        self.showingPanel.contentBlockStrategy=self.backupContentBlockStrategy #type:ignore 
        self.backupContentBlockStrategy=None #type:ignore

        #去除 槽函数
        self.mainWindow.inputPanel.funcButtonRight.clicked.disconnect(self.doInputCommitAction)
        # self.mainWindow.inputPanel.promptInputEdit.returnPressed.disconnect(self.doInputCommitAction)
        self.aiThread=None

        #清理工具组件引用；
        self.mainWindow.topToolsMessageWindow.removeCentralWidget() 
        #

        self.AAXW_CLASS_LOGGER.info(f"{self.name} Applet被停用")
        pass

    @override
    def onRemove(self):
        if self.toolsFrame:
            self.toolsFrame.deleteLater()
            self.toolsFrame = None
        self.AAXW_CLASS_LOGGER.info(f"{self.name} Applet被移除")
        pass


@AAXW_JUMPIN_LOG_MGR.classLogger()
class AAXWJumpinKBSPlugin(AAXWAbstractBasePlugin):
    AAXW_CLASS_LOGGER: logging.Logger

    def __init__(self) -> None:
        # 初始化插件，并将插件管理器中需要的资源置为None
        super().__init__()
        self.dependencyContainer: AAXWDependencyContainer = None  # 插件依赖管理器 #type:ignore
        self.jumpinConfig: 'AAXWJumpinConfig' = None  # 插件配置对象 #type:ignore
        self.mainWindow: 'AAXWJumpinMainWindow' = None  # 主窗口对象 #type:ignore
        self.jumpinAppletManager: AAXWJumpinAppletManager = None  # 小程序管理器 #type:ignore

    @override
    def onInstall(self):
        # 安装插件时的操作
        self.kbsApplet = AAXWJumpinKBSApplet()  # 创建一个小程序示例
        self.AAXW_CLASS_LOGGER.info(f"{self.__class__.__name__}.onInstall()")  # 记录安装日志
        pass

    @override
    def enable(self):
        # 启用插件时的操作
        self.jumpinAppletManager.addApplet(self.kbsApplet)  # 将小程序添加到管理器中
        self.AAXW_CLASS_LOGGER.info(f"{self.__class__.__name__}.enable()")  # 记录启用日志
        pass

    @override
    def disable(self):
        # 禁用插件时的操作
        self.jumpinAppletManager.removeAppletByInstance(self.kbsApplet)  # 从管理器中移除小程序
        self.AAXW_CLASS_LOGGER.info(f"{self.__class__.__name__}.disable()")  # 记录禁用日志
        pass

    @override
    def onUninstall(self):
        # 卸载插件时的操作
        self.AAXW_CLASS_LOGGER.info(f"{self.__class__.__name__}.onUninstall()")  # 记录卸载日志
        pass



##
# 1个带top工具与消息面板的，简单例子。
# 无实际其他功能。
##
#
@AAXW_JUMPIN_LOG_MGR.classLogger()
class AAXWJumpinTopWinExpApplet(AAXWAbstractApplet):
    """一个带顶端工具与消息窗口的Applet框架样例（未带任何对话或按钮功能）"""
    AAXW_CLASS_LOGGER: logging.Logger

    def __init__(self):
        self.name = "jumpinChatHistoryApplet"
        self.title = "TWIN"
        self.dependencyContainer: AAXWDependencyContainer = None  # type: ignore
        self.jumpinConfig: 'AAXWJumpinConfig' = None  # type: ignore
        self.mainWindow: 'AAXWJumpinMainWindow' = None  # type: ignore

    @override
    def getName(self) -> str:
        return self.name

    @override
    def getTitle(self) -> str:
        return self.title
    
    def getDesc(self) -> str:
        return self.__class__.__doc__ if self.__class__.__doc__ else "..."
        # if self.__class__.__doc__:
        #     return self.__class__.__doc__ #type:ignore
        # else:
        #     return ""

    def _expButtonClicked(self):
        """例子按钮按下"""
        self.AAXW_CLASS_LOGGER.info("打开历史记录列表")

    @override
    def onAdd(self):

        self.toolsFrame=self._createToolsMessagePanel()
        self.AAXW_CLASS_LOGGER.info(f"{self.name} Applet被添加")
        pass
    

    # 创建1个工具菜单组件-对应本applet；（界面）
    def _createToolsMessagePanel(self):
        """创建工具面板"""
        # 创建主Frame
        toolsframe = QFrame()
        toolsframe.setObjectName("top_toolsframe")
        toolsframe.setStyleSheet("""
            QFrame#chat_history_toolsframe {
                background-color: #f0f0f0;
                border: 1px solid #ccc;
                border-radius: 5px;
            }
        """)
        layout = QVBoxLayout(toolsframe)


        # 添加文本说明，设置ObjectName
        self.descLabel = QLabel(self.getDesc())
        self.descLabel.setObjectName("desc_label")
        layout.addWidget(self.descLabel)
        
        # 添加分割线
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(line)


        # 创建工具栏
        toolbar = QToolBar()
        
        # 创建保存聊天历史按钮
        left_win_button = QPushButton("<<<")
        left_win_button.clicked.connect(self._expButtonClicked)
        toolbar.addWidget(left_win_button)

        layout.addWidget(toolbar)
        return toolsframe

    @override
    def onActivate(self):
        # 主要展示界面 界面可能变化，所以接货的时候获取界面内容；
        self.showingPanel=self.mainWindow.msgShowingPanel #用于展示的
        

        # 展示策略关联给 self.showingPanel
        self.backupContentBlockStrategy=self.showingPanel.contentBlockStrategy
        self.showingPanel.contentBlockStrategy=AAXWJumpinCompoMarkdownContentStrategy()

        #  将输入触发逻辑关联给inputkit
        #
        # self.mainWindow.inputPanel.funcButtonRight.clicked.connect(self.doInputCommitAction)


        #按钮标志与基本按钮曹关联
        self.mainWindow.inputPanel.funcButtonLeft.setText(self.getTitle())

        #加上工具组件
        self.mainWindow.topToolsMessageWindow.setCentralWidget(self.toolsFrame)  #type:ignore
        self.AAXW_CLASS_LOGGER.info(f"{self.name} Applet被激活")
        pass

    @override
    def onInactivate(self):
        #
        self.showingPanel.contentBlockStrategy=self.backupContentBlockStrategy #type:ignore 
        self.backupContentBlockStrategy=None #type:ignore

        #去除 槽函数
        # self.mainWindow.inputPanel.funcButtonRight.clicked.disconnect(self.doInputCommitAction)
        # self.mainWindow.inputPanel.promptInputEdit.returnPressed.disconnect(self.doInputCommitAction)
        # self.aiThread=None

        #清理工具组件引用；
        self.mainWindow.topToolsMessageWindow.removeCentralWidget() 
        #

        self.AAXW_CLASS_LOGGER.info(f"{self.name} Applet被停用")
        pass

    @override
    def onRemove(self):
        if self.toolsFrame:
            self.toolsFrame.deleteLater()
            self.toolsFrame = None
        self.AAXW_CLASS_LOGGER.info(f"{self.name} Applet被移除")
        pass


@AAXW_JUMPIN_LOG_MGR.classLogger()
class AAXWJumpinTopWinExpPlugin(AAXWAbstractBasePlugin):
    AAXW_CLASS_LOGGER: logging.Logger

    def __init__(self) -> None:
        # 初始化插件，并将插件管理器中需要的资源置为None
        super().__init__()
        self.dependencyContainer: AAXWDependencyContainer = None  # 插件依赖管理器 #type:ignore
        self.jumpinConfig: 'AAXWJumpinConfig' = None  # 插件配置对象 #type:ignore
        self.mainWindow: 'AAXWJumpinMainWindow' = None  # 主窗口对象 #type:ignore
        self.jumpinAppletManager: AAXWJumpinAppletManager = None  # 小程序管理器 #type:ignore

    @override
    def onInstall(self):
        # 安装插件时的操作
        self.chatHistoryApplet = AAXWJumpinTopWinExpApplet()  # 创建一个小程序示例
        self.AAXW_CLASS_LOGGER.info(f"{self.__class__.__name__}.onInstall()")  # 记录安装日志
        pass

    @override
    def enable(self):
        # 启用插件时的操作
        self.jumpinAppletManager.addApplet(self.chatHistoryApplet)  # 将小程序添加到管理器中
        self.AAXW_CLASS_LOGGER.info(f"{self.__class__.__name__}.enable()")  # 记录启用日志
        pass

    @override
    def disable(self):
        # 禁用插件时的操作
        self.jumpinAppletManager.removeAppletByInstance(self.chatHistoryApplet)  # 从管理器中移除小程序
        self.AAXW_CLASS_LOGGER.info(f"{self.__class__.__name__}.disable()")  # 记录禁用日志
        pass

    @override
    def onUninstall(self):
        # 卸载插件时的操作
        self.AAXW_CLASS_LOGGER.info(f"{self.__class__.__name__}.onUninstall()")  # 记录卸载日志
        pass


