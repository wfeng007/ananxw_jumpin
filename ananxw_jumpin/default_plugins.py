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
#
# @Author:wfeng007 小王同学 wfeng007@163.com
# @Date:2025-03-20 
# @Last Modified by:wfeng007
#
##
#
# AAXWJumpinDefaultCompoApplet 默认的applet实现。
# 左上角title为🐶OP的默认applet。
# 进入界面后默认的的LLM对话与agent功能。
# 
#
# 另外，提供了1个简单插件+空applet的例子实现。
#
"""默认插件和Applet实现"""

import logging
import sys
import re
import time
from datetime import datetime
import traceback
from typing import Optional, List, Dict, Any, Union, cast, Type
from pydantic import BaseModel, Field, create_model
import asyncio

try:
    from typing import override
except ImportError:
    from typing_extensions import override

from PySide6.QtCore import QObject, Signal, Qt, QThread, QEvent, QRunnable
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QFrame, QToolBar
)

# ai相关
# openai客户端
from openai import OpenAI
from openai.types.chat import ChatCompletionSystemMessageParam, ChatCompletionUserMessageParam
# langchain
from langchain_openai import ChatOpenAI
# from langchain.embeddings import OpenAIEmbeddings
# from langchain.embeddings import OllamaEmbeddings
from langchain_community.embeddings import OpenAIEmbeddings
# from langchain_community.embeddings import OllamaEmbeddings

from langchain_community.chat_message_histories.file import FileChatMessageHistory
from langchain.prompts import PromptTemplate
from langchain.schema import (
        BaseMessage,
        AIMessage,  # 等价于OpenAI接口中的assistant role
        HumanMessage,  # 等价于OpenAI接口中的user role
        SystemMessage  # 等价于OpenAI接口中的system role
    )
from langchain.memory import ConversationBufferMemory
from langchain.prompts import PromptTemplate



# pyside6 
from PySide6.QtCore import (
    Qt, QEvent, QObject, QThread, Signal, QTimer, QSize, QPoint,
    QRegularExpression,QMutex,QRunnable,QThreadPool,Slot,
)
from PySide6.QtWidgets import (
    QApplication, QSystemTrayIcon, QFrame, QWidget, QScrollArea,
    QHBoxLayout, QVBoxLayout, QSizePolicy, QLineEdit, QPushButton,
    QTextBrowser, QStyleOption, QMenu, QPlainTextEdit, QLabel,QToolBar,
    QStackedWidget,QButtonGroup,
)
from PySide6.QtGui import (
    QKeySequence, QShortcut, QTextDocument, QTextCursor, QMouseEvent,
    QPainter, QIcon, QImage, QPixmap, QTextOption, QSyntaxHighlighter,
    QTextCharFormat, QColor
)

# pyside6 - qfluentwidgetss
from qfluentwidgets import FluentIcon as FIF
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


# inner modules
from .comm import AAXW_JUMPIN_LOG_MGR

from .backbone import (
    AAXWAbstractBasePlugin, 
    AAXWAbstractApplet,
    AAXWDependencyContainer,
    AAXWJumpinConfig,
    AAXWJumpinAppletManager,
    AAXWJumpinHistoriedMemory,
    AAXWJumpinFileAIMemoryManager,
    AAXWAbstractAIConnOrAgent,

)

from .gui_pyside6 import (
    AAXWContentBlockStrategy, CardWidget, MessageBoxBase,
    AAXWJumpinMainWindow,AAXWJumpinCompoMarkdownContentStrategy,NavigationWidget,ScrollArea,
    AAXWScrollPanel,AAXW_JUMPIN_QTSRR,QTimeoutMutexLocker,
)
from .ananxw_aiagent import BaseAgentAction,BaseAgent,AgentEnvironment,SafetyFallbackAgent

from mcp.types import Tool as McpTool
from .ananxw_mcp import McpClient


# 本模块，模块日志器
AAXW_JUMPIN_MODULE_LOGGER:logging.Logger=AAXW_JUMPIN_LOG_MGR.getModuleLogger(
    sys.modules[__name__])

# applet与 plugin的功能逻辑
#
@AAXW_JUMPIN_LOG_MGR.classLogger()
class AAXWJumpinDefaultSimpleApplet(AAXWAbstractApplet):
    AAXW_CLASS_LOGGER:logging.Logger
    
    def __init__(self):
        self.name = "jumpinDefaultSimpleApplet"
        self.title = "SIMP"
        self.dependencyContainer:AAXWDependencyContainer=None #type:ignore
        self.jumpinConfig:'AAXWJumpinConfig'= None #type:ignore
        self.mainWindow:'AAXWJumpinMainWindow'=None #type:ignore
        
    @override
    def getName(self) -> str:
        return self.name
        
    @override 
    def getTitle(self) -> str:
        return self.title

    # 创建1个工具菜单组件-对应本applet；（界面向）
    def _createToolsMessagePanel(self):
        # 创建主Frame
        toolsframe = QFrame()
        layout = QVBoxLayout(toolsframe)
        
        # 添加文本说明
        label = QLabel("工具面板")
        layout.addWidget(label)
        
        # 添加分割线
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(line)
        
        # 创建工具栏
        toolbar = QToolBar()
        button1 = QPushButton("按钮1")
        button2 = QPushButton("按钮2") 
        button3 = QPushButton("按钮3")
        
        toolbar.addWidget(button1)
        toolbar.addWidget(button2)
        toolbar.addWidget(button3)
        
        layout.addWidget(toolbar)
        
        return toolsframe

    @override
    def onAdd(self):
       
        self.toolsFrame=self._createToolsMessagePanel()
        self.AAXW_CLASS_LOGGER.info(f"{self.name} Applet被添加")
        pass

    @override
    def onActivate(self):
        #按钮标志与基本按钮曹关联
        self.mainWindow.inputPanel.funcButtonLeft.setText(self.getTitle())

        #加上工具组件
        self.mainWindow.topToolsMessageWindow.setCentralWidget(self.toolsFrame)
        self.AAXW_CLASS_LOGGER.info(f"{self.name} Applet被激活")
        pass

    @override
    def onInactivate(self):
        #清理工具组件引用；
        self.mainWindow.topToolsMessageWindow.removeCentralWidget()
        #
        self.AAXW_CLASS_LOGGER.info(f"{self.name} Applet被停用")
        pass

    @override
    def onRemove(self):

        self.AAXW_CLASS_LOGGER.info(f"{self.name} Applet被移除")
        pass



