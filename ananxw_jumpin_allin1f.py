#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# @Author:wfeng007 小王同学 wfeng007@163.com
# @Date:2024-09-24 18:05:01
# @Last Modified by:wfeng007

#
# 小王的AI 网络/节点（随便什么吧），AI与套件快速快速入口，投入ai吧！ANAN其实也是只狗狗。。。
# An AI Net/Node of XiaoWang ， jumpin AI ! ANAN is a dog...
# 

# 一个提示符操作界面
# 可以快捷键唤起展示的；
# 支持钉在桌面最前端，全局热键换出与隐藏；
# 0.2:托盘功能；
# 0.3:较好的Markdown展示气泡，基本可扩展的展示气泡逻辑；
# 0.4+:
#      已增加工作目录配置与维护，基本文件系统能力。
#      已增加日志功能，默认标准输出中输出；支持工作目录生成日志；并根据时间与数量清理；
# TODO 可切换agent或其他kit-intergration功能，同时提供对应工具面板展示；
#           不同的agent或kit可以定制自己的工具面板。
# 
# 0.5+: 
#      已增加简易注入框架；更好组织代码逻辑；
# TODO 简易插件框架；支持二次开发；
#      可集成密塔等搜索（可插件方式）
# 
# 提供基本的提示发送与结果展示界面；
# 可支持多轮交互；
# 可支持富文本范围内容展示；
# 提供可切换的AI LLM/Agent的对接；
# 
#

import pstats
import sys, os,time
from datetime import datetime
from typing import Callable, List, Dict, Type,Any,TypeVar
try:
    from typing import override #3.12+ #type:ignore
except ImportError:
    from typing_extensions import override #3.8+

from abc import ABC, abstractmethod
# import functools
import threading
import argparse

import logging
from logging.handlers import TimedRotatingFileHandler

# 加载环境变量 #openai 的key读取
from dotenv import load_dotenv, find_dotenv

# yaml 配置
import yaml

# pyside6 
from PySide6.QtCore import (
    Qt, QEvent, QObject, QThread, Signal, QTimer, QSize, 
    QRegularExpression
)
from PySide6.QtWidgets import (
    QApplication, QSystemTrayIcon, QFrame, QWidget, QScrollArea,
    QHBoxLayout, QVBoxLayout, QSizePolicy, QLineEdit, QPushButton,
    QTextBrowser, QStyleOption, QMenu, QPlainTextEdit, QLabel
)
from PySide6.QtGui import (
    QKeySequence, QShortcut, QTextDocument, QTextCursor, QMouseEvent,
    QPainter, QIcon, QImage, QPixmap, QTextOption, QSyntaxHighlighter,
    QTextCharFormat, QColor
)
# WebEngineView用hide()方式时会崩溃，默认展示框用了textbrowser
# from PySide6.QtWebEngineWidgets import QWebEngineView 

# pynput 用于全局键盘事件
from pynput import keyboard

#
import markdown

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
from langchain.prompts import PromptTemplate
from langchain.schema import BaseMessage,HumanMessage,SystemMessage








# 环境变量，用于openai key等；
_ = load_dotenv(find_dotenv())  # 读取本地 .env 文件，里面定义了 OPENAI_API_KEY

# 版本
__version__ = "0.4.0"


# 日志器
class AAXWLoggerManager:
    _instance = None
    _initialized = False
    APP_LOGGER_NAME = "AAXW"
    
    APP_DEFAULT_LEVEL = logging.INFO

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AAXWLoggerManager, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not self._initialized:
            self.loggers = {}
            self.logDir = None
            self.fileHandler:logging.Handler = None #type:ignore
            self.consoleHandler:logging.Handler = None #type:ignore
            self.setupBasicLogger()
            self._initialized = True

    def setupBasicLogger(self):
        """设置基本的控制台处理器"""
        self.consoleHandler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        self.consoleHandler.setFormatter(formatter)

        # 设置应用级别日志器
        self.appLogger = logging.getLogger(self.APP_LOGGER_NAME)
        self.appLogger.propagate = False #不传播
        self.appLogger.setLevel(self.APP_DEFAULT_LEVEL)
        self.appLogger.addHandler(self.consoleHandler)

    #这里后续扩展出注册不同日志文件，可以关联不同范围或级别的日志。
    def setLogDirAndFile(self, logDir,filename="app.log"):
        """设置工作目录并创建文件处理器"""
        self.logDir = logDir
        log_file = os.path.join(logDir, filename)
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        self.fileHandler = TimedRotatingFileHandler(
            log_file,
            when="midnight",
            interval=1,
            backupCount=3,
            encoding='utf-8'
        )
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(module)s.%(funcName)s [%(filename)s:%(lineno)d] - %(message)s')
        self.fileHandler.setFormatter(formatter)

        # 更新所有现有的日志器
        for logger in self.loggers.values():
            if self.fileHandler not in logger.handlers:
                logger.addHandler(self.fileHandler)

        # 为应用级别日志器添加文件处理器
        self.appLogger.addHandler(self.fileHandler)

    def getLogger(self, name, level=None,isPropagate=False):
        """
        获取或创建一个日志器
        :param name: 日志器名称
        :param level: 日志级别，如果为None则不设置
        :param isPropagate: 是否传播日志消息到父日志器
        """
        full_name = f"{self.APP_LOGGER_NAME}.{name}" if name else self.APP_LOGGER_NAME
        if full_name not in self.loggers:
            logger = logging.getLogger(full_name)

            logger.propagate=isPropagate

            if level is not None:
                logger.setLevel(level)
            else:
                # 如果没有指定级别，则不设置，让它继承父级别
                logger.setLevel(logging.NOTSET)
            
            # 只有在这个日志器还没有处理器时才添加
            if not logger.handlers:
                logger.addHandler(self.consoleHandler)
                if self.fileHandler:
                    logger.addHandler(self.fileHandler)
            
            self.loggers[full_name] = logger
        return self.loggers[full_name]

    def getModuleLogger(self, module, level=None, isPropagate=False):
        """获取模块级别的日志器"""
        return self.getLogger(module.__name__, level, isPropagate)
    
    def getClassLogger(self, cls, level=None, isPropagate=False):
        """获取类级别的日志器"""
        return self.getLogger(f"{cls.__module__}.{cls.__name__}", level, isPropagate)
    
    def getClassLoggerByName(self, moduleName:str,className:str, level=None, isPropagate=False):
        """获取类级别的日志器"""
        return self.getLogger(f"{moduleName}.{className}", level, isPropagate)

    def classLogger(self, level=None, isPropagate=False):
        """为类添加日志器的装饰器  设置了类属性:AAXW_CLASS_LOGGER"""
        T = TypeVar('T')
        def decorator(cls:T)->T:
            # cls.AAXW_CLASS_LOGGER = self.getClassLogger(cls, level, isPropagate) #type:ignore
            setattr(cls, 'AAXW_CLASS_LOGGER', self.getClassLogger(cls, level, isPropagate))
            return cls
        return decorator

    def getRootLogger(self):
        """获取根日志器"""
        return logging.getLogger()

    def getAppLogger(self):
        """获取应用级别日志器"""
        return self.appLogger

    def setLoggerLevel(self, name, level):
        """设置指定日志器的级别"""
        full_name = f"{self.APP_LOGGER_NAME}.{name}" if name else self.APP_LOGGER_NAME
        if full_name in self.loggers:
            self.loggers[full_name].setLevel(level)

    def setLoggerFormatter(self, name, formatter):
        """设置指定日志器的格式器"""
        full_name = f"{self.APP_LOGGER_NAME}.{name}" if name else self.APP_LOGGER_NAME
        if full_name in self.loggers:
            for handler in self.loggers[full_name].handlers:
                handler.setFormatter(formatter)

