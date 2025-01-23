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
# 待丢弃代码与案例，可能无法执行。只是备用或参考。
#




##
# 原 builtin_plugins.py内容。
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