#
#插件例子，理论上会扫描
@AAXW_JUMPIN_LOG_MGR.classLogger()
class AAXWJumpinDefaultBuiltinPlugin(AAXWAbstractBasePlugin):
    AAXW_CLASS_LOGGER:logging.Logger


    #
    # 过滤tab，为input左侧按钮按下。
    # 改为触发applet-manager切换为下一个applet
    # 
    @AAXW_JUMPIN_LOG_MGR.classLogger()
    class EditEventFilter(QObject):
        AAXW_CLASS_LOGGER:logging.Logger
        """
        拦截 Tab 键，并替换为特定的功能；主要作用于InputEdit；
        Tab:
        """

        def __init__(self, mainWindow):
            super().__init__()
            self.mainWindow: AAXWJumpinMainWindow = mainWindow

        def eventFilter(self, obj, event):
            # Tab按键改为控制左侧按钮按下执行 （该也可以考虑改为组合键control+Tab，似）
            if event.type() == QEvent.Type.KeyPress and event.key() == Qt.Key.Key_Tab:
                # print("Tab 键被按下")
                self.mainWindow.inputPanel.funcButtonLeft.click()  # TODO 先注册左侧按钮功能。
                self.AAXW_CLASS_LOGGER.debug("按下了Tab ！")
                return True  # 被过滤
            #
            return False
        
    def __init__(self) -> None:
        super().__init__()
        #jumpin-mgr 会注入
        self.dependencyContainer:AAXWDependencyContainer = None #type:ignore
        self.jumpinConfig:'AAXWJumpinConfig' = None #type:ignore
        self.mainWindow:'AAXWJumpinMainWindow' = None #type:ignore
        self.jumpinAppletManager:AAXWJumpinAppletManager = None #type:ignore

        self.editEventHandler:AAXWJumpinDefaultBuiltinPlugin.EditEventFilter=None #type:ignore 

    @override
    def onInstall(self):
        self.AAXW_CLASS_LOGGER.info(f"{self.__class__.__name__}.onInstall()")
        self.simpleApplet=AAXWJumpinDefaultSimpleApplet()
        
        # inputedit额外的事件处理器，如优先处理如Tab按下
        self.editEventHandler=self.EditEventFilter(self.mainWindow)
        pass

    @override
    def enable(self):
        self.AAXW_CLASS_LOGGER.info(f"{self.__class__.__name__}.enable()")

        # AppletManager 本身会注入资源
        self.jumpinAppletManager.addApplet(self.simpleApplet) 

        
        self.mainWindow.inputPanel.funcButtonLeft.clicked.connect(
            self.jumpinAppletManager.activateNextLoop )
        
        #安装过滤器
        self.mainWindow.inputPanel.promptInputEdit.installEventFilter(
            self.editEventHandler) 
        pass

    @override
    def disable(self):
        self.AAXW_CLASS_LOGGER.info(f"{self.__class__.__name__}.disable()")

        #去除过滤器
        self.mainWindow.inputPanel.promptInputEdit.removeEventFilter(
            self.editEventHandler) 
        
        #去除操作链接
        self.mainWindow.inputPanel.funcButtonLeft.clicked.disconnect(
            self.jumpinAppletManager.activateNextLoop )

        #去除applet 维护；
        self.jumpinAppletManager.removeAppletByInstance(self.simpleApplet) 
        pass

    @override
    def onUninstall(self):
        self.AAXW_CLASS_LOGGER.info(f"{self.__class__.__name__}.onUninstall()")
        self.editEventHandler=None #type:ignore
        pass
    pass


#临时实现
class AIConnectRunnable(QRunnable,QObject):
    """
    异步AI处理线程
    """
    #newContent,id 对应：ShowingPanel.appendToContentById 回调
    updateUI = Signal(str,str)  

    def __init__(self,text:str,uiCellId:str,llmagent:AAXWAbstractAIConnOrAgent):
        super().__init__()
        
        # self.mutex = QMutex()
        self.text:str=text
        self.uiId:str=uiCellId
        self.llmagent:AAXWAbstractAIConnOrAgent=llmagent
        
    def run(self):
        QThread.msleep(500)  # 执行前先等界面渲染
        # self.mutex.lock()
        # print(f"thread inner str:{self.text} \n")
        self.llmagent.requestAndCallback(self.text, self.callUpdateUI)
        # self.mutex.unlock()
        
    def callUpdateUI(self,newContent:str):
        # 最好强制类型转换。self.uiId:str 或 str(self.uiId)
        self.updateUI.emit(str(newContent), str(self.uiId)) 

# pydantic 类型 注入属性日志器可能有问题。
class McpToolAgentAction(BaseAgentAction):
    """MCP工具的Agent Action适配器"""

    #
    mcpClient: McpClient = Field(description="MCP客户端实例")
    serverName: str = Field(description="服务器名称")
    
    def __init__(self, mcpClient: McpClient, serverName: str, tool:McpTool):
        """
        初始化MCP工具适配器
        Args:
            mcpClient: MCP客户端实例
            serverName: 服务器名称
            tool: MCP工具对象
        """
        try:
            # 创建动态的 pydantic model 作为参数模式
            # 动态创建参数模式类    
            args_schema=self._jsonSchemaToPydanticModel(tool.inputSchema)
        
            AAXW_JUMPIN_MODULE_LOGGER.info(
                f"已初始化MCP工具适配器: {tool.name} \n{mcpClient} \n{serverName} \n{tool}")
        except Exception as e:
            AAXW_JUMPIN_MODULE_LOGGER.warning(
                f"初始化MCP工具适配器异常，无法解析生成，args_schema。"
                +f"args_schema将会设置为None，只能利用description作为工具描述。\n "
                +f"异常信息: {str(e)} \n堆栈信息: {traceback.format_exc()}")

            args_schema=None

        ## 初始化； 
        super().__init__(
            name=tool.name,
            description=tool.description,
            args_schema=args_schema,
            mcpClient=mcpClient,
            serverName=serverName
        )

    ## 
    # 当前应该还不支持嵌套
    # cursor：
    # 从 Pydantic 官方文档来看，他们推荐使用 datamodel-code-generator 
    #   工具来实现 JSON Schema 到 Pydantic 模型的转换。这是一个独立的工具，
    #   而不是 Pydantic 的内置功能。
    # 但是，如果我们需要在运行时动态处理 JSON Schema，可以使用 Pydantic 的 TypeAdapter 类。
    #   TypeAdapter 可以用来验证和序列化任意类型的数据，包括从 JSON Schema 生成的类型。
    # 在 schema-first 项目中，我看到了一个有趣的实现方式，它使用 datamodel-codegen 
    #   在构建时生成 Pydantic 模型，而不是运行时。
    ##
    def _jsonSchemaToPydanticModel(self,jsonSchema:dict)->Type[BaseModel]:
        """将JSON Schema转换为Pydantic模型
        
        Args:
            jsonSchema: JSON Schema 字典
            
        Returns:
            生成的 Pydantic 模型类
        """
        # 类型映射
        type_mapping = {
            "string": str,
            "integer": int,
            "number": float,
            "boolean": bool,
            "array": list,
            "object": dict,
            "null": type(None)
        }
        
        # 获取属性定义
        properties = jsonSchema.get("properties", {})
        required = jsonSchema.get("required", [])
        
        # 创建字段定义
        fields = {}
        for field_name, field_schema in properties.items():
            # 获取字段类型
            field_type = field_schema.get("type", "string")  # 默认为string
            python_type = type_mapping.get(field_type, str)
            
            # 获取字段约束
            field_info = {}
            if "description" in field_schema:
                field_info["description"] = field_schema["description"]
            if "default" in field_schema:
                field_info["default"] = field_schema["default"]
            if "title" in field_schema:
                field_info["title"] = field_schema["title"]
                
            # 添加验证约束
            if "minimum" in field_schema:
                field_info["ge"] = field_schema["minimum"]
            if "maximum" in field_schema:
                field_info["le"] = field_schema["maximum"]
            if "minLength" in field_schema:
                field_info["min_length"] = field_schema["minLength"]
            if "maxLength" in field_schema:
                field_info["max_length"] = field_schema["maxLength"]
            if "pattern" in field_schema:
                field_info["pattern"] = field_schema["pattern"]
            
            # 处理必填字段
            if field_name in required:
                field_info["required"] = True
            
            # 创建字段定义
            fields[field_name] = (python_type, Field(**field_info))
        
        # 创建模型类名
        model_name = jsonSchema.get("title", "DynamicModel")
        
        # 创建并返回模型类
        return create_model(
            model_name,
            __doc__=jsonSchema.get("description", ""),
            **fields
        )

    def _run(self, **kwargs) -> str:
        """执行MCP工具调用
        直接调用MCP客户端的调用方法，并同步等待结果
        """
        AAXW_JUMPIN_MODULE_LOGGER.warning(f"执行MCP工具调用: server:{self.serverName} tool:{self.name} \n{kwargs}")
        
        try:
            # 使用同步方法调用工具
            result = self.mcpClient.callTool(
                serverName=self.serverName,
                toolName=self.name,
                args=kwargs,
                timeout=10.0  # 10秒超时
            )
            return str(result)
            
        except TimeoutError:
            AAXW_JUMPIN_MODULE_LOGGER.error(f"调用工具 server:{self.serverName} tool:{self.name} 超时")
            return f"调用工具 server:{self.serverName} tool:{self.name} 超时"
        except Exception as e:
            AAXW_JUMPIN_MODULE_LOGGER.error(f"调用工具 server:{self.serverName} tool:{self.name} 失败: {str(e)} \n堆栈信息: {traceback.format_exc()}")
            return f"调用工具 server:{self.serverName} tool:{self.name} 失败: {str(e)}"

    pass 