# 创建日志管理器实例 globe层次；
AAXW_JUMPIN_LOG_MGR = AAXWLoggerManager()
# 本模块日志器
AAXW_JUMPIN_MODULE_LOGGER:logging.Logger=AAXW_JUMPIN_LOG_MGR.getModuleLogger(
    sys.modules[__name__])



# Di框架与插件框架
# framework-di , framework-plugin
class AAXWDependencyContainer:
    """
    简易的依赖组织容器
    注册依赖关系：
    @dependencyContainer.register('key', isSingleton=True, isLazy=True)
    class...

    创建/获取已有，资源对象，如其依赖未创建则会创建对应依赖：
    dependencyContainer.getAANode(key)
    
    """
    def __init__(self):
        self._factories: Dict[str, Callable] = {}
        self._dependencies: Dict[str, Dict[str, str]] = {}
        self._isSingletonFlags: Dict[str, bool] = {}
        self._isLazyFlags: Dict[str, bool] = {}
        self._instances: Dict[str, Any] = {}

    def register(self, key: str, isSingleton: bool = True, isLazy: bool = False, **dependencies):
        T = TypeVar('T', bound=Callable[..., Any])
        def decorator(f: T)-> T:
            self._factories[key] = f
            self._dependencies[key] = dependencies
            self._isSingletonFlags[key] = isSingleton
            self._isLazyFlags[key] = isLazy
            return f
        return decorator

    def getAANode(self, key: str) -> Any:
        if key not in self._factories:
            raise KeyError(f"没有注册名为 {key} 的依赖")
        
        isSingleton = self._isSingletonFlags[key]
        if isSingleton and key in self._instances:
            return self._instances[key]
        
        instance = self._createInstance(key)
        
        if isSingleton:
            self._instances[key] = instance
        
        return instance

    def setAANode(self, key: str, node: Any, isSingleton: bool = True, **dependencies):
        if isSingleton:
            self._instances[key] = node
        
        # 注册工厂函数
        self._factories[key] = lambda: node
        
        # 注册依赖关系
        self._dependencies[key] = dependencies
        
        # 设置单例和懒加载标志
        self._isSingletonFlags[key] = isSingleton
        self._isLazyFlags[key] = False  # setAANode 默认不使用懒加载
        
        # 注入依赖
        self._injectDependencies(node, dependencies)
        
        return node

    def _injectDependencies(self, instance: Any, dependencies: Dict[str, str]):
        for attr, dep_key in dependencies.items():
            if dep_key in self._instances:
                setattr(instance, attr, self._instances[dep_key])
            elif dep_key in self._factories:
                setattr(instance, attr, self.getAANode(dep_key))
            else:
                raise KeyError(f"依赖 {dep_key} 未注册")

    def _createInstance(self, key: str) -> Any:
        factory = self._factories[key]
        instance = factory()
        
        dependencies = self._dependencies[key]
        self._injectDependencies(instance, dependencies)
        
        return instance

    def _lazyProperty(self, dep_key):
        #返回改写属性为特定方法；
        #当第一次访问该属性时设置并返回
        def getter(obj):
            attr_name = f'_{dep_key}'
            if not hasattr(obj, attr_name) or getattr(obj, attr_name) is None:
                setattr(obj, attr_name, self.getAANode(dep_key)) #这里get是非线程安全的
            return getattr(obj, attr_name)
        return property(getter)

    def clear(self):
        self._instances.clear()
        self._factories.clear()
        self._dependencies.clear()
        self._isSingletonFlags.clear()
        self._isLazyFlags.clear()

class AAXWJumpinDICSingleton: #单例化
    """AAXWDependencyContainer的单例化工具类"""
    __instance = None
    _insLock = threading.Lock()
    # _opLock = threading.Lock()

    @classmethod
    def getInstance(cls):
        if cls.__instance is None:
            with cls._insLock:
                if cls.__instance is None:
                    cls.__instance = AAXWDependencyContainer()
        return cls.__instance

    @classmethod
    def register(cls, key: str, isSingleton: bool = True, isLazy: bool = False, **dependencies):
        return cls.getInstance().register(key, isSingleton, isLazy, **dependencies)

    @classmethod
    def getAANode(cls, key: str) -> Any:
        # with cls._opLock:
            return cls.getInstance().getAANode(key)

    @classmethod
    def setAANode(cls, key: str, node: Any, isSingleton: bool = True, **dependencies):
        return cls.getInstance().setAANode(key, node, isSingleton, **dependencies)

    @classmethod
    def clear(cls):
        with cls._insLock:
            if cls.__instance:
                cls.__instance.clear()
            cls.__instance = None

