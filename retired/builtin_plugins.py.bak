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
import traceback

def __setup_env__():
    __package_name__="ananxw_jumpin"
    _file_basename = os.path.splitext(os.path.basename(__file__))[0]
    if __name__ != f"{__package_name__}.{_file_basename}":
        sys.modules[f"{__package_name__}.{_file_basename}"] = sys.modules[__name__]
        print(f"\n新模块名: {__package_name__}.{_file_basename} 已设置到 sys.modules")
    else:
        print(f"\n未增加模块名，已有模块:{__name__} 已设置到 sys.modules")
__setup_env__()


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
#
# 打包chromadb后运行时导入模块会存在多个 命名未定义导入本模块失败。chroma v0.5.23
# 临时进行部分修改，import对应命名
# 1 import chromadb.utils.embedding_functions.__init__.py 中引用了未定义的 ONNXMiniLM_L6_V2 
#   实际在 chromadb.utils.embedding_functions.onnx_mini_lm_l6_v2.ONNXMiniLM_L6_V2 
#   
# 2 chromadb 内部还有动态导入：chromadb\api\shared_system_client.py -> chromadb\config.py.get_class()
#   先导入一下：（或者打包时放入隐含导入，方便静态分析）
# 打包时，chromdb可能还是至少在静态分析阶段要隐含导入给与分析。
# if getattr(sys, 'frozen', False):
#     try:
#         import chromadb.telemetry.product.posthog
#         import chromadb.api.segment
#         import chromadb.db.impl
#         import chromadb.db.impl.sqlite
#         import chromadb.segment.impl.manager.local
#         import chromadb.execution.executor.local
#         import chromadb.quota.simple_quota_enforcer
#         import chromadb.rate_limit.simple_rate_limit
#         import chromadb.segment.impl.metadata
#         import tiktoken.registry
#         # langchain,  embedding模型需要 尤其用ada2,进行文档灌库时
#         import tiktoken_ext.openai_public  # embedding模型需要 尤其用ada2
#         import tiktoken_ext # embedding模型需要 尤其用ada2
#     except Exception as e:
#         print(f"用于打包分析，导入chromadb依赖包，失败:{e}\n{traceback.format_exc()}")
    
# import chromadb.migrations # 这里面是内置的sql文件
# import chromadb.migrations.embeddings_queue
# import chromadb.migrations.sysdb
# import chromadb.migrations.metadb
# 
# 为了适配打包，考虑尝试进行动态导入；chroma相对是独立的db应用，内部有很多动态导入模块动作，不太适合打包。
#       并尝试将Chroma的库以py脚本形式整个放入libs或libs_ext，看打包后能否解析读取执行。
from langchain_chroma import Chroma
from langchain_community.document_loaders import PyMuPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders.word_document import UnstructuredWordDocumentLoader
# from langchain import Document
from langchain_core.documents import Document


# if __name__ == "__main__":
#     # 获取当前文件的父目录的父目录（即 projectlab/）
#     project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
#     if project_root not in sys.path:
#         sys.path.insert(0, project_root)  # 插入到路径最前面

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
# 代知识库实现案例；
# RAG基础实现之一；
##

# 简单知识库实现， chroma，openai-embedding，pypdf
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
                chunk_size=1000,
                chunk_overlap=500,
                length_function=len,
                add_start_index=True,
            )
            documents: List[Document] = text_splitter.split_documents(raw_docs)
            
            # 为每个文档片段添加元数据
            for doc in documents:
                self.AAXW_CLASS_LOGGER.info(
                    f"为每个文档片段添加元数据:{file_name} to {self.vectorstore._collection_name} ")
                doc.metadata.update({
                    "source_file": file_name,
                    "file_path": target_path,
                    "file_type": file_ext,
                    "collection": self.vectorstore._collection_name, #TODO 需要更合理的获取
                    "chunk_size": 1000,
                    "chunk_overlap": 500
                })
            
            if not documents:
                self.AAXW_CLASS_LOGGER.error("文档切分失败")
                return False
            
            self.AAXW_CLASS_LOGGER.info(f"准备添加文档到集合 {collectionName or 'default'}: {file_name}")
            # 添加到向量存储
            vectorstore.add_documents(documents)
            
            self.AAXW_CLASS_LOGGER.info(f"成功添加文档到集合 {collectionName or 'default'}: {file_name}")
            return True
            
        except Exception as e:
            self.AAXW_CLASS_LOGGER.error(f"添加文档到集合 {collectionName or 'default'} 失败: {str(e)}")
            self.AAXW_CLASS_LOGGER.error(f" {str(e)}\n {traceback.format_exc()}")
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
        uploadButton.clicked.connect(self._aHandleUploadFile)
        toolbar.addWidget(uploadButton)
        self.uploadButton=uploadButton
        
       
        layout.addWidget(toolbar)
        return toolsframe

    @AAXW_JUMPIN_LOG_MGR.classLogger()
    class KBSUploadThread(QThread):
        """知识库文件上传处理线程"""
        AAXW_CLASS_LOGGER: logging.Logger
        
        # 定义信号：用于更新UI状态
        updateStatus = Signal(str)  # 状态消息更新信号
        updateButton = Signal(bool)  # 按钮状态更新信号
        
        def __init__(self, file_path: str, kbs: FileChromaKBS):
            super().__init__()
            self.file_path = file_path
            self.kbs = kbs
        
        def run(self):
            try:
                # 开始处理前发送状态更新和按钮禁用信号
                self.updateStatus.emit("正在处理文件...")
                self.updateButton.emit(False)
                
                # 执行文件上传
                success = self.kbs.addDocument(self.file_path)
                
                # 根据上传结果更新状态
                if success:
                    self.AAXW_CLASS_LOGGER.info(f"文件 {self.file_path} 已成功添加到知识库")
                    self.updateStatus.emit("文件添加成功")
                else:
                    self.AAXW_CLASS_LOGGER.error(f"文件 {self.file_path} 添加失败")
                    self.updateStatus.emit("文件添加失败")
                    
            except Exception as e:
                self.AAXW_CLASS_LOGGER.error(f"Upload thread error: {str(e)}")
                self.updateStatus.emit(f"上传失败: {str(e)}")
                
            finally:
                # 确保按钮最终被启用，状态更新为完成
                self.updateButton.emit(True)
                self.updateStatus.emit("处理完成")

    
    def _aHandleUploadFile(self):
        """异步处理文件上传"""
        # 打开文件选择对话框
        file_path, _ = QFileDialog.getOpenFileName(
            self.mainWindow,
            "选择文件",
            "",
            "文档文件 (*.pdf *.doc *.docx)"
        )
        
        if file_path:
            self.AAXW_CLASS_LOGGER.info(f"选择的文件: {file_path}")
            
            try:
                # 创建并启动上传线程
                self.uploadThread = self.KBSUploadThread(file_path, self.kbs)
                # 连接信号到对应的UI更新槽函数
                self.uploadThread.updateStatus.connect(self.statusLabel.setText)
                self.uploadThread.updateButton.connect(self.uploadButton.setEnabled)
                self.uploadThread.start()
                
            except Exception as e:
                self.AAXW_CLASS_LOGGER.error(f"创建上传线程失败: {str(e)}")
    



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