@AAXW_JUMPIN_LOG_MGR.classLogger()
class AAXWJumpinDefaultCompoApplet(AAXWAbstractApplet):
    "默认带有复合功能的Applet实现"
    AAXW_CLASS_LOGGER:logging.Logger

    def __init__(self):
        self.appletManager:AAXWJumpinAppletManager=None #type:ignore
        self.dependencyContainer:AAXWDependencyContainer=None #type:ignore
        self.jumpinConfig:'AAXWJumpinConfig'= None #type:ignore
        self.mainWindow:'AAXWJumpinMainWindow'=None #type:ignore

        self.name="jumpinDefaultCompoApplet"
        self.title="🐶OP"

        self.backupContentBlockStrategy:AAXWContentBlockStrategy=None #type:ignore

        self.agentEnvironment:AgentEnvironment=None #type:ignore
        self.aaAgent:BaseAgent=None #type:ignore
        self.mcpClient:McpClient = None 
        pass
    
    @override
    def getName(self) -> str:return  self.name
    @override
    def getTitle(self) -> str:return  self.title

    
    @override
    def onAdd(self):
        #
        #加入管理时获取细节资源,内置简单ai访问器（Openai）
        # ai  （后台类资源默认应该都有）

        # self.simpleAIConnOrAgent:AAXWSimpleAIConnOrAgent=self.dependencyContainer.getAANode(
        #     "simpleAIConnOrAgent")
        self.simpleAIConnOrAgent:AAXWAbstractAIConnOrAgent=self.dependencyContainer.getAANode(
            "configurableAIConnOrAgent")
        
        # 

        self.jumpinAIMemoryManager:AAXWJumpinFileAIMemoryManager=self.dependencyContainer.getAANode(
            "jumpinAIMemoryManager")

        self.currentHistoriedMemory:AAXWJumpinHistoriedMemory=None #type:ignore

        #
        # 默认agent @TODO 将AgentEnvironment 绑定到di容器里面去。并升级为agent容器。
        #   并能关联各种agent的使用的资源，比如MCP的工具，记忆库等。

        # pyside6 的线程调用异步mcp client 会卡死？
        # self.agentEnvironment=AgentEnvironment(runtimeType="pyside6")
        #
        self.agentEnvironment=AgentEnvironment(runtimeType="thread_pool")
        
        try:
            # agent 使用的mcp client (model control protocol)
            # path 从统一配置中获取。
            self.mcpClient=McpClient(configPath="./mcp.json")
            
            # 初始化MCP客户端
            if not self.mcpClient.initialize(timeout=10.0):
                self.AAXW_CLASS_LOGGER.warning("MCP客户端初始化失败,initialize()返回False。")
                self.mcpClient=None
        except Exception as e:
            self.AAXW_CLASS_LOGGER.warning(
                f"获取MCP初始化失败: {str(e)}\n 堆栈信息: {traceback.format_exc()}")

       
        # 已临时处理 aaAgent初始化失败的方式。
        ##  @TODO 最好再增加1个可切换agent的界面功能，从失败转移的SafetyFallbackAgent到正常agent；
        try:
            self.aaAgent=self.agentEnvironment.createAgent(
                name="ANAN",
                lifeGoalOrRole="你是一个应用资源管理者。根据用户的信息、事件输入、前次思考执行情况，选择合适的动作来管理应用资源并回复。")
        except Exception as e:
            self.AAXW_CLASS_LOGGER.error(f"Agent初始化失败: {str(e)}\n{traceback.format_exc()}")
            self.aaAgent = SafetyFallbackAgent("ANAN_EMPTY")
            self.AAXW_CLASS_LOGGER.warning("已使用空Agent实现作为备用")
        
        if self.aaAgent is None:
            self.aaAgent = SafetyFallbackAgent("ANAN_EMPTY")
            self.AAXW_CLASS_LOGGER.warning("aaAgent is None,已使用空Agent实现作为备用")
        
        # 创建并配置Agent Action
        renameAgentAction = self.ChatHisRenameAgentAction(compoApplet=self)
        # 连接重命名信号到槽函数
        renameAgentAction.signalEmitter.renameSignal.connect(
            slot=self._renameMemoryAction,
            type=Qt.ConnectionType.QueuedConnection  # 使用队列连接确保线程安全
        )
        # 增加action
        self.aaAgent.addActions([
            self.ChatHisReadAgentAction(aiMemoryManager=self.jumpinAIMemoryManager),
            renameAgentAction
        ])

        # 启动服务器mcp tools:
        if self.mcpClient and "echoserver" in self.mcpClient.getConfiguredServers():
            try:
                # 启动MCP server
                if not self.mcpClient.startServer(serverName="echoserver", timeout=5.0):
                    self.AAXW_CLASS_LOGGER.warning("未正常启动与连接MCP server")
                    raise RuntimeWarning("未正常启动与连接MCP server")
                    
                self.AAXW_CLASS_LOGGER.warning("已启动mcp server:echoserver成功")

                # 获取工具列表
                tools = self.mcpClient.listTools(serverName="echoserver", timeout=5.0)
                self.AAXW_CLASS_LOGGER.warning(f"已获取tools: {tools}")
                
                for tool in tools:
                    # 使用适配器类创建action
                    baseAction = McpToolAgentAction(
                        mcpClient=self.mcpClient,
                        serverName="echoserver",
                        tool=tool
                    )
                    self.aaAgent.addAction(baseAction)
                    
            except TimeoutError:
                self.AAXW_CLASS_LOGGER.warning("启动MCPserver或获取MCP工具列表超时")
            except Exception as e:
                self.AAXW_CLASS_LOGGER.warning(f"启动MCPserver或获取MCP工具列表失败: {str(e)}\n堆栈信息: {traceback.format_exc()}")
        else:
            self.AAXW_CLASS_LOGGER.warning(
                "MCP客户端未正常初始化或没有找到指定server配置，如：echoserver。" )
        #列表展示面板
        self.memoriesListPanel: AAXWJumpinDefaultCompoApplet.MemoriesListPanel =None #type:ignore
        
        #持续展示近期列表；只要applet还在mgr运行，就持续展示；
        #直接在applet初始化时初始化；
        self._initAIMemoryListUI()

        # 初始化"新互动"表菜单项
        self._initNewInteractionUI()

        # 初始化所有记忆/历史列表菜单项
        self._initAllAIMemeoryListUI()

        pass
    


    @override
    def onRemove(self):
        self.AAXW_CLASS_LOGGER.warning(
            f"这是个默认Applet{self.__class__.__name__}只有关闭整体时才应该被移除释放。")
        self.aaAgent.stop()
        self.agentEnvironment.stopAll()
        # 关闭MCP客户端
        if self.mcpClient:
            self.mcpClient.close(timeout=5.0)
        pass


    class ChatHisReadAgentAction(BaseAgentAction):
        """对话历史读取动作"""
        #Action管理器使用
        name: str = "对话历史读取"
        description: str = "读取指定名的'对话历史'的内容"
        # 
        aiMemoryManager: Optional[
            AAXWJumpinFileAIMemoryManager] = Field(default=None, description="AI记忆管理器")

        # 这是用来获取参数的Schema信息，用来生成prompt或来解析。
        class ArgumentSchema(BaseModel):
            """读取对话历史的参数模型"""
            chatHisName: str = Field(..., description="对话历史名称")
            content: str = Field(default="", description="指定范围内容,可选参数")

        args_schema: Type[BaseModel] = ArgumentSchema

        def _run(self, chatHisName: str, content: str = "") -> str:
            if self.aiMemoryManager is None:
                    return f"[错误] 未注入 aiMemoryManager,无法读取对话历史 {chatHisName},无法完成Action"
                
            try:
                memory = self.aiMemoryManager.loadOrCreateMemory(chatHisName)
                msgLs:List[BaseMessage]=memory.message_history.messages
                
                # 获取最后10条消息
                last_messages = msgLs[-10:] if len(msgLs) > 10 else msgLs
                
                # 格式化消息内容
                formatted_messages = []
                for msg in last_messages:
                    role = "Human" if isinstance(msg, HumanMessage) else "Assistant"
                    formatted_messages.append(f"{role}: {msg.content}")
                
                history_content = "\n\n".join(formatted_messages)
                return f"## 对话历史 {chatHisName} 的内容:\n\n{history_content}"
            except Exception as e:
                return f"[错误] 读取对话历史 {chatHisName} 失败: {str(e)}"

    class ChatHisRenameAgentAction(BaseAgentAction):
        """重命名对话历史动作"""
        name: str = "对话历史重命名"
        description: str = "将指定名称的对话历史重命名为新名称"
        
        # 继承QObject以支持信号机制
        class RenameSignalEmitter(QObject):
            renameSignal = Signal(str, str)  # 重命名信号(oldName, newName)
    
        # 将signalEmitter定义为Field
        signalEmitter: RenameSignalEmitter = Field(
            default_factory=RenameSignalEmitter,
            description="信号发射器"
        )
    
        compoApplet: Optional[
            'AAXWJumpinDefaultCompoApplet'] = Field(default=None, description="复合功能Applet")

        class ArgumentSchema(BaseModel):
            """重命名对话历史的参数模型"""
            chatHisName: str = Field(..., description="原对话历史名称")
            newName: str = Field(..., description="新的对话历史名称")

        args_schema: Type[BaseModel] = ArgumentSchema

        def _run(self, chatHisName: str, newName: str) -> str:
            if self.compoApplet is None:
                return f"[错误] 未注入 compoApplet,无法重命名对话历史 {chatHisName}"
            
            try:
                # 通过信号触发重命名操作
                self.signalEmitter.renameSignal.emit(chatHisName, newName)
                return f"[成功] 已发送重命名请求: {chatHisName} -> {newName}"
                
            except Exception as e:
                return f"[错误] 重命名失败: {str(e)}"



    @override
    def onActivate(self): 
        # 主要操作逻辑的"定义与注册"放在本方法中；
        # 激活时，检测默认界面组件；
        # 需要有默认 输入kit与展示panel 
        
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

        pass

    @override
    def onInactivate(self):
        #
        self.showingPanel.contentBlockStrategy=self.backupContentBlockStrategy
        self.backupContentBlockStrategy=None #type:ignore


        #去除 槽函数
        self.mainWindow.inputPanel.funcButtonRight.clicked.disconnect(self.doInputCommitAction)
        # self.mainWindow.inputPanel.promptInputEdit.returnPressed.disconnect(self.doInputCommitAction)
        
        pass
    
    # ui-init
    def _initNewInteractionUI(self):
        # 初始化"新互动"的功能
        niWg:NavigationWidget=self.mainWindow.navigationInterface.widget('new_interaction')
        niWg.clicked.connect(self.doNewInteractionAction)
        pass

    # ui-init    
    #初始化记忆/历史记录列表
    def _initAIMemoryListUI(self):
        """初始化界面上的记忆列表
        由于界面是从头部插入,而查询结果是新的在前,所以需要反转列表顺序再插入
        """
        # 获取记忆列表(默认按修改时间降序,新的在前)
        mems = self.jumpinAIMemoryManager.listMemoryNames(
            offset=0,
            limit=5,  # 默认只展示最近5条
            sortByModified=True,
            ascending=False
        )
        
        # 反转列表,这样插入到界面时顺序就正确了
        # 因为界面是从头部插入,而我们希望最新的在最上面
        for record in reversed(mems):
            # 定义右键菜单项
            menuItems = [
                ("重命名", lambda _,r=record: self.showRenameMemoryDialogUI(name=r)),
                ("删除", lambda _,r=record: self.deleteMemoryAction(name=r))
            ]

            self.mainWindow.navigationInterface.insertItemWithContextMenu(
                0,  # 在首个位置插入
                routeKey=f'{record}',
                icon=FIF.CHAT,
                text=f'{record}',
                # 原insertItem 的onClick默认有1个bool 参数，所有要有 _ 占位符
                # onClick=lambda _,rr=record: self.loadMemoryAction(record=rr),
                onClick=lambda rr=record: self.loadMemoryAction(record=rr),
                menuItems=menuItems,
                selectable=True,
                position=NavigationItemPosition.SCROLL,
                tooltip=f'{record}'
            )

    def _initAllAIMemeoryListUI(self):
        """初始化 列出所有memory/history的菜单项以及列表展示面板"""

        #初始化列表展示面板
        if self.memoriesListPanel is None:
            self.memoriesListPanel = self.MemoriesListPanel(
                applet=self,
                title="记忆与对话历史列表",
                parent=self.mainWindow.mainStackedFrame)
            self.mainWindow.mainStackedFrame.addWidget(self.memoriesListPanel)

        #初始化列出功能菜单项
        allmemoryItem = cast(NavigationTreeWidget, 
            self.mainWindow.navigationInterface.widget('all_history'))
        allmemoryItem.clicked.connect(self.listAllMemoriesAction)

        pass


    #
    # 
    def listAllMemoriesAction(self):
        """展示memories列表面板"""
        
        # 获取记忆列表(默认按修改时间降序,新的在前)
        mems = self.jumpinAIMemoryManager.listMemoryNames(
            offset=0,
            limit=200,  # 默认只展示最近100
            sortByModified=True,
            ascending=False
        )

        # 构建记忆数据格式
        memories = [{
            "name":mems[i],
            "title": f"{mems[i]}", 
            "description": "...概要描述..."} 
            for i in range(len(mems))
        ]

        self.memoriesListPanel.renderMemoryList(memories)
        #前台展示
        self.mainWindow.mainStackedFrame.setCurrentWidget(self.memoriesListPanel)
        # self.memoriesListPanel.show()

    class MemoOrHisCardWidget(CardWidget):
        def __init__(self, name,title, description, index, applet,parent=None):
            super().__init__(parent)
            self.memoOrHisName=name
            self.index = index
            # self.routekey = routeKey
            self.applet:AAXWJumpinDefaultCompoApplet=applet #type:ignore
            
            # 设置卡片属性
            self.setBorderRadius(8)
            self.setObjectName('memoOrHisCardWidget')
            self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)  # 添加此行
            # self.setFixedHeight(120)  # 添加此行，设置固定高度
            
            # 主布局
            self.hBoxLayout = QHBoxLayout(self)
            
            # 左侧图标
            self.iconWidget = IconWidget(FIF.HISTORY, self)
            self.iconWidget.setFixedSize(16, 16)
            
            # 中间内容布局
            self.contentLayout = QVBoxLayout()
            self.contentLayout.setSpacing(1)
            self.contentLayout.setContentsMargins(0, 0, 0, 0)
            self.contentLayout.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
            
            # 标题和描述
            stitle = title[:10] + '...'if len(title) > 12 else title
            # self.titleLabel = SubtitleLabel(stitle, self)
            self.titleLabel = StrongBodyLabel(stitle, self)
            # self.descriptionLabel = BodyLabel(TextWrap.wrap(description, 45, False)[0], self)
            # 使用 PlainTextEdit 来展示描述
            # self.descriptionLabel = TextEdit(self)
            self.descriptionLabel = TextBrowser(self)
            self.descriptionLabel.setPlainText(description)
            self.descriptionLabel.setReadOnly(True)  # 设置为只读
            self.descriptionLabel.setFixedHeight(80)
            # 设置样式为无边框且颜色与外部组件一致
            self.descriptionLabel.setStyleSheet("""
                QTextBrowser {
                    border: none;  /* 无边框 */
                    background-color: transparent;  /* 背景透明 */
                }
            """)
            
            # 右侧按钮布局
            self.buttonLayout = QVBoxLayout()
            self.buttonLayout.setSpacing(4)
            self.buttonLayout.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignBottom)
            
            # 按钮
            self.detailButton = PushButton('详情', self, icon=FIF.INFO)
            self.deleteButton = PushButton('删除', self, icon=FIF.DELETE)
            self.renameButton = PushButton('重命名', self, icon=FIF.EDIT)
            
            for btn in (self.detailButton, self.deleteButton, self.renameButton):
                btn.setFixedWidth(100)
                
            # 组装布局
            # self.contentLayout.addStretch(1)
            self.contentLayout.addWidget(self.titleLabel)
            self.contentLayout.addWidget(self.descriptionLabel)
            # self.contentLayout.addStretch(1)
            
            
            self.buttonLayout.addWidget(self.detailButton)
            self.buttonLayout.addWidget(self.renameButton)
            self.buttonLayout.addWidget(self.deleteButton)
            
            self.hBoxLayout.addWidget(
                self.iconWidget, 0, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
            self.hBoxLayout.addLayout(self.contentLayout, 1)
            self.hBoxLayout.addLayout(self.buttonLayout, 0)
            
            # 设置布局属性
            self.hBoxLayout.setContentsMargins(20, 16, 16, 16)
            self.hBoxLayout.setSpacing(28)
            
            # 设置卡片属性
            self.setBorderRadius(8)
            self.setObjectName('customCard')
            
            # 信号连接
            self.detailButton.clicked.connect(self.on_detail_click)
            self.deleteButton.clicked.connect(self.on_delete_click)
            self.renameButton.clicked.connect(self.on_rename_click)
        
        def mouseReleaseEvent(self, e):
            super().mouseReleaseEvent(e)
            # signalBus.switchToCard.emit(self.routekey, self.index)
        
        def on_detail_click(self): 
            #  self.applet.
            self.applet.loadMemoryAction(record=self.memoOrHisName)
            pass
        def on_delete_click(self): 
            print(f"Delete memo or his name:{self.memoOrHisName}")
            self.applet.deleteMemoryAction(self.memoOrHisName)
        def on_rename_click(self): 
            print(f"Rename memo or his name:{self.memoOrHisName}")
            self.applet.showRenameMemoryDialogUI(self.memoOrHisName)
    
    #
    class MemoriesListPanel(QWidget):
        def __init__(self,applet,title="",parent=None):
            super().__init__(parent)
            self.applet:AAXWJumpinDefaultCompoApplet=applet
            self.titleLabel = QLabel(title, self)
            self.vBoxLayout = QVBoxLayout(self)
            # self.setGeometry(100, 100, 400, 300)
            self.vBoxLayout.addWidget(self.titleLabel)
            self.scrollArea = ScrollArea(self)
            self.scrollArea.setWidgetResizable(True)

            self.container = QWidget()
            self.flowLayout = QVBoxLayout(self.container)
            self.flowLayout.setAlignment(Qt.AlignmentFlag.AlignTop)
            self.scrollArea.setWidget(self.container)
            
            self.vBoxLayout.addWidget(self.scrollArea)
            self.vBoxLayout.setContentsMargins(10, 10, 10, 10)
            self.vBoxLayout.setSpacing(10)

        def renderMemoryList(self, memories):
            """刷新记忆列表:
            memories[{
                title:'xxx'
                description:'xxx'
            },...]
            """
            # 清空当前内容
            self.clearMemoryList()
            # 添加新的记忆项
            for index, memory in enumerate(memories):
                card = AAXWJumpinDefaultCompoApplet.MemoOrHisCardWidget(
                    name=memory['name'],title=memory['title'],
                    description=memory['description'],index=index,applet=self.applet,parent=self)
                self.flowLayout.addWidget(card)

        def clearMemoryList(self):
            """清空记忆列表展示"""
            for i in reversed(range(self.flowLayout.count())):
                widget = self.flowLayout.itemAt(i).widget()
                if widget is not None:
                    widget.deleteLater()


    def _initBuddyAndAppletListUI(self):
        """初始化伙伴与应用列表UI
        Partner指AIAgent或其他可互动主体；
        """
        # 获取aiagent_applet项，并显式转换类型实际就是NavigationTreeWidget
        aiagentItem = cast(NavigationTreeWidget, 
            self.mainWindow.navigationInterface.widget('aiagent_applet'))
        
        if aiagentItem:
            # 遍历并移除所有子项
            for child in aiagentItem.treeChildren[:]:  # 使用切片创建副本进行遍历
                aiagentItem.removeChild(child)
        
        # 获取所有applet的名称和标题列表
        appletNamesAndTitles = self.appletManager.listAppletsNamesAndTitles()
        
        self.AAXW_CLASS_LOGGER.warning(f"伙伴或应用数量-{len(appletNamesAndTitles)}")
        # 添加每个applet作为子项
        for index, (name, title) in enumerate(appletNamesAndTitles):
            self.mainWindow.navigationInterface.addItem(
                routeKey=f'ba_{name}_{index}',  # 使用applet名称作为唯一标识
                icon=FIF.ROBOT,  # 使用机器人图标表示applet
                text=title,  # 显示applet的标题
                onClick=lambda _,i=index: self.appletManager.activateApplet(index=i),  # 使用index激活对应applet
                tooltip=f'切换到 {title}',
                selectable=False,
                parentRouteKey='aiagent_applet'  # 指定父级为aiagent_applet
            )
            self.AAXW_CLASS_LOGGER.warning(f"已添加伙伴或应用-{name}-'{title}")
        


    @Slot()
    def deleteMemoryAction(self, name: str):
        """删除记忆操作
        Args:
            record: 记忆ID
        """
        # TODO: 可以添加确认对话框
        self.AAXW_CLASS_LOGGER.info(f"删除记忆操作:{name}")
        try:
            # 从文件系统删除
            self.jumpinAIMemoryManager.deleteMemory(name)
            # 从导航栏移除
            self.mainWindow.navigationInterface.removeWidget(name)
            # 如果当前加载的就是这条记忆,清空显示
            if (self.currentHistoriedMemory and 
                self.currentHistoriedMemory.chat_id == name):
                self.currentHistoriedMemory = None
                self.clearContentAction()
            # 刷新列表
            self.refreshMemoryListUIAction()
        except Exception as e:
            self.AAXW_CLASS_LOGGER.error(
                f"删除记忆失败: {str(e)}\n{traceback.format_exc()}")

    class RenameMemoryMessageBox(MessageBoxBase):
        """ Custom message box """

        def __init__(self, oldName:str=None, parent=None): #type:ignore
            super().__init__(parent)
            self.titleLabel = SubtitleLabel('修改互动名称：', self)
            self.nameLineEdit = LineEdit(self)
            
            # 添加单选按钮组
            self.radioGroup = QButtonGroup(self) 
            self.userRadio = RadioButton('用户指定', self)
            self.agentRadio = RadioButton('Agent自动', self)
            self.radioGroup.addButton(self.userRadio)
            self.radioGroup.addButton(self.agentRadio)
            self.userRadio.setChecked(True)  # 默认选中用户指定
            
            # 创建水平布局放置单选按钮
            radioLayout = QHBoxLayout()
            radioLayout.addWidget(self.userRadio)
            radioLayout.addWidget(self.agentRadio)
            radioLayout.addStretch()
            
            if oldName:
                self.nameLineEdit.setText(oldName)
            else:
                self.nameLineEdit.setPlaceholderText('请输入新名称')
            self.nameLineEdit.setClearButtonEnabled(True)

            self.warningLabel = CaptionLabel("名称长度4-20个字符，只能包含字母、数字、下划线、中划线、点")
            self.warningLabel.setTextColor(QColor(255, 28, 32))

            # add widget to view layout
            self.viewLayout.addWidget(self.titleLabel)
            self.viewLayout.addLayout(radioLayout)  # 添加单选按钮组布局
            self.viewLayout.addWidget(self.nameLineEdit)
            self.viewLayout.addWidget(self.warningLabel)
            self.warningLabel.hide()

            # change the text of button
            self.yesButton.setText('修改')
            self.cancelButton.setText('取消')

            self.widget.setMinimumWidth(350)
            
            # 连接单选按钮状态改变信号
            self.radioGroup.buttonClicked.connect(self._onRadioChanged)
            
        def _onRadioChanged(self):
            """单选按钮状态改变时的处理"""
            isUserMode = self.userRadio.isChecked()
            self.nameLineEdit.setEnabled(isUserMode)
            self.warningLabel.setVisible(isUserMode and not self.validate())
    
        @override
        def validate(self):
            """ Rewrite the virtual method """
            # 如果是Agent自动模式，直接返回True
            if self.agentRadio.isChecked():
                return True
                
            # 用户指定模式下进行验证
            text = self.nameLineEdit.text()
            # 修改正则表达式以支持中文字符
            isValid = (4 <= len(text) <= 20) and bool(
                re.match(r'^[\u4e00-\u9fa5a-zA-Z0-9_\-\.]+$', text)
            )
            self.warningLabel.setHidden(isValid)
            return isValid

        def getNewName(self) -> str:
            """获取新名称"""
            return self.nameLineEdit.text()
            
        def isAgentMode(self) -> bool:
            """获取是否为Agent自动模式"""
            return self.agentRadio.isChecked()

    @Slot()
    def showRenameMemoryDialogUI(self, name: str):
        dialog = self.RenameMemoryMessageBox(oldName=name, parent=self.mainWindow)
        if dialog.exec():
            if dialog.isAgentMode() :
                # self.aaAgent.sendMessageToMe(
                #     "请帮我将'"+
                #     name+
                #     "'的对话历史改名，先读取对话历史内容并小结出新名字，然后将其改名。"+
                #     "对话历史名字不能超过15个字符。改完请回复我一下。"
                # )
                self.aaAgent.senseEnvironmentEvent(
                    command="请帮忙将'"+
                    name+
                    "'的对话历史改名，先读取对话历史内容并小结出新名字，然后将其改名。"+
                    "对话历史名字不能超过15个字符且保留原后缀。改完或失败就结束无需回复。"
                )
            else:
                newName = dialog.getNewName()
                self.AAXW_CLASS_LOGGER.info(f"准备重命名记忆:{name} 新名称:{newName}")
                self._renameMemoryAction(name, newName)
        else:
            self.AAXW_CLASS_LOGGER.info(f"取消重命名记忆:{name}")

    @Slot()
    def _renameMemoryAction(self, record: str,newName:str):
        """重命名记忆操作
        Args:
            record: 记忆ID
        """
        self.AAXW_CLASS_LOGGER.warning(f"重命名记忆操作:{record}")
        #
        self.jumpinAIMemoryManager.renameMemory(record, newName)

        # 刷新列表
        self.refreshMemoryListUIAction()

        ...

    @Slot()
    def loadMemoryAction(self, record:str):
        self.AAXW_CLASS_LOGGER.info(f'记录:{record} clicked')
        #首先显示默认的消息展示面板
        self.mainWindow.showMsgShowingPanel()

        chat_id = record  # 获取被点击项的文本内容
        self.loadMemory(chat_id)  # 调用加载方法


    @Slot()
    def refreshMemoryListUIAction(self):
        """刷新历史记录列表
        1. 删除已有的历史记录导航项
        2. 重新添加最新的历史记录列表
        """
        # 获取所有导航项(在scrollWidget中的项)
        scrollWidget = self.mainWindow.navigationInterface.panel.scrollWidget
        for widget in scrollWidget.findChildren(NavigationWidget):
            routeKey = widget.property('routeKey')
            # 过滤掉固定项和树形节点的子项
            if (routeKey not in ['all_history', 'aiagent_applet'] and 
                not isinstance(widget.parent(), NavigationTreeWidget)):
                self.mainWindow.navigationInterface.removeWidget(routeKey)
        

        #重新加载初始化Memory列表
        self._initAIMemoryListUI()
        
        # 刷新界面
        self.mainWindow.navigationInterface.panel.update()

        # 增加 刷新指定位置（比如 新加的列表面板）
        if self.mainWindow.mainStackedFrame.currentWidget() is self.memoriesListPanel:
            #刷新列表
            self.listAllMemoriesAction()
    

    
    def loadMemory(self, chat_id: str):
        """加载指定的聊天历史或记忆"""
        self.AAXW_CLASS_LOGGER.info(f"加载聊天历史: {chat_id}")
        
        self.currentHistoriedMemory = self.jumpinAIMemoryManager.loadOrCreateMemory(chat_id)
        
        # 创建新的加载线程
        loadThread = self.LoadMemoryUpdateShowingPanelRunnable(
                    self.currentHistoriedMemory
                    ,self.mainWindow)
        loadThread.clearContentSignal.connect(self.clearContentAction)
        loadThread.addRowContentSignal.connect(self.addRowContentAction)
        loadThread.appendContentSignal.connect(self.appendContentAction)
        
        # 使用mainWindow的线程池来管理线程
        worker = self.mainWindow.qworkerpool.createAndStartWorker(loadThread)
        
        # 添加完成回调以清理线程
        worker.signals.ON_FINISHED.connect(lambda: loadThread.deleteLater())

    @Slot()
    def clearContentAction(self):
        self.mainWindow.msgShowingPanel.clearContent()

    @Slot()
    def addRowContentAction(self, content: str, rowId: str, contentOwner: str,contentOwnerType:str):
        """添加行内容的槽函数"""
        self.mainWindow.msgShowingPanel.addRowContent(
            content=content, rowId=rowId, contentOwner=contentOwner, 
            contentOwnerType=contentOwnerType
        )

    @Slot()
    def appendContentAction(self, content: str, rowId: str):
        """追加内容的槽函数"""
        self.mainWindow.msgShowingPanel.appendContentByRowId(content, rowId=rowId)
        # 同步更新界面会阻塞界面- 参考_mockAIUpdateUI方法。
       
    @Slot()
    def doNewInteractionAction(self):
        # 清除当前展示内容
        self.clearContentAction()
        #创建1个新的chat/memo 并且作为当前chat/memo
        self.currentHistoriedMemory=self.jumpinAIMemoryManager.loadOrCreateMemory()
        # 加载新的记忆
        self.loadMemory(self.currentHistoriedMemory.chat_id)
        # 刷新列表展示
        self.refreshMemoryListUIAction()
        pass

    @Slot()
    def doInputCommitAction(self):
        self.AAXW_CLASS_LOGGER.debug("Right button clicked!")

        #首先显示默认的消息展示面板
        self.mainWindow.showMsgShowingPanel()

        # 获取用户输入
        text = self.mainWindow.inputPanel.promptInputEdit.text()

         # 用户输入容消息气泡与内容初始化
        rid = int(time.time() * 1000)
        self.mainWindow.msgShowingPanel.addRowContent(
            content=text, rowId=str(rid), contentOwner="user_xiaowang",
            contentOwnerType=AAXWScrollPanel.ROW_CONTENT_OWNER_TYPE_USER,
        )
        
        # 等待0.5秒
        # 使用QThread让当前主界面线程等待0.5秒 #TODO 主要为了生成rowid，没必要等待。
        QThread.msleep(500) 
        # 反馈内容消息气泡与内容初始化
        rrid = int(time.time() * 1000)
        self.mainWindow.msgShowingPanel.addRowContent(
            content="", rowId=str(rrid), contentOwner="assistant_aaxw",
            contentOwnerType=AAXWScrollPanel.ROW_CONTENT_OWNER_TYPE_OTHERS,
        )

        #
        #生成异步处理AI操作的线程
        #注入要用来执行的ai引擎以及 问题文本+ ui组件id
        #FIXME 执行时需要基于资源，暂时锁定输入框；
        #           多重提交，多线程处理还没很好的做，会崩溃；

        # 暂时使用当前HistoriedMemory
        if self.currentHistoriedMemory is None:
            self.currentHistoriedMemory=self.jumpinAIMemoryManager.loadOrCreateMemory()
            #刷新列表展示
            self.refreshMemoryListUIAction() #需要信号发送去执行；这里是doInputCommitAction本身是槽函数
            
        # 创建并启动AI处理线程
        aiThread = self.MemorisedAIConnectUpdateShowingPanelRunnable(
            text=text, uiCellId=str(rrid), llmagent=self.simpleAIConnOrAgent, 
            hMemo=self.currentHistoriedMemory,mainWindow=self.mainWindow,
            aaAgent=self.aaAgent)
        aiThread.updateUI.connect(self.mainWindow.msgShowingPanel.appendContentByRowId)
        
        # 使用mainWindow的线程池来管理线程
        self.mainWindow.qworkerpool.createAndStartWorker(aiThread)
       
        self.mainWindow.inputPanel.promptInputEdit.clear()

    #
    def _logInput(self):
        # 打印输入框中的内容
        self.AAXW_CLASS_LOGGER.debug(f"Input: {self.mainWindow.inputPanel.promptInputEdit.text()}")


    
    @AAXW_JUMPIN_LOG_MGR.classLogger()
    class LoadMemoryUpdateShowingPanelRunnable(QRunnable,QObject):
        """用于加载历史消息并更新到界面msgShowingPanel运行时逻辑"""
        AAXW_CLASS_LOGGER: logging.Logger
        addRowContentSignal = Signal(str, str, str,str)  # (内容, rowId, contentOwner,contentOwnerType)
        appendContentSignal = Signal(str, str)        # (内容, rowId)
        clearContentSignal = Signal()

        # MUTEX_LOCKER=QMutex()
        # MUTEX_LOCKER=AAXW_JUMPIN_QTSRR.getMutex(resourceId='')

        def __init__(self,memory: AAXWJumpinHistoriedMemory,mainWindow:'AAXWJumpinMainWindow'):
            QRunnable.__init__(self)
            QObject.__init__(self)
            self.memory = memory
            self.mainWindow=mainWindow
            #避免递归锁定。线程级别使用线程锁。
            self.mutexLocker= AAXW_JUMPIN_QTSRR.getMutex(
                resourceId="Thread_"+str(self.mainWindow.msgShowingPanel.THREAD_SAFE_RESOURCE_ID))
            self.setAutoDelete(True)  # 设置自动删除
    
        @override
        def run(self):
            """线程运行方法"""
            try:
                self.synchRun()
            except Exception as e:
                self.AAXW_CLASS_LOGGER.error(f"线程执行过程中发生错误: {e}")
                self.AAXW_CLASS_LOGGER.error(traceback.format_exc())
            finally:
                self.AAXW_CLASS_LOGGER.info("线程执行完成。")

        def synchRun(self):
            with QTimeoutMutexLocker(mutex=self.mutexLocker,  
                    _verboseName="LoadMemoryUpdateShowingPanelRunnable", timeout_ms=3000) as locked:
                if not locked:
                    self.AAXW_CLASS_LOGGER.warning("获取锁超时，可能已有线程在执行。请不要连续重复操作！")
                    return
                else:
                    messages = self.memory.message_history.messages
                    self.clearContentSignal.emit()
                    for msg in messages:
                        rowId = str(datetime.now().timestamp())
                        if isinstance(msg, HumanMessage):
                            user_content = msg.content
                            self.addRowContentSignal.emit(user_content, rowId, "user",
                                AAXWScrollPanel.ROW_CONTENT_OWNER_TYPE_USER)  # 通过信号更新用户消息
                        elif isinstance(msg, AIMessage):
                            self.addRowContentSignal.emit("", rowId,"ai",
                                AAXWScrollPanel.ROW_CONTENT_OWNER_TYPE_OTHERS)  # 发送占位符
                            QThread.msleep(50)  # 模拟延迟
                            ai_content = msg.content
                            ai_content = str(ai_content)
                            for chunk in ai_content.splitlines(keepends=True):
                                self.appendContentSignal.emit(chunk, rowId)  # 通过信号更新AI消息
                                # self.msleep(100)
                        QThread.msleep(50)  # 模拟延迟

    @AAXW_JUMPIN_LOG_MGR.classLogger()
    class MemorisedAIConnectUpdateShowingPanelRunnable(AIConnectRunnable,QObject):
        AAXW_CLASS_LOGGER: logging.Logger

        PROMPT_TEMPLE=PromptTemplate(
            input_variables=["chat_history", "question"],
            template="根据之前的对话历史:'{chat_history}'; 回答相关问题:{question}"
        )

        #newContent,id 对应：ShowingPanel.appendToContentById 回调
        # updateUI = Signal(str,str)  

        def __init__(self,text:str,uiCellId:str,llmagent:AAXWAbstractAIConnOrAgent,
                hMemo:AAXWJumpinHistoriedMemory,mainWindow:'AAXWJumpinMainWindow',
                aaAgent:Optional[BaseAgent]=None):
            QObject.__init__(self)
            AIConnectRunnable.__init__(self,text=text,uiCellId=uiCellId,llmagent=llmagent)
            self.hMemo = hMemo
            self.mainWindow=mainWindow
            #线程级别锁
            self.mutexLocker= AAXW_JUMPIN_QTSRR.getMutex(
                resourceId="Thread_"+str(self.mainWindow.msgShowingPanel.THREAD_SAFE_RESOURCE_ID))
            self.wholeResponse = ""
            self.setAutoDelete(True)  # 设置自动删除
            self.aaAgent:Optional[BaseAgent]=aaAgent
            
        def run(self):
            # 等待之前user快更新完成
            QThread.msleep(500) 
            #米面递归锁定。资源名称还是要分开。
            with QTimeoutMutexLocker(self.mutexLocker,
                    _verboseName="MemorisedAIConnectUpdateShowingPanelRunnable", timeout_ms=3000) as locked:
                if not locked:
                    self.AAXW_CLASS_LOGGER.warning("获取锁超时，可能已有线程在执行。请不要连续重复操作！")
                    return
                
                self.AAXW_CLASS_LOGGER.info("已加锁")
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

                    #如果是steaming则内部是循环调用onRespone
                    #TODO 如果服务卡顿一直不返回，有时候需要提供强制终端的手段；
                    self.llmagent.requestAndCallback(prompted, self.onResponse)
                except Exception as e:
                    import traceback
                    self.AAXW_CLASS_LOGGER.error(f"An exception occurred: {str(e)}", exc_info=True)
                    self.AAXW_CLASS_LOGGER.error(traceback.format_exc())
                    exec_e=e
                finally:
                    #onfinish
                    if exec_e is None and self.wholeResponse: #没有异常才写入库
                        ai_message = AIMessage(content=self.wholeResponse)
                        self.hMemo.save(ai_message)
                        self.asyncMemoryRenameByAgent(self.hMemo.chat_id)
                    pass
        
        def asyncMemoryRenameByAgent(self,name:str):
            """异步改名"""
            if name is None:
                return
            try:
                if  self.aaAgent is None:
                    self.AAXW_CLASS_LOGGER.warning(f"aaAgent为None,无法用agent改名。")
                    return 
                if not name.startswith('interact'):
                    self.AAXW_CLASS_LOGGER.debug(f"对话历史（记忆）'{name}'无需改名")
                    return 
                
                self.AAXW_CLASS_LOGGER.info(f"异步发起对话历史（记忆）' {name}'重命名,向Agent提供环境事件。")
                self.aaAgent.senseEnvironmentEvent(
                    command="请帮忙将'"+
                    name+
                    "'的对话历史改名，先读取对话历史内容并小结出新名字，然后将其改名。"+
                    "对话历史名字不能超过15个字符且保留原后缀。改完或失败就结束无需回复。"
                )
            except Exception as e:
                self.AAXW_CLASS_LOGGER.error(f"异步发起重命名对话历史'{name}'时发生错误: {str(e)}", exc_info=True)
                self.AAXW_CLASS_LOGGER.error(traceback.format_exc())
        
        def onResponse(self,str):
            self.wholeResponse += str
            self.callUpdateUI(str)
    
    pass 