# 插件框架





# 基本config信息，与默认配置；
@AAXWJumpinDICSingleton.register(key="jumpinConfig") 
@AAXW_JUMPIN_LOG_MGR.classLogger()
class AAXWJumpinConfig:
    AAXW_CLASS_LOGGER:logging.Logger

    # 默认配置
    FAMILY_NAME="AAXW" #之后可用来拆分抽象；
    APP_NAME_DEFAULT = "AAXW_Jumpin"
    APP_VERSION_DEFAULT = __version__
    DEBUG_DEFAULT = False #暂时没用到
    LOG_LEVEL_DEFAULT = "INFO"
    APP_WORK_DIR_DEFAULT = "./"
    APP_CONFIG_FILENAME_DEFAULT = "aaxw_jumpin_config.yaml"

    # 原有的 QSS 配置保持不变
    MSGSHOWINGPANEL_QSS = """
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
        margin-left: 200px;
    }
    QTextBrowser[contentOwnerType="ROW_CONTENT_OWNER_TYPE_AGENT"] {
        background-color: #e6e6fa;
        color: #00008b;
    }
    """
    
    MAIN_WINDOWS_QSS = """
    QWidget#jumpin_main_window {
        /*background-color: #d4f2e7; 这个是特殊背景，用来调试界面样式*/
        background-color: #fff;
        border-radius: 10px;
    }
    """

    # 新增 INPUT_STYLE #非文本 而是 dict做法
    # 需要拼接为文本 self.promptInputEdit.setStyleSheet("; ".join([f"{k}: {v}" for k, v in AAXWJumpinConfig.INPUT_STYLE.items()]))
    INPUT_EDIT_QSS_DICT = {
        "border": "1px solid gray",
        "padding": "5px",
        "border-radius": "5px",
    }

    # 新增 INPUT_PANEL_STYLE
    INPUT_PANEL_QSS = """
        AAXWInputPanel {
            background-color: #f0f0f0;
            border-radius: 10px;
        }
        QPushButton {
            background-color: #4CAF50;
            color: white;
            border: none;
            padding: 5px 10px;
            border-radius: 5px;
        }
        QPushButton:hover {
            background-color: #45a049;
        }
    """

    def __init__(self):
        # 初始化实例属性
        self.appName = self.APP_NAME_DEFAULT
        self.appVersion = self.APP_VERSION_DEFAULT
        
        self.debug = self.DEBUG_DEFAULT
        self.logLevel = self.LOG_LEVEL_DEFAULT
        self.appWorkDir = self.APP_WORK_DIR_DEFAULT
        self.appConfigFilename = self.APP_CONFIG_FILENAME_DEFAULT

        #默认顺序初始化；
        self.loadEnv()
        self.loadArgs()
        self.loadYaml()
        self.AAXW_CLASS_LOGGER.info(f"All config loaded，new base-config: "
                    f"appWorkDir={self.appWorkDir}, "
                    f"logLevel={self.logLevel}, "
                    f"appConfigFilename={self.appConfigFilename}, "
                    f"debug={self.debug}")
        #暂时初始化时调用
        self.initAANode()



    def loadEnv(self):
        self.appWorkDir = os.environ.get('AAXW_APPWORKDIR', self.appWorkDir)
        self.logLevel = os.environ.get('AAXW_LOG_LEVEL', self.logLevel)
        self.appConfigFilename = os.environ.get('AAXW_CONFIG_FILE_NAME', self.appConfigFilename)
        self.debug = os.environ.get('AAXW_DEBUG', self.debug)

    def loadArgs(self):
        parser = argparse.ArgumentParser()
        parser.add_argument('--appworkdir', help='Application work directory')
        parser.add_argument('--log-level', help='Logging level')
        parser.add_argument('--config-file', help='Configuration file name')
        parser.add_argument('--debug', action='store_true', help='Enable debug mode')
        
        args, unknown = parser.parse_known_args()
        if args.appworkdir:
            self.appWorkDir = args.appworkdir
        if args.log_level:
            self.logLevel = args.log_level
        if args.config_file:
            self.appConfigFilename = args.config_file
        if args.debug is not None:
            self.debug = args.debug


    #yaml config
    def loadYaml(self,yamlPath=None):
        yaml_path = os.path.join(self.appWorkDir, self.appConfigFilename)
        if os.path.exists(yaml_path):
            with open(yaml_path, 'r', encoding='utf-8') as file:
                try:
                    yaml_config = yaml.safe_load(file)
                    self.__dict__.update(yaml_config)
                    self.AAXW_CLASS_LOGGER.info(f"Yaml config file loaded: new base-config"
                            f"appWorkDir={self.appWorkDir}, "
                            f"logLevel={self.logLevel}, "
                            f"appConfigFilename={self.appConfigFilename}, "
                            f"debug={self.debug}")
                except yaml.YAMLError as e:
                    self.AAXW_CLASS_LOGGER.warning(f"Error reading YAML file: {e}")

    def setWorkCfgAndloadYaml(self, workdir=None, configName=None):
        if workdir: self.appWorkDir = workdir
        if configName: self.appConfigFilename = configName
        self.loadYaml()

    def initAANode(self): #init after di；当前秀先在自己内部执行；
        #这里日志器进程全局的，所以其实__init__初始化时就能调用；
        AAXW_JUMPIN_LOG_MGR.setLogDirAndFile(logDir=self.appWorkDir,filename="aaxw_app.log")

        #其他di胡执行的工作；
        pass



        
    

    # @classmethod
    # def create_with_current_dir(cls):
    #     config = cls()
    #     script_dir = os.path.dirname(os.path.abspath(__file__))
    #     config.set_work_dir(script_dir)
    #     return config

