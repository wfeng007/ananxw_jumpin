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
# 额外的内置插件。可发验证或测试使用。
#
import sys,os,time
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
    QLabel, QToolBar,QSizePolicy, QHBoxLayout, QLineEdit,QApplication
)

import urllib.parse
import urllib.request
import json


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
    AAXWJumpinConfig,AAXWOllamaAIConnOrAgent,
    AAXWJumpinCompoMarkdownContentStrategy,
    AAXWScrollPanel,AIThread,
)

AAXW_JUMPIN_MODULE_LOGGER:logging.Logger=AAXW_JUMPIN_LOG_MGR.getModuleLogger(
    sys.modules[__name__])

AAXW_JUMPIN_MODULE_LOGGER.info(f"module {__name__} is running...")


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
    
    def __init__(self, button_text: str = "", placeholder_text: str = "", parent: QWidget = None):
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