#
# AI相关
#
class AbstractAIConnOrAgent(ABC):
    @abstractmethod
    def requestAndCallback(self, prompt: str, func: Callable[[str], None],isStream: bool = True):
        # raise NotImplementedError("Subclasses must implement sendRequestStream method")
        ...

    def embedding(self, prompt:str):
        ...

    def edit(self, prompt:str, instruction:str):
        ...
       



@AAXWJumpinDICSingleton.register(key="simpleAIConnOrAgent")
@AAXW_JUMPIN_LOG_MGR.classLogger()
class AAXWSimpleAIConnOrAgent(AbstractAIConnOrAgent):
    """
    简单实现的连接LLM/Agent的类，支持流式获取响应。
    使用Langchain封装的OpenAI的接口实现。
    """

    SYSTME_PROMPT_TEMPLE="""
    你的名字是ANAN是一个AI入口助理;
    请关注用户跟你说的内容，和善的回答用户，与用户要求。
    如果用户说的不明确，请提示用户可以说的更明确。
    如果被要求纯文本来回答，在段落后面增加<br/>标签。
    """

    USER_PROMPT_TEMPLE="""
    以下是用户说的内容：
    {message}
    """
    
    def __init__(self, api_key:str =None,base_url:str=None, model_name: str = "gpt-4o-mini"): # type: ignore
        """
        初始化OpenAI连接代理。
        
        :param api_key: OpenAI API密钥。
        :param base_url: OpenAI API基础URL。
        :param model_name: 使用的模型名称。
        """
        # 从环境变量读取API密钥和URL
        self.openai_api_key = api_key or os.getenv('OPENAI_API_KEY')
        self.openai_base_url = base_url or os.getenv('OPENAI_BASE_URL')
        self.model_name = model_name or os.getenv('OPENAI_MODEL_NAME', 'gpt-4o-mini')
        
        if not self.openai_api_key:
            raise ValueError("OpenAI API key is required.")
        
        chat_params = {
            "temperature": 0,
            "model": self.model_name,
            "api_key": self.openai_api_key,
        }
        
        if self.openai_base_url:
            chat_params["base_url"] = self.openai_base_url
        
        self.llm: ChatOpenAI = ChatOpenAI(**chat_params)
    
    @override
    def requestAndCallback(self, prompt: str, func: Callable[[str], None], isStream: bool = True):
        """
        发送请求到LLM，并通过回调函数处理流式返回的数据。
        
        :param prompt: 提供给LLM的提示文本。
        :param func: 用于处理每次接收到的部分响应的回调函数。
        :param isStream: 是否使用流式响应。
        """
        system_message = SystemMessage(content=self.SYSTME_PROMPT_TEMPLE)
        human_message = HumanMessage(content=self.USER_PROMPT_TEMPLE.format(message=prompt))
        messages = [system_message, human_message]
        
        if isStream:
            for msgChunk in self.llm.stream(messages):
                if msgChunk.content:
                    time.sleep(0.1)
                    func(str(msgChunk.content))
        else:
            response = self.llm.invoke(messages)
            func(str(response.content))

    def embedding(self, prompt: str, model: str = "text-embedding-ada-002"):
        """
        获取文本嵌入。
        
        :param prompt: 需要嵌入的文本。
        :param model: 使用的嵌入模型。
        :return: 文本的嵌入向量。
        """
        embeddings = OpenAIEmbeddings(
            api_key=self.openai_api_key,
            base_url=self.openai_base_url,
            model=model
        )
        return embeddings.embed_query(prompt)



@AAXWJumpinDICSingleton.register(key="ollamaAIConnOrAgent")
@AAXW_JUMPIN_LOG_MGR.classLogger()
class AAXWOllamaAIConnOrAgent(AbstractAIConnOrAgent):
    """
    直接使用OpenAI的接口实现。对Ollama的访问；
    """
    AAXW_CLASS_LOGGER:logging.Logger

    SYSTEM_PROMPT_DEFAULT="""
    你的名字是ANAN是一个AI入口助理;
    请关注用户跟你说的内容，和善的回答用户，与用户要求。
    如果用户说的不明确，请提示用户可以说的更明确。
    如果没有特别说明，可考虑用markdown格式输出一般内容。
    """

    USER_PROMPT_TEMPLE="""
    以下是用户说的内容：
    {message}
    """
    
    def __init__(self, model_name: str = "llama3.2:3b"): #llama3.2:3b qwen2:1.5b qwen2.5:7b
        self.client = OpenAI(
            base_url="http://localhost:11434/v1",
            api_key="ollama"
        )
        self.model_name = model_name
        
        models = self.listModels()
        self.AAXW_CLASS_LOGGER.info(f"Available Ollama models found: {', '.join(models)}")
        

    def listModels(self) -> List[str]:
        """列出可用的Ollama模型"""
        try:
            models = self.client.models.list()
            return [model.id for model in models.data]
        except Exception as e:
            raise Exception(f"Failed to list models: {str(e)}")
    

    @override
    def requestAndCallback(self, prompt: str, func: Callable[[str], None],isStream: bool = True):
        """使用OpenAI API风格生成流式聊天完成"""
        formatted_prompt = self.USER_PROMPT_TEMPLE.format(message=prompt)
        messages = [
            ChatCompletionSystemMessageParam(content=self.SYSTEM_PROMPT_DEFAULT, role="system"),
            ChatCompletionUserMessageParam(content=formatted_prompt, role="user")
        ]
        try:
            stream = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                stream=True
            )
            for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    content = chunk.choices[0].delta.content
                    func(content)
        except Exception as e:
            raise Exception(f"Failed to generate stream chat completion: {str(e)}")

@AAXWJumpinDICSingleton.register(key="aiConnOrAgentProxy")
@AAXW_JUMPIN_LOG_MGR.classLogger()
class AIConnOrAgentProxy(AbstractAIConnOrAgent):
    def __init__(self, innerInst: AbstractAIConnOrAgent=None): #type:ignore
        self.innerInstance = innerInst

    @override
    def requestAndCallback(self, prompt: str, func: Callable[[str], None],isStream: bool = True):
        return self.innerInstance.requestAndCallback(prompt, func=func,isStream=isStream)

    def setInnerInstance(self, innerInst: AbstractAIConnOrAgent):
        self.innerInstance = innerInst

# 线程异步处理AI IO任务。
@AAXW_JUMPIN_LOG_MGR.classLogger()
class AIThread(QThread):
    
    #newContent,id 对应：ShowingPanel.appendToContentById 回调
    updateUI = Signal(str,str)  

    def __init__(self,text:str,uiCellId:str,llmagent:AbstractAIConnOrAgent):
        super().__init__()
        
        # self.mutex = QMutex()
        self.text:str=text
        self.uiId:str=uiCellId
        self.llmagent:AbstractAIConnOrAgent=llmagent
        
    def run(self):
        self.msleep(500)  # 执行前先等界面渲染
        # self.mutex.lock()
        # print(f"thread inner str:{self.text} \n")
        self.llmagent.requestAndCallback(self.text, self.callUpdateUI)
        # self.mutex.unlock()
        
    def callUpdateUI(self,newContent:str):
        
        #
        # print(f"streaming, emitL{newContent} id:{self.uiId}")
        
        #
        # 最好强制类型转换。self.uiId:str 或 str(self.uiId)
        # 
        self.updateUI.emit(str(newContent), str(self.uiId)) 
        


##
# 界面组件相关
##
#
# 暂时单独放在input edit之外实现，
# TODO 之后考虑放在插件机制剥离实现？ 不分功能比如tab键的控制似乎可能不属于基础功能；
class EditEventFilter(QObject):
    """
    拦截 Tab 键，并替换为特定的功能；主要作用于InputEdit；
    Tab:
    """

    def __init__(self, mainWindow):
        super().__init__()
        self.manwindow: AAXWJumpinMainWindow = mainWindow

    def eventFilter(self, obj, event):
        # Tab按键改为控制左侧按钮按下执行 （该也可以考虑改为组合键control+Tab，似）
        if event.type() == QEvent.Type.KeyPress and event.key() == Qt.Key.Key_Tab:
            # print("Tab 键被按下")
            self.manwindow.inputPanel.funcButtonLeft.click()  # 点击左侧按钮
            return True  # 被过滤
        #
        return False

@AAXW_JUMPIN_LOG_MGR.classLogger()
class AAXWInputLineEdit(QLineEdit):
    """ 
    主要指令，提示信息，对话信息输入框； 
    """

    AAXW_CLASS_LOGGER:logging.Logger


    def __init__(self, mainWindow, parent=None):
        super().__init__(parent)
        self.mainWindow: AAXWJumpinMainWindow = mainWindow
        # 额外的事件处理器，如优先处理如Tab按下
        self.editEventHandler=EditEventFilter(self.mainWindow)
        self.installEventFilter(self.editEventHandler)
        
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
class AAXWInputPanel(QWidget):
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
        self.promptInputEdit = AAXWInputLineEdit(self.mainWindow, self)
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

        self.funcButtonLeft.clicked.connect(self.toggleLeftFunc)
        self.funcButtonRight.clicked.connect(self.rightButtonClicked)
        self.promptInputEdit.returnPressed.connect(self.enterClicked)


    ###
    # 基本行为封装
    ###
    # 左侧
    def toggleLeftFunc(self):
        if self.funcButtonLeft.text() == "Toggle":
            self.funcButtonLeft.setText("😊")
        else:
            self.funcButtonLeft.setText("😢")

    # 异步操作emit做法
    # def sendInputText(self):
    #     text = self.promptInputEdit.text()
    #     if text:
    #         self.sendRequest.emit(text)
    #         self.promptInputEdit.clear()
    # 
    # input 回车
    def enterClicked(self):
        # 处理回车事件
        self.AAXW_CLASS_LOGGER.debug("Enter key pressed!")
        self.funcButtonRight.click()

    # 右侧
    def rightButtonClicked(self):
        self.AAXW_CLASS_LOGGER.debug("Right button clicked!")

        text = self.promptInputEdit.text()
        self.mainWindow.handleInputRequest(text)
        
        self.promptInputEdit.clear()
        self._logInput()

    #
    def _logInput(self):
        # 打印输入框中的内容
        self.AAXW_CLASS_LOGGER.debug(f"Input: {self.promptInputEdit.text()}")


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


class ContentBlockStrategy(ABC):
    #TODO 改为DI容器维护策略。
    #单例化的
    strategies: Dict[str, Type['ContentBlockStrategy']] = {}


    @classmethod
    def register(cls, strategy_type: str):
        def decorator(subclass):
            cls.strategies[strategy_type] = subclass
            return subclass
        return decorator

    @classmethod
    def getStrategy(cls, strategy_type: str) -> 'ContentBlockStrategy':
        strategy = cls.strategies.get(strategy_type)
        if not strategy:
            raise ValueError(f"Unknown strategy type: {strategy_type}")
        return strategy()


    #TODO 这里临时用执行期注入，其实策略也最有定义期注入。使用实例化策略保存定义期需要的属性；
    #执行期可放入返回的
    @staticmethod
    @abstractmethod
    def createWidget(rowId: str, contentOwner: str, contentOwnerType: str,
                    mainWindow: QWidget, strategyWidget:QWidget) -> QWidget:
        pass

    @staticmethod
    @abstractmethod
    def initContent(widget: QWidget,content:str) -> QWidget:
        pass

    @staticmethod
    @abstractmethod
    def insertContent(widget: QWidget, content: str):
        pass

    @staticmethod
    @abstractmethod
    def adjustSize(widget: QWidget):
        pass
    
    
#定义期初始化对象了，其实不一定好。要用最好在最外层控制使用注册
@ContentBlockStrategy.register("text_browser")
@AAXW_JUMPIN_LOG_MGR.classLogger()
class TextBrowserStrategy(ContentBlockStrategy):

    AAXW_CLASS_LOGGER:logging.Logger

    # 用特殊符号最为追加占位标记
    MARKER = "[💬➡️🏁]"
    @staticmethod
    @override
    def createWidget(rowId: str, contentOwner: str, contentOwnerType: str, 
                     mainWindow: 'AAXWJumpinMainWindow', strategyWidget: 'AAXWScrollPanel') -> QTextBrowser:
        
        tb = QTextBrowser()
        tb.setObjectName(f"{AAXWScrollPanel.ROW_BLOCK_NAME_PREFIX}_{rowId}")
        tb.setProperty("id", rowId)
        tb.setProperty("contentOwner", contentOwner)
        tb.setProperty("contentOwnerType", contentOwnerType)
        # 高度先限定，然后根据内部变化，关闭滚动条
        tb.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        tb.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        # 关闭自动格式化？
        tb.setAutoFormatting(QTextBrowser.AutoFormattingFlag.AutoNone)
        tb.setLineWrapMode(QTextBrowser.LineWrapMode.WidgetWidth)

        # 设置基本样式；
        doc = QTextDocument()
        tb.setDocument(doc)
        doc.setDefaultStyleSheet("p { white-space: pre-wrap; }")


        # 内容改变改变高度
        tb.document().contentsChanged.connect(lambda: TextBrowserStrategy.adjustSize(tb))

        #初始化空间
        # initial_text = " "
        # doc.setHtml(initial_text)
        # tb.append(TextBrowserStrategy.MARKER)  # 这里增加一个追加内容用的特别Marker
        TextBrowserStrategy.initContent(widget=tb,content=" ")

        # 现在可以使用 main_window 和 panel 进行额外的设置或操作
        tb.setProperty("mainWindow", mainWindow)
        tb.setProperty("strategyWidget", strategyWidget)

        return tb

    @staticmethod
    @override
    def initContent(widget: QTextBrowser, content: str):
        tb=widget
        doc=tb.document()
         #初始化空间
        initial_text = content
        doc.setHtml(initial_text)
        tb.append(TextBrowserStrategy.MARKER)  # 这里增加一个追加内容用的特别Marker

    @staticmethod
    @override
    def insertContent(widget: QTextBrowser, content: str):
        # 使用游标进行查找marker并更新平文
        doc = widget.document()
        cursor = doc.find(TextBrowserStrategy.MARKER)
        if cursor:
            cursor.movePosition(QTextCursor.MoveOperation.PreviousCharacter, 
                                QTextCursor.MoveMode.MoveAnchor
            )
            cursor.insertHtml(f"{content}")  # 可以追加html但是会过滤掉不符合规范的比如div
            widget.repaint()  # 非线程调用本方法，可能每次都要重绘，否则是完成完后一次性刷新。
        else:
            TextBrowserStrategy.AAXW_CLASS_LOGGER.debug(
                "not found marker:" + TextBrowserStrategy.MARKER)

    @staticmethod
    @override
    def adjustSize(widget: QTextBrowser):
        
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



class PythonHighlighter(QSyntaxHighlighter):
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

    def highlightBlock(self, text):
        for pattern, format in self.highlightingRules:
            expression = QRegularExpression(pattern)
            it = expression.globalMatch(text)
            while it.hasNext():
                match = it.next()
                self.setFormat(match.capturedStart(), match.capturedLength(), format)

class CodeBlockWidget(QWidget): #QWidget有站位，但是并不绘制出来。
    def __init__(self, code, title="Unkown", parent=None):
        super().__init__(parent)
        self.sizeChangedCallbacks = []
        self.title = title

        self.setStyleSheet("""
            CodeBlockWidget {
                background-color: #1E1E1E;
                border-radius: 5px;
                overflow: hidden;
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
        for color in ['#ED6A5E', '#F4BF4F', '#61C554']:  # 红、黄、绿按钮
            button = QPushButton()
            button.setFixedSize(15, 15)
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
        self.highlighter = PythonHighlighter(self.codeEdit.document())

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
        
        
        # print(f"Adjusted height: {totalHeight}px, Lines: {lineCount}")
        return totalHeight

    def sizeHint(self): #重写 预期尺寸
        width = self.width()
        height = self.expectantHeight()
        return QSize(width, height)
    
@AAXW_JUMPIN_LOG_MGR.classLogger(level=logging.DEBUG)
class CompoMarkdownContentBlock(QFrame): #原来是QWidget
    AAXW_CLASS_LOGGER:logging.Logger

    MIN_HEIGHT = 50  # 设置一个最小高度

    # 基础QSS样式
    BASE_QSS = """
    /* */
    CompoMarkdownContentBlock {
        background-color: #f0f0f0;
        border: none ;
        border-radius: 5px;
    }
    CompoMarkdownContentBlock[contentOwnerType="ROW_CONTENT_OWNER_TYPE_USER"] {
        border: 1px solid #a0a0a0;
        background-color: #d4f2e7;
        margin-left: 200px; /* 模拟右对齐，实际最好脚本中用layout实现对齐； */
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
        newWidget = CodeBlockWidget(code,title=title)
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
        if isinstance(self.currentWidget, CodeBlockWidget):
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

        

@ContentBlockStrategy.register("compoMarkdownContentStrategy") 
class CompoMarkdownContentStrategy(ContentBlockStrategy):
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

    @staticmethod
    @override
    def createWidget(rowId: str, contentOwner: str, contentOwnerType: str, 
                     mainWindow: 'AAXWJumpinMainWindow', strategyWidget: 'AAXWScrollPanel') -> CompoMarkdownContentBlock:
        
        mdBlock = CompoMarkdownContentBlock()
        mdBlock.setObjectName(f"{AAXWScrollPanel.ROW_BLOCK_NAME_PREFIX}_{rowId}")
        mdBlock.setProperty("id", rowId)
        mdBlock.setProperty("contentOwner", contentOwner)
        mdBlock.setProperty("contentOwnerType", contentOwnerType)

        #根据contentOwnerType提供不同的展示：
        # mdBlock.

        #
        # 
        # 当内容变更时调整控件尺寸，这里主要是高度；
        # 
        # 注册内容变化的回调
        # mdBlock.registerContentChangeCallback(
        #     lambda: CompoMarkdownContentStrategy.adjustSize(mdBlock) #
        # )
        mdBlock.registerSizeChangedCallbacks(
             lambda: CompoMarkdownContentStrategy.onSizeChanged(mdBlock) #
        )

        # 设置属性以便后续操作
        mdBlock.setProperty("mainWindow", mainWindow)
        mdBlock.setProperty("strategyWidget", strategyWidget)

        # 先写入点东西
        mdBlock.addContent(" \n")

        return mdBlock

    @staticmethod
    @override
    def initContent(widget: CompoMarkdownContentBlock, content: str):

        # widget.clear()
        widget.addContent(content)
        # qs:QSize=widget.currentWidget.sizeHint() #type:ignore

        # 由于主线程有sleep会阻碍重绘，导致曹方法失效；（主要是方法 ）
        # 如果曹方法失效
        # 1秒钟后（保证展示出来后）重绘1次大小
        QTimer.singleShot(1000, widget.currentWidget.adjustSize)#type:ignore
        # 马上调用没用。
        # widget.currentWidget.adjustSize()

    @staticmethod
    @override
    def insertContent(widget: CompoMarkdownContentBlock, content: str):
        widget.addContent(content)


    @staticmethod
    def onSizeChanged(widget: CompoMarkdownContentBlock):
        
        # 为啥一下子高度就满了？
        # 调整主窗口高度
        mainWindow: "AAXWJumpinMainWindow" = widget.property("mainWindow")
        if mainWindow:
            mainWindow.adjustHeight()

    

    @staticmethod
    @override
    def adjustSize(widget: CompoMarkdownContentBlock):
        widget.adjustSize()

        # 调整主窗口高度
        mainWindow: "AAXWJumpinMainWindow" = widget.property("mainWindow")
        if mainWindow:
            mainWindow.adjustHeight()
        pass

@AAXW_JUMPIN_LOG_MGR.classLogger()
class AAXWScrollPanel(QFrame):
    """
    垂直方向以列表样式可追加内容的展示面板；
    内容所在Row部件会根据内容调整高度；
    内部聚合了定制的vbxlayout，增加content时默认使用TextBrowser用作Row展示。
    提供了为RowContent追加内容的方式，支持流式获取文本追加到Row中。
    """
    AAXW_CLASS_LOGGER:logging.Logger
    
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
    # 区分展示内容行的类型
    ROW_CONTENT_OWNER_TYPE_USER="ROW_CONTENT_OWNER_TYPE_USER"
    ROW_CONTENT_OWNER_TYPE_AGENT="ROW_CONTENT_OWNER_TYPE_AGENT"
    ROW_CONTENT_OWNER_TYPE_SYSTEM="ROW_CONTENT_OWNER_TYPE_SYSTEM"

    def __init__(self, mainWindow: "AAXWJumpinMainWindow", qss:str=DEFAULT_STYLE, parent=None, strategy_type="text_browser"):
        """
        当前控件展示与布局结构：
        AAXWScrollPanel->QVBoxLayout->QScrollArea->QWidget(scrollWidget)-> TB等
        """
        super().__init__(parent)
        self.mainWindow = mainWindow
        self.setFrameShape(QFrame.Shape.StyledPanel)
        # self.setFrameShadow(QFrame.Raised) #阴影凸起
        self.setStyleSheet(qss)
   

        self.strategy = ContentBlockStrategy.getStrategy(strategy_type)

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


    def addRowContent(self, content, rowId, contentOwner="unknown", 
                      contentOwnerType=ROW_CONTENT_OWNER_TYPE_SYSTEM, isAtTop=True):
        """
        在scrollLayout上添加一个内容行，默认使用QTextBrowser。
        默认在顶端加入；
        rowId 表示内容行的唯一标识，用于后续查找，组件定位；
        """
        
        widget = self.strategy.createWidget(rowId, contentOwner, contentOwnerType, self.mainWindow, self)
        
        # 加入列表
        if isAtTop:
            self.scrollLayout.addWidgetAtTop(widget)  # 这里每次在头部加layout定制了
        else:
            self.scrollLayout.addWidget(widget)
        
        self.strategy.initContent(widget, content)


    def appendContentByRowId(self, text, rowId: str):
        """
        在指定Rowid的Row中追加内容
        """
        # 查找对应的 QWidget 并追加内容
        # 用名字查找元素
        widget = self.scrollWidget.findChild(
            QWidget, f"{self.ROW_BLOCK_NAME_PREFIX}_{rowId}"
        )
        #TODO findChild 默认返回的是object，这里类型需要处理一下；
        if widget:
            self.strategy.insertContent(widget, text) #type:ignore
            # self.strategy.adjustSize(widget) #type:ignore
            # self.mainWindow.adjustHeight()
        else:
            self.AAXW_CLASS_LOGGER.debug(f"Not found widget by name: {self.ROW_BLOCK_NAME_PREFIX}_{rowId}")

    # 
    # Panel的内部基于scroll-widget增加组件后的期望尺寸；
    def expectantHeight(self):
        # 关键点是Panel，scrollArea的实际大小与 self.scrollArea.widget() 提供的大小即内部期望的大小是不一样的。
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



    #
    # 可增加事件过滤器，需要时可以install到外部大窗口上。比如QEvent.Type.Resize事件触发动作。
    # 
    pass  # AAXWScrollPanel end

from typing import cast
class AAXWJumpinMainWindow(QWidget):
    """
    主窗口:
        包含所有组件关联：
    """
    
    MAX_HEIGHT = 500
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.installAppHotKey()

        # 转容器关联；
        self.jumpinConfig:AAXWJumpinConfig = None; #type:ignore
        self.llmagent:AbstractAIConnOrAgent=AIConnOrAgentProxy(AAXWSimpleAIConnOrAgent())
        
        # self.llmagent=AIConnAgentProxy(AAXWOllamaAIConnAgent())

    
    def init_ui(self):
        
        self.setObjectName("jumpin_main_window")
        self.setStyleSheet(AAXWJumpinConfig.MAIN_WINDOWS_QSS)
        
        # 界面主布局，垂直上下布局；
        mainVBoxLayout = QVBoxLayout()  

        self.inputPanel = AAXWInputPanel(self,self)
        # self.inputPanel.sendRequest.connect(self.handleInputRequest)

        msgShowingPanel = AAXWJumpinConfig.MSGSHOWINGPANEL_QSS
        self.msgShowingPanel = AAXWScrollPanel(
            mainWindow=self, 
            qss=msgShowingPanel, 
            parent=self,
            strategy_type='compoMarkdownContentStrategy',
        )

        mainVBoxLayout.addWidget(self.inputPanel)
        mainVBoxLayout.addWidget(self._createAcrossLine(QFrame.Shape.HLine))
        mainVBoxLayout.addWidget(self.msgShowingPanel)  # showing panel
        self.setLayout(mainVBoxLayout)

        # 主窗口设置
        self.setWindowTitle("快捷键唤起输入框")
        # self.setGeometry(300, 300, 600, 120)
        self.setMinimumSize(600, 120)  # 限定大小
        self.setMaximumSize(600, self.MAX_HEIGHT)
        
        self.setWindowFlags(self.windowFlags()| Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
         # self.setWindowFlags(self.windowFlags()| Qt.WindowType.WindowStaysOnTopHint) #默认钉在最上层
        

        # 设置窗口大小策略
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)

        # 初始高度为 200 像素
        # self.setFixedHeight(200) 
        self.resize(self.width(), 200)

        self.inputPanel.promptInputEdit.setFocus()

    def handleInputRequest(self, text):

        # 用户输入容消息气泡与内容初始化
        rid = int(time.time() * 1000)
        self.msgShowingPanel.addRowContent(
            content=text, rowId=rid, contentOwner="user_xiaowang",
            contentOwnerType=AAXWScrollPanel.ROW_CONTENT_OWNER_TYPE_USER,
        )
        # self.msgShowingPanel.repaint() #重绘然后然后再等待？
        
        # FIXME 阻塞主线程可能会，这里可能会导致回调曹方法失效。应为计算尺寸与绘制是两个线程完成的。
        # 互相又依赖数据。如果没有重绘，则会应该可以拿到新尺寸的没拿到。
        # 这里考虑用其他方法生成不同的id更好。
        # 
        # 等待0.5秒
        # 使用QThread让当前主界面线程等待0.5秒
        QThread.msleep(500) 
        # 反馈内容消息气泡与内容初始化
        rrid = int(time.time() * 1000)
        self.msgShowingPanel.addRowContent(
            content="", rowId=rrid, contentOwner="assistant_aaxw",
            contentOwnerType=AAXWScrollPanel.ROW_CONTENT_OWNER_TYPE_AGENT,
        )

        #
        #生成异步处理AI操作的线程
        #注入要用来执行的ai引擎以及 问题文本+ ui组件id
        #FIXME 执行时需要基于资源，暂时锁定输入框；
        #           多重提交，多线程处理还没很好的做，会崩溃；
        self.aiThread = AIThread(text, str(rrid), self.llmagent)
        self.aiThread.updateUI.connect(self.msgShowingPanel.appendContentByRowId)
        self.aiThread.start()

        #同步方式调用: 界面会hang住。
        # self.llmagent.send_request(text, 
        #      lambda content:self.msgShowingPanel.appendToContentById(content,rrid ))


    #
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
        painter.drawRoundedRect(rect, 20, 20)

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

    #
    ##
    # 装载关联快捷键
    # 特殊按键处理器
    # end
    ##


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

    #
    # 根据内部部件大小调整主窗口自身大小；还是本来就有这个设置？
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

@AAXW_JUMPIN_LOG_MGR.classLogger()
class AAXWGlobalShortcut:
    # 全局快捷键 运行器
    AAXW_CLASS_LOGGER:logging.Logger

    def __init__(self, mainWindow: AAXWJumpinMainWindow):
        self.mainWindow: AAXWJumpinMainWindow = mainWindow
        self.hotkey = keyboard.GlobalHotKeys({"<alt>+z": self.on_activate})

    def on_activate(self):
        self.AAXW_CLASS_LOGGER.debug("全局快捷键<alt>+z被触发")
        self.mainWindow.toggleHidden()

    def start(self):
        self.hotkey.start()

    def stop(self):
        self.hotkey.stop()

@AAXW_JUMPIN_LOG_MGR.classLogger(level=logging.DEBUG)
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
    agstool=None
    try:
        app = QApplication(sys.argv)
        mainWindow = AAXWJumpinMainWindow()
        AAXWJumpinDICSingleton.setAANode(
            key="mainWindow",node=mainWindow,
            llmagent='ollamaAIConnOrAgent',
            jumpinConfig='jumpinConfig')
        tray=AAXWJumpinTrayKit(mainWindow)
        agstool = AAXWGlobalShortcut(mainWindow)
        
        agstool.start()
        tray.show()
        mainWindow.show()
        mainWindow.raise_()
        sys.exit(app.exec())
    except Exception as e:  
        AAXW_JUMPIN_MODULE_LOGGER.error("Main Exception:", e)
        raise e
    finally:
        if agstool:agstool.stop()
        AAXWJumpinDICSingleton.clear()
        

if __name__ == "__main__":
    main()
    pass


##
# 遗留代码，待删除；
##
...