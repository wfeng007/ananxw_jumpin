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
# @Date:2024-09-24 18:05:01
# @Last Modified by:wfeng007
#
##
# AnAn jumpin 是AI网络/节点（随便什么吧），AI(+Applet kits)智能工具套件快速快速入口，
#   投入ai吧！ANAN其实也是只狗狗。。。
# An AI Net/Node of XiaoWang ， jumpin AI ! ANAN is a dog...
#
##
# 0.1:基础功能，基础chat功能，openai ollama接入，界面等；
# 0.2:托盘功能；支持钉在桌面最前端，全局热键换出与隐藏；
# 0.3:较好的Markdown展示气泡，基本可扩展的展示气泡逻辑;python代码块展示；
# 0.4+:
#      已增加工作目录配置与维护，基本文件系统能力。
#      已增加日志功能，默认标准输出中输出；支持工作目录生成日志；并根据时间与数量清理；
#      已增加简易注入框架；更好组织代码逻辑；
#      
# 0.5+: @Date:2024-11-03左右开始
#      已增加可切换的Applet 功能，applet可根据自己功能逻辑调用资源与界面完成相对专门的特性功能；
#      已增简易插件框架；支持二次开发；
# 
# 计划与路线
# 0.6+: @Date:2024-11-12左右开始 - 11-26日左右结束 
#       已增加通用工具消息面板（上或下），附加展示功能面板（左或右），
#           不同Applet可以定制自己的工具面板，展示面板等等。
#       已增加 本地Ollama模型使用与简单管理功能（使用单独的内置插件模块文件：builtin_plugins.py实现）
#       chat 信息展示界面问题修订，代码块展示功能按钮基本实现；
#       注释说明整体梳理，初步建设1抡项目说明与二开参考说明
#       增加chat history（memory）与多轮对话功能，提示词模版功能；并提供例子；
#
# 0.7+：@Date: 2024-12-03 - 12-21
#       已增加基本向量数据库（基于chroma 0.5.23实现），支持形成基本rag能力；并提供例子
#       已完成 打包与发布版初步建设；且支持chroma 0.5.23版本；

# 0.8+  @Date: 2025-01-05 - 01-22
#       已提供整体导航栏；
#       已提供基础线程框架，集中异步处理与界面异步处理；保证可用性与稳定性，防止QTread崩溃；
#       已沉淀前期样例中的功能-历史记忆等到核心功能中；
#       已在主导航中增加applet/agent列表与切换能力；

# 
# 0.9+
#       已实现初步的agent框架能力，提供1个agent样例如：自主动态改名；
#       已实现专门的记忆/历史列表面板、单项记忆/历史card化展示及其操作功能；
#       mac运行支持与打包支持；
#
#       代码块需支持plaintext/unknown 以及其他结构，未知，平文为全白。
#       提供其他ai相关样例，如：chateveredit等
#       coze集成对接应用样例；
#       dify集成对接样例；
#       可集成密塔等搜索；
#       支持可能轻量级，流程式agent/多agent
#       轻量级meta agent；
#      
#       
# 
#

# import pstats
import sys, os,time
import re 
import traceback
from datetime import datetime

# 包与模块命名处理：
try:
    #如果所在包有 __init__.py 且设置了__package_name__ 就能导入。如果没有则用目录名。
    from __init__ import __package_name__  #type:ignore
    print(f'导入了包__init__.py 中的 __package_name__:{__package_name__}')
except ImportError:
    #   pyinstaller 后os.path.abspath(__file__)"本文件"来确定路径会变成 _interal目录（默认资源目录）
    __package_name__= "ananxw_jumpin"
    print(f'导入本代码文件:{__file__} 中的 __package_name__:{__package_name__}')


def _setup_app_env_():
    # 设定在不同模式下环境情况

    if __name__ == "__main__": #作为入口运行
        # 为自己增加注册模块名：以 "包.文件主名" 为模块名
        _file_basename = os.path.splitext(os.path.basename(__file__))[0]
        sys.modules[f"{__package_name__}.{_file_basename}"] = sys.modules["__main__"]
        print(f"\n{__package_name__}.{_file_basename} 已设置到 sys.modules")
        # del _file_basename

        # 将当前目录作为包的根目录
        # if base_path not in sys.path:
        #     sys.path.insert(0, base_path)

        if getattr(sys, 'frozen', False):
            # 作为入口运行 且为打包后执行： 
            # 注意打包后，根目录名未必是ananxw_jumpin，所以无法用增加祖父目录为扫描路径的方式发现本包

            # base_path = os.path.dirname(sys.executable) #可执行文件的运行所在路径
            # 
            ...
        else:
            # 作为入口运行 且为开发环境直接执行
            # base_path = os.path.dirname(os.path.abspath(__file__))

            # 获取当前文件的父目录的父目录（如 projectlab/）
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            if project_root not in sys.path:
                sys.path.insert(0, project_root)  # 插入到路径最前面
            ...
    else :
        # 作为模块导入运行        
        pass
_setup_app_env_()


from typing import Callable, List, Dict, Type,Any,TypeVar,Union,cast, Tuple,Protocol,Optional
from typing import cast
from pydantic import BaseModel, Field # pydantic对象模型支持
from functools import wraps

try:
    from typing import override #python 3.12+ #type:ignore
except ImportError:
    from typing_extensions import override #python 3.8+
from abc import ABC, abstractmethod
import importlib

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
# WebEngineView用hide()方式时会崩溃，默认展示框用了textbrowser
# from PySide6.QtWebEngineWidgets import QWebEngineView 

# qfluentwidgets(PySide6-Fluent-Widgets) pyside6上的界面扩展
from qfluentwidgets import (
    NavigationInterface, NavigationItemPosition, NavigationAvatarWidget,NavigationTreeWidget,
    NavigationPushButton,MessageBoxBase,SubtitleLabel,LineEdit,CaptionLabel,PushButton,
    BodyLabel,TextWrap,CardWidget,StrongBodyLabel,PlainTextEdit,TextEdit,TextBrowser,
    SegmentedWidget,ComboBox,CheckBox,FlowLayout,InfoBar,InfoBarPosition,EditableComboBox,
    PillPushButton,PrimaryPushButton,
    NavigationWidget, MessageBox, SettingCardGroup, SwitchSettingCard, FolderListSettingCard,
    OptionsSettingCard, PushSettingCard, HyperlinkCard, PrimaryPushSettingCard, ScrollArea,
    ComboBoxSettingCard, ExpandLayout, Theme, CustomColorSettingCard,RadioButton,IconWidget,
    setTheme, setThemeColor, RangeSettingCard, isDarkTheme, ConfigItem, SettingCard, qrouter
)
from qfluentwidgets import FluentIcon as FIF
#


# pynput 用于全局键盘事件
from pynput import keyboard
# from pydantic.deprecated.decorator import ValidatedFunction
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

from langchain_community.chat_message_histories.file import FileChatMessageHistory
from langchain.prompts import PromptTemplate
from langchain.schema import (
        BaseMessage,
        AIMessage,  # 等价于OpenAI接口中的assistant role
        HumanMessage,  # 等价于OpenAI接口中的user role
        SystemMessage  # 等价于OpenAI接口中的system role
    )
from langchain.memory import ConversationBufferMemory


# ollama使用web客户端工具
import urllib.parse
import urllib.request
import json



#本包 导入
from ananxw_jumpin.ananxw_framework import AAXWDependencyContainer
from ananxw_jumpin.ananxw_jumpin_comm import AAXW_JUMPIN_LOG_MGR,AAXWJumpinDICUtilz
#
from ananxw_jumpin.ananxw_aiagent import BaseAgentAction,AgentEnvironment, BaseAgent

##
# 导入结束
##

# 读取补充环境变量的配置.env，find_dotenv()
#   会以本文件为基础逐层目录往上寻找，直到寻找到为止。
__evnpath=find_dotenv()
print(f"Found evnpath: {__evnpath} , will load it.")
_ = load_dotenv(__evnpath)  #

# 版本
__version__ = "0.9.0"

#本模块，模块日志器
AAXW_JUMPIN_MODULE_LOGGER:logging.Logger=AAXW_JUMPIN_LOG_MGR.getModuleLogger(
    sys.modules[__name__])


##
# 基本 插件框架与机制
##
class AAXWAbstractBasePlugin(ABC):
    """
    抽象插件基类；
    定义了插件的基本接口与插件框架关联实现。
    
    插件生命周期包括：
    1. 检测：插件管理器扫描文件系统，识别潜在插件类
    2. 加载：导入插件模块，检索插件类
    3. 安装：实例化插件类，调用onInstall方法
    4. 启用/禁用：激活或停用插件功能
    5. 卸载：清理插件资源，调用onUninstall方法
    
    开发新插件与扩展管理器，例如：
    1. 继承此抽象类并实现所有抽象方法；
    2. 通过AAXWFileSourcePluginManager或其子类自动扫描载入并生命周期管理；
    3. 扩展管理器可在实例化插件时增加注入资源，如AAXWJumpinPluginManager实现中增加了:
        - dependencyContainer: DI容器实例
        - jumpinConfig: 应用配置实例 
        - mainWindow: 主窗口实例
    """

    @abstractmethod
    def onInstall(self):
        """
        插件安装时的回调方法
        建议实现:
            - 初始化插件所需的资源
            - 注册插件提供的服务到DI容器
            - 设置插件的配置信息
            - 创建必要的UI组件
        """
        pass

    @abstractmethod
    def onUninstall(self):
        """
        插件卸载时的回调方法
        建议实现:
            - 清理插件创建的资源
            - 从DI容器注销服务
            - 保存配置信息
            - 移除UI组件
        """
        pass

    @abstractmethod
    def enable(self):
        """
        启用插件功能时的回调方法
        建议实现:
            - 激活插件的功能
            - 显示插件的UI组件
            - 注册事件监听器
            - 启动后台服务
        """
        pass

    @abstractmethod
    def disable(self):
        """
        禁用插件功能时的回调方法
        建议实现:
            - 停用插件的功能
            - 隐藏插件的UI组件
            - 注销事件监听器
            - 停止后台服务
        """
        pass

# 插件框架
@AAXW_JUMPIN_LOG_MGR.classLogger()
class AAXWFileSourcePluginManager:
    """
    1 插件管理类
    负责检测、加载、安装、卸载、启用和禁用插件
    插件生命周期包括：
    - 检测：扫描文件系统，识别潜在插件
    - 加载：导入插件模块，检索插件类
    - 安装：实例化插件类，调用onInstall方法
    - 启用/禁用：激活或停用插件功能
    - 卸载：清理插件资源，调用onUninstall方法
    
    2. 动态插件加载：
   - 自动扫描指定目录，支持多层目录结构
   - 使用importlib动态导入和重新加载插件模块
   - 支持以下目录结构：
     plugins/
     ├── plugin_basic.py          # 导入为: plugins.plugin_basic
     ├── plugin_core.py           # 导入为: plugins.plugin_core
     └── plugin_features/         # 特性插件目录
         ├── __init__.py
         ├── plugin_feature1.py   # 导入为: plugins.plugin_features.plugin_feature1
         └── plugin_feature2.py   # 导入为: plugins.plugin_features.plugin_feature2

    3. 插件命名和加载规则：
   - DEFAULT_PLUGIN_PREFIX: 用于过滤文件和目录名（默认为"plugin_"）
   - DEFAULT_PACKAGE_PREFIX: 用于构建Python包的导入路径（默认为"plugins"）
   - 顶级目录插件直接使用包名前缀
   - 子目录插件使用"包名前缀.子目录名.模块名"的形式
    """
    AAXW_CLASS_LOGGER:logging.Logger

    # 用于过滤文件和目录的前缀
    DEFAULT_PLUGIN_PREFIX = "plugin_"
    # 用于模块导入时的包名前缀
    DEFAULT_PACKAGE_PREFIX = "plugins"
    # 改为内置插件前缀
    # BUILTIN_PACKAGE_PREFIX = "builtin_plugins"  # 原 SYSTEM_PACKAGE_PREFIX
    # 使用getattr()来安全地获取包名，如果不存在则使用默认值 
    #     当前本文件main函数中 直接 pluginManager.builtinPackagePrefix="ananxw_jumpin"
    BUILTIN_PACKAGE_PREFIX = getattr(globals(), '__package_name__', "builtin_plugins")

    
    def __init__(self, rootDirectory: str = 'plugins', 
                 pluginPrefix: Union[str , None] = None,
                 packagePrefix: Union[str , None] = None,
                 builtinPackagePrefix: Union[str , None] = None):
        
        self.pluginRootDirectory = rootDirectory
        self.pluginPrefix = pluginPrefix or AAXWFileSourcePluginManager.DEFAULT_PLUGIN_PREFIX
        self.packagePrefix = packagePrefix or AAXWFileSourcePluginManager.DEFAULT_PACKAGE_PREFIX
        self.builtinPackagePrefix = \
            builtinPackagePrefix or AAXWFileSourcePluginManager.BUILTIN_PACKAGE_PREFIX
        
        # 可以看做保存了类构建器函数；
        # 检测扫描到的插件建设器要么是个类 要么是 工厂函数，
        # TODO 之后可能扩展builder策略实现
        self.pluginBuilders: Dict[
            str, Union[Type[AAXWAbstractBasePlugin], Callable[[], AAXWAbstractBasePlugin]]
        ] = {}

        self.installedPlugins: Dict[str, AAXWAbstractBasePlugin] = {}
        self.modules: Dict[str, Any] = {}
        # 改为内置插件跟踪
        self.builtinPluginBuilders: Dict[
            str, Union[Type[AAXWAbstractBasePlugin], Callable[[], AAXWAbstractBasePlugin]]
        ] = {}  # 原 systemPlugins

    ##
    # 检测文件系统加载plugin的builder，释放等 插件容器生命周期管理
    ##
    def detectPlugins(self):
        """检测并加载插件目录中的所有插件"""
        if not os.path.exists(self.pluginRootDirectory):
            # os.makedirs(self.pluginFolder)
            raise FileNotFoundError(f"插件目录 '{self.pluginRootDirectory}' 不存在")
        
        for item in os.listdir(self.pluginRootDirectory):
            itemPath = os.path.join(self.pluginRootDirectory, item)
            
            if os.path.isdir(itemPath) and item.startswith(self.pluginPrefix):
                self._detectPluginsFromDirectory(itemPath)
            elif item.endswith('.py') and item.startswith(self.pluginPrefix):
                self._loadPluginModule(itemPath)

    def _detectPluginsFromDirectory(self, directory: str):
        """从指定目录检测插件模块"""
        for filename in os.listdir(directory):
            if filename.endswith('.py') and filename.startswith(self.pluginPrefix):
                pluginPath = os.path.join(directory, filename)
                self._loadPluginModule(pluginPath)

    def _loadPluginModule(self, pluginPath: str):
        """加载单个插件模块"""
        try:
            moduleName = os.path.basename(pluginPath)[:-3]
            dirName = os.path.basename(os.path.dirname(pluginPath))
            
            if dirName == self.pluginRootDirectory:
                fullModuleName = f"{self.packagePrefix}.{moduleName}"
            else:
                fullModuleName = f"{self.packagePrefix}.{dirName}.{moduleName}"

            try:
                # 导入到sys.modules 
                module = importlib.import_module(fullModuleName)
                #

                # 自己也保留
                self.modules[fullModuleName] = module
                self._detectPluginBuildersFromModule(module, fullModuleName)
            except ImportError as e:
                self.AAXW_CLASS_LOGGER.error(f"导入模块 {fullModuleName} 时出错: {e}")
            except Exception as e:
                self.AAXW_CLASS_LOGGER.error(f"加载模块 {fullModuleName} 时发生意外错误: {e}")
        except Exception as e:
            self.AAXW_CLASS_LOGGER.error(f"处理插件文件 {pluginPath} 时出错: {e}")
    
    def _detectPluginBuildersFromModule(self, module: Any, moduleName: str, isBuiltin=False):
        """检测模块中的插件"""
        for attrName in dir(module):
            attr = getattr(module, attrName)
            #
            # 这里的判断需要导入的模块中 引用的AAXWAbstractBasePlugin有ananxw_junmpin的前缀模块中，
            # 否则， issubclass 可能会检错为否？
            #
            if isinstance(attr, type) and issubclass(attr, AAXWAbstractBasePlugin) and attr is not AAXWAbstractBasePlugin:
                plugin_key = f"{moduleName}.{attrName}"
                self._putPluginBuilder(pluginKey=plugin_key,
                    builder=attr,isBuiltin=isBuiltin)

    def _putPluginBuilder(self, pluginKey:str,builder,isBuiltin:bool):
        if isBuiltin:
            self.builtinPluginBuilders[pluginKey] = builder
        self.pluginBuilders[pluginKey] = builder
    
    def detectBuiltinPlugins(self):
        """从内置模块中检测插件"""
        # 获取所有符合前缀的模块名称
        builtin_module_names = [  # 原 system_module_names
            name for name in sys.modules.keys() 
            if name.startswith(self.builtinPackagePrefix)
        ]
        self.AAXW_CLASS_LOGGER.info(
            f"基于模块名前缀{self.builtinPackagePrefix}，准备扫描的内置builtin可能所在模块:{builtin_module_names}")
        # 处理符合条件的模块
        for module_name in builtin_module_names:
            try:
                module = sys.modules[module_name]
                self._detectPluginBuildersFromModule(
                    module=module, moduleName=module_name, isBuiltin=True
                )
            except Exception as e:
                self.AAXW_CLASS_LOGGER.error(f"从{module_name}检测内置插件时发生错误: {e}")
    
    def release(self):
        """释放所有插件资源，在需要插件机制关闭时调用"""
        # 卸载所有已安装的插件
        for plugin_name in list(self.installedPlugins.keys()):
            self.uninstallPlugin(plugin_name)
        
        # 清空所有缓存的数据
        self.pluginBuilders.clear()
        self.builtinPluginBuilders.clear()
        self.modules.clear()
        self.installedPlugins.clear()
        
        self.AAXW_CLASS_LOGGER.info("插件管理器已释放资源。plugin manager relased!")
    #
    # 检测-加载与释放  end
    ##


    ##
    # 实例化与安装卸载以及生效紧要操作 单独插件生命周期管理
    ##
    # 
    def installPlugin(self, pluginName: str) -> bool:
        """安装插件（支持检测到的插件和内置插件）"""
        if ((pluginName in self.pluginBuilders or 
             pluginName in self.builtinPluginBuilders) and 
            pluginName not in self.installedPlugins):
            # 优先从detected中获取，如果没有则从builtin中获取
            pluginClass = (self.pluginBuilders.get(pluginName) or 
                         self.builtinPluginBuilders.get(pluginName))
            try:
                plugin = self._createPluginInstance(pluginClass)
                plugin.onInstall()
                self.installedPlugins[pluginName] = plugin
                self.enablePlugin(pluginName)
                return True
            except Exception as e:
                print(f"安装插件 {pluginName} 时出错: {e}")
                return False
        return False
    
    # 
    # TODO 这里是否应该改为策略或模版模式，主要需要注入资源与依赖。
    # 
    def _createPluginInstance(self,pluginClass):
        return pluginClass()
        

    def uninstallPlugin(self, pluginName: str) -> bool:
        if pluginName in self.installedPlugins:
            plugin = self.installedPlugins[pluginName]
            self.disablePlugin(pluginName)
            plugin.onUninstall()
            del self.installedPlugins[pluginName]
            return True
        return False

    def enablePlugin(self, pluginName: str) -> bool:
        if pluginName in self.installedPlugins:
            self.installedPlugins[pluginName].enable()
            return True
        return False

    def disablePlugin(self, pluginName: str) -> bool:
        if pluginName in self.installedPlugins:
            self.installedPlugins[pluginName].disable()
            return True
        return False

    def reloadPlugin(self, pluginName: str) -> bool:
        if pluginName in self.installedPlugins:
            self.uninstallPlugin(pluginName)
            moduleName = '.'.join(pluginName.split('.')[:-1])
            if moduleName in self.modules:
                self.modules[moduleName] = importlib.reload(self.modules[moduleName])
                self._detectPluginBuildersFromModule(self.modules[moduleName], moduleName)
            return self.installPlugin(pluginName)
        return False
    
    # 批量操作
    def installAllDetectedPlugins(self) -> Dict[str, bool]:
        """尝试安装所有检测到的插件（包括内置插件），返回安装结果字典"""
        results = {}
        # 合并两个字典的键，并去重
        all_plugins = set(self.pluginBuilders.keys()) | \
                     set(self.builtinPluginBuilders.keys())
        
        for plugin_name in all_plugins:
            if not self.isPluginInstalled(plugin_name):
                results[plugin_name] = self.installPlugin(plugin_name)
        return results
    
    def uninstallAllPlugins(self) -> Dict[str, bool]:
        """卸载所有已安装的插件，返回卸载结果字典"""
        results = {}
        for plugin_name in list(self.installedPlugins.keys()):
            results[plugin_name] = self.uninstallPlugin(plugin_name)
        return results
    #
    #  实例化与安装卸载以及生效紧要操作 end
    ##

    #
    # 各类工具方法
    #
    def listPluginBuilderNames(self, pluginTypeFlag: int = 0) -> List[str]:
        """
        返回已检测到的插件名称
        Args:
            flag: 选择返回的插件类型。
                0: 返回所有插件名称
                1: 只返回普通插件名称 
                2: 只返回内置插件名称
                3: 返回普通插件和内置插件名称
        """
        if pluginTypeFlag == 1:
            return list(self.pluginBuilders.keys())
        elif pluginTypeFlag == 2:
            return list(self.builtinPluginBuilders.keys())
        elif pluginTypeFlag == 0 or pluginTypeFlag == 3:
            return list(set(self.pluginBuilders.keys()) | 
                       set(self.builtinPluginBuilders.keys()))
        else:
            return []

    def listInstalledPluginNames(self) -> List[str]:
        return list(self.installedPlugins.keys())

    # 获取内置插件列表的方法
    def listBuiltinPluginBuilderNames(self) -> List[str]:  # 
        """返回已检测到的内置插件名称列表"""
        return self.listPluginBuilderNames(pluginTypeFlag=2)

    # 检查插件是否为内置插件的方法 
    def isBuiltinPlugin(self, pluginName: str) -> bool:  # 
        """检查指定插件是否为内置插件"""
        return pluginName in self.builtinPluginBuilders

    # 获取已安装的插件实例
    def getInstalledPlugin(self, pluginName: str) -> Union[AAXWAbstractBasePlugin,None] :
        """获取指定名称的已安装插件实例"""
        return self.installedPlugins.get(pluginName) #type: ignore 
    
    # 获取已检测到的插件类/构造器
    def getPluginBuilder(
        self, 
        pluginName: str
    ) -> Union[Type[AAXWAbstractBasePlugin], Callable[[], AAXWAbstractBasePlugin], None]:
        """获取指定名称的已检测到的插件类（包括内置插件）"""
        return (self.pluginBuilders.get(pluginName) or 
                self.builtinPluginBuilders.get(pluginName))
    
    # 插件状态查询
    def isPluginInstalled(self, pluginName: str) -> bool:
        """检查插件是否已安装"""
        return pluginName in self.installedPlugins
    
    def isPluginDetected(self, pluginName: str) -> bool:
        """检查插件是否已被检测到（包括内置插件）"""
        return pluginName in self.pluginBuilders or pluginName in self.builtinPluginBuilders
    
    # 统计信息
    def getInnerCounts(self) -> Dict[str, int]:
        """获取插件相关计数信息"""
        return {
            "detectedBuilder": len(self.pluginBuilders),
            "installed": len(self.installedPlugins),
            "builtinBuilder": len(self.builtinPluginBuilders),  # 原 system
            "modules": len(self.modules)
        }
    
    # 插件信息获取
    def getPluginInfo(self, pluginName: str) -> Dict[str, Any]:
        """获取指定插件的详细信息"""
        info = {
            "name": pluginName,
            "detected": self.isPluginDetected(pluginName),
            "installed": self.isPluginInstalled(pluginName),
            "builtin": self.isBuiltinPlugin(pluginName),  # 原 system
            "builder": None,
            "instance": None,
            "module": None
        }
        
        # Check both detected and builtin plugins for builder
        if self.isPluginDetected(pluginName):
            info["builder"] = self.getPluginBuilder(pluginName)

        # Get module information
        module_name = ".".join(pluginName.split(".")[:-1])
        info["module"] = self.modules.get(module_name) or sys.modules.get(module_name)
            
        # Get instance if installed
        if self.isPluginInstalled(pluginName):
            info["instance"] = self.getInstalledPlugin(pluginName)
            
        return info

#
# 插件框架与机制 end
##

#
# Applet 小应用程序 机制。
#
class AAXWAbstractApplet(ABC):
    """
    Applet抽象基类
    定义了Applet的基本接口，提供小程序套件（applet-kit）功能的开发的基本约定。
    小程序套件，指在AAXW系列的应用中，封装专有或复合功能的组件形成用户应用能力。
    
    样例：
    Jumpin中DefaultApplet可提供：
        1. openai-llm访问；
        2. chat方式的信息界面展示； 
        3. session持久化保存；
        4. session界面展示与选择；
    
    开发新的Applet需要：
    1. 继承此抽象类并实现所有抽象方法
    2. 通过AAXWJumpinAppletManager进行注册和生命周期管理
    3. 可以访问以下注入的资源:
        - dependencyContainer: DI容器实例
        - jumpinConfig: 应用配置实例 
        - mainWindow: 主窗口实例

    生命周期方法调用顺序：
    1. onAdd(): Applet被添加到管理器时调用
    2. onActivate(): Applet被激活为当前活动Applet时调用
    3. onInactivate(): Applet不再是当前活动Applet时调用
    4. onRemove(): Applet从管理器中移除时调用
    """
    
    @abstractmethod
    def getName(self) -> str:
        """
        获取Applet的名称一般关联用，"非唯一"标志。
        对于有效控制范围内可以用于容器访问句柄，
            如，插件定义的Applet进行插件内部容器管理，这样需要插件开发者自己控制唯一性。
        """
        pass
    
    @abstractmethod
    def getTitle(self) -> str:
        """获取Applet的显示用标题
        由于可能用于按钮，建议不超过4半角字符或2个全角字符。
        """
        pass
    
    @abstractmethod
    def onAdd(self):
        """Applet加入管理时的回调
        建议实现：
            注入特定固有资源，如：容器、主界面等注入；
        """
        pass
    
    @abstractmethod
    def onRemove(self):
        """
        Applet移除时的回调
        建议实现：
            显示调用内部资源的关闭或清理方法。
            释放应用资源与状态方便解析器释放资源。
        """
        pass

    @abstractmethod
    def onActivate(self):
        """
        当Applet被切换为当前活动Applet时的回调；
        一般appletManager实现中（如：AAXWAppletManager）只有1个Applet为当前激活Applet。
        建议实现：
            使用界面控件切换到界面前台，后台资源初始化或绑定到本applet。
            完整准备用户使用状态。
            注意备份被移除的原有界面控件或后台资源，在applet被切出后恢复。
        """
        pass
    
    @abstractmethod
    def onInactivate(self):
        """
        当Applet不再是当前活动Applet时的回调。
        建议实现：
            恢复onActivate时备份的原有界面控件或后台资源。
            释放激活时才需要的临时资源；
        """
        pass


@AAXW_JUMPIN_LOG_MGR.classLogger()
class AAXWAppletManager:
    """
    Applet管理器
    负责Applet的添加、移除和生命周期管理
    """
    AAXW_CLASS_LOGGER:logging.Logger
    DEFAULT_MAX_CAPACITY = 10  # 默认最大容量

    def __init__(self, maxCapacity: int = DEFAULT_MAX_CAPACITY):
        self.applets: List[AAXWAbstractApplet] = []
        self.activatedAppletIndex: int = -1  # 当前激活的Applet索引
        self.maxCapacity = maxCapacity #容量阈值

    def activateApplet(self, index: int) -> bool:
        """
        激活指定索引的Applet
        :param index: Applet在列表中的索引
        :return: 激活是否成功
        """
        if not (0 <= index < len(self.applets)):
            self.AAXW_CLASS_LOGGER.warning(f"Invalid applet index: {index}")
            return False

        try:
            # 如果有已激活的Applet，先通知它将被切出
            if self.activatedAppletIndex != -1 and self.activatedAppletIndex < len(self.applets):
                activated_applet = self.applets[self.activatedAppletIndex]
                activated_applet.onInactivate()

            # 激活新的Applet
            new_applet = self.applets[index]
            new_applet.onActivate()
            
            self.activatedAppletIndex = index
            self.AAXW_CLASS_LOGGER.info(
                f"Activated applet [{index}]: {new_applet.getName()} ({new_applet.getTitle()})")
            return True
            
        except Exception as e:
            self.AAXW_CLASS_LOGGER.error(f"Failed to activate applet at index {index}: {str(e)}")
            return False

    def getActivatedApplet(self) -> Tuple[int, Union[AAXWAbstractApplet, None]]:
        """
        获取当前激活的Applet
        :return: (激活的Applet索引, Applet实例) 如果没有激活的Applet则返回(-1, None)
        """
        if self.activatedAppletIndex == -1 or self.activatedAppletIndex >= len(self.applets):
            return (-1, None)
        return (self.activatedAppletIndex, self.applets[self.activatedAppletIndex])

    def getAppletByIndex(self, index: int) -> Union[AAXWAbstractApplet, None]:
        """
        通过索引获取Applet实例
        :param index: Applet在列表中的索引
        :return: Applet实例或None
        """
        if 0 <= index < len(self.applets):
            return self.applets[index]
        return None

    
    def addApplet(self, applet: AAXWAbstractApplet, index: int = -1) -> bool:
        """
        添加Applet
        :param applet: Applet实例
        :param index: 插入位置，-1表示追加到末尾
        :return: 添加是否成功
        """
        if len(self.applets) >= self.maxCapacity:
            self.AAXW_CLASS_LOGGER.error(f"Cannot add applet: maximum capacity ({self.maxCapacity}) reached")
            return False

        try:
            applet.onAdd()
            
            if index == -1:
                self.applets.append(applet)
            else:
                if not (0 <= index <= len(self.applets)):
                    raise ValueError(f"Invalid index: {index}")
                self.applets.insert(index, applet)
                # 如果插入位置在已激活的Applet之前，需要更新activatedAppletIndex
                if self.activatedAppletIndex != -1 and index <= self.activatedAppletIndex:
                    self.activatedAppletIndex += 1
                
            self.AAXW_CLASS_LOGGER.info(f"Successfully added applet: {applet.getName()}")
            return True
        except Exception as e:
            self.AAXW_CLASS_LOGGER.error(f"Failed to add applet {applet.getName()}: {str(e)}")
            
            self.AAXW_CLASS_LOGGER.error(
                f"Failed to add applet {applet.getName()}: {str(e)}\n{traceback.format_exc()}")
            return False

    
    def removeApplet(self, index: int) -> bool:
        """
        移除指定索引的Applet
        :param index: Applet在列表中的索引
        :return: 移除是否成功
        """
        if not (0 <= index < len(self.applets)):
            return False

        try:
            applet = self.applets[index]
            
            # 如果要移除的是当前激活的Applet，先将其切换为非激活状态
            if index == self.activatedAppletIndex:
                applet.onInactivate()
                self.activatedAppletIndex = -1
            # 如果移除的Applet在已激活的Applet之前，需要更新activatedAppletIndex
            elif index < self.activatedAppletIndex:
                self.activatedAppletIndex -= 1
                
            applet.onRemove()
            self.applets.pop(index)
            
            self.AAXW_CLASS_LOGGER.info(f"Successfully removed applet at index {index}: {applet.getName()}")
            return True
        except Exception as e:
            self.AAXW_CLASS_LOGGER.error(f"Failed to remove applet at index {index}: {str(e)}")
            return False

    def getApplet(self, name: str) -> List[AAXWAbstractApplet]:
        """获取指定名称的所有Applet实例"""
        return [applet for applet in self.applets if applet.getName() == name]

    def listAppletsNamesAndTitles(self) -> List[Tuple[str, str]]:
        """返回所有已安装的Applet的名称和标题列表，按安装顺序排序
        Returns:
            List[Tuple[str, str]]: 返回元组列表，每个元组包含:
                - [0] str: Applet的名称name，
                - [1] str: Applet的标题title（一般展示用）
                - 数组下标: 对应applet所在所在下标；
        """
        return [(applet.getName(), applet.getTitle()) for applet in self.applets]

# 小程序机制 end
##


##
# 应用级别框架扩展
##
#

            


#
#
@AAXWJumpinDICUtilz.register(key="jumpinPluginManager",
        dependencyContainer="_nativeDependencyContainer", #这里是内联 aware方式没有用singleton方式
        jumpinConfig="jumpinConfig",
        jumpinAppletManager="jumpinAppletManager",
        mainWindow="mainWindow")
# @AAXW_JUMPIN_LOG_MGR.classLogger()
class AAXWJumpinPluginManager(AAXWFileSourcePluginManager):
    @override
    def __init__(self):
        super().__init__()
        self.dependencyContainer:Union[AAXWDependencyContainer,None]=None 
        self.jumpinConfig:Union['AAXWJumpinConfig',None]=None
        self.mainWindow:Union['AAXWJumpinMainWindow',None]=None
        self.jumpinAppletManager:Union[AAXWJumpinAppletManager,None]=None

    @override
    def _createPluginInstance(self, pluginClass):
        inst=pluginClass()
        # 注入依赖容器
        setattr(inst, 'dependencyContainer', self.dependencyContainer)
        setattr(inst, 'jumpinConfig', self.jumpinConfig)
        setattr(inst, 'mainWindow', self.mainWindow)
        setattr(inst, 'jumpinAppletManager', self.jumpinAppletManager)

        return inst
    pass

    # 可以过率builder的类型 
    @override
    def _putPluginBuilder(self, pluginKey: str, builder, isBuiltin: bool):
        return super()._putPluginBuilder(pluginKey, builder, isBuiltin)

# 
# 
##

# 基本config信息，与默认配置；
# 添加LLM提供商配置的DTO类
class OpenAIProvider(BaseModel):
    """OpenAI提供商配置DTO"""
    apiKey: str = ""
    baseUrl: str = ""
    # modelName: str = "gpt-4o-mini"
    defaultModelName:str="gpt-4o-mini"

    def candidateModels(self):
        return [
            "gpt-4o-mini",
            "gpt-4o",
            "gpt-3.5-turbo",
        ]
    
class OllamaProvider(BaseModel):
    """Ollama提供商配置DTO"""
    serviceUrl: str = "http://localhost:11434/v1"
    # modelName: str = "llama3"
    defaultModelName:str="qwen2.5:1.5b"
    def candidateModels(self):
        return [
            "llama3.2",
            "qwen2.5:1.5b",
            "llama3.1:8b",
        ]

# 基本config信息，与默认配置；
@AAXWJumpinDICUtilz.register(key="jumpinConfig") 
@AAXW_JUMPIN_LOG_MGR.classLogger(level=logging.DEBUG)
class AAXWJumpinConfig:
    AAXW_CLASS_LOGGER:logging.Logger

    # 默认配置
    FAMILY_NAME = "AAXW"  # 之后可用来拆分抽象
    APP_NAME_DEFAULT = "AAXW_Jumpin"
    APP_VERSION_DEFAULT = __version__
    DEBUG_DEFAULT = False  # 暂时没用到
    LOG_LEVEL_DEFAULT = "INFO"
    APP_WORK_DIR_DEFAULT = "./"
    APP_CONFIG_FILENAME_DEFAULT = "aaxw_jumpin_config.yaml"

    # LLM配置默认值
    DEFAULT_LLM_PROVIDER = "openai"  # 默认LLM提供商
    DEFAULT_LLM_MODEL = "gpt-4o-mini"  # 默认LLM模型
    
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
    QTextBrowser[contentOwnerType="ROW_CONTENT_OWNER_TYPE_OTHERS"] {
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
        # 初始化基本属性
        self.appName = self.APP_NAME_DEFAULT
        self.appVersion = self.APP_VERSION_DEFAULT
        
        self.debug = self.DEBUG_DEFAULT
        self.logLevel = self.LOG_LEVEL_DEFAULT
        self.appWorkDir = self.APP_WORK_DIR_DEFAULT
        self.appConfigFilename = self.APP_CONFIG_FILENAME_DEFAULT
        
        # 初始化LLM配置属性 - 修改属性名
        self.llmProvider = self.DEFAULT_LLM_PROVIDER
        self.llmModel = self.DEFAULT_LLM_MODEL
        
        # 使用DTO类初始化配置
        self.openaiProvider = OpenAIProvider()
        self.ollamaProvider = OllamaProvider()

        ## env 环境变量中读取保存的LLM配置，在yaml配置文件中没有时使用。
        self.envOpenAIApiKey=""
        self.envOpenAIBaseUrl=""    

        # 默认顺序初始化
        self.loadEnv()
        self.loadArgs()
        self.loadYaml()
        self.AAXW_CLASS_LOGGER.info(f"All config loaded，new base-config: "
                    f"appWorkDir={self.appWorkDir}, "
                    f"logLevel={self.logLevel}, "
                    f"appConfigFilename={self.appConfigFilename}, "
                    f"debug={self.debug}")
        # 记录LLM配置
        self.logLLMConfig()
        
        # 暂时初始化时调用
        self.initAANode()

    def loadEnv(self):
        """从环境变量加载配置"""
        self.appWorkDir = os.environ.get('AAXW_APPWORKDIR', self.appWorkDir)
        self.logLevel = os.environ.get('AAXW_LOG_LEVEL', self.logLevel)
        self.appConfigFilename = os.environ.get('AAXW_CONFIG_FILE_NAME', self.appConfigFilename)
        self.debug = os.environ.get('AAXW_DEBUG', self.debug)

        # 从环境变量读取LLM配置
        self.envOpenAIApiKey = os.environ.get('OPENAI_API_KEY', self.envOpenAIApiKey)
        self.envOpenAIBaseUrl = os.environ.get('OPENAI_BASE_URL', self.envOpenAIBaseUrl)

    def loadArgs(self):
        """从命令行参数加载配置"""
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

    def loadYaml(self, yamlPath=None):
        """从YAML配置文件加载配置"""
        yaml_path = yamlPath or os.path.join(self.appWorkDir, self.appConfigFilename)
        if os.path.exists(yaml_path):
            with open(yaml_path, 'r', encoding='utf-8') as file:
                try:
                    yaml_config = yaml.safe_load(file)
                    if yaml_config:
                        # 更新基础配置
                        for key, value in yaml_config.items():
                            if key != 'openaiProvider' and key != 'ollamaProvider':
                                if hasattr(self, key):
                                    setattr(self, key, value)
                        
                        # 更新Provider配置，移除兼容旧版本的代码
                        if 'openaiProvider' in yaml_config and isinstance(yaml_config['openaiProvider'], dict):
                            for key, value in yaml_config['openaiProvider'].items():
                                if hasattr(self.openaiProvider, key):
                                    setattr(self.openaiProvider, key, value)
                        
                        # 检查openaiProvider的字段，如果为空则使用环境变量
                        if hasattr(self.openaiProvider, 'apiKey') and (not self.openaiProvider.apiKey or self.openaiProvider.apiKey.strip() == ''):
                            if self.envOpenAIApiKey:
                                self.openaiProvider.apiKey = self.envOpenAIApiKey
                                self.AAXW_CLASS_LOGGER.info("Using OPENAI_API_KEY from environment variable")
                        
                        if hasattr(self.openaiProvider, 'baseUrl') and (not self.openaiProvider.baseUrl or self.openaiProvider.baseUrl.strip() == ''):
                            if self.envOpenAIBaseUrl:
                                self.openaiProvider.baseUrl = self.envOpenAIBaseUrl
                                self.AAXW_CLASS_LOGGER.info("Using OPENAI_API_BASE from environment variable")
                        
                        if 'ollamaProvider' in yaml_config and isinstance(yaml_config['ollamaProvider'], dict):
                            for key, value in yaml_config['ollamaProvider'].items():
                                if hasattr(self.ollamaProvider, key):
                                    setattr(self.ollamaProvider, key, value)
                    
                    self.AAXW_CLASS_LOGGER.info(f"Yaml config file loaded: {yaml_path}")
                except yaml.YAMLError as e:
                    self.AAXW_CLASS_LOGGER.warning(f"Error reading YAML file: {e}")
        else:
            self.AAXW_CLASS_LOGGER.warning(f"YAML config file not found: {yaml_path}")

    def saveConfigToYaml(self, yamlPath=None):
        """保存配置到YAML文件"""
        yaml_path = yamlPath or os.path.join(self.appWorkDir, self.appConfigFilename)
        
        # 构建配置字典
        config_dict = {}
        
        # 添加基础属性，排除特定属性
        excluded_keys = [
            'AAXW_CLASS_LOGGER', 'openaiProvider', 'ollamaProvider',
            'envOpenAIApiKey', 'envOpenAIBaseUrl'
        ]
        
        for key, value in self.__dict__.items():
            if not key.startswith('_') and key not in excluded_keys:
                config_dict[key] = value
        
        # 添加Provider配置
        config_dict['openaiProvider'] = self.openaiProvider.model_dump()
        config_dict['ollamaProvider'] = self.ollamaProvider.model_dump()
        
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(os.path.abspath(yaml_path)), exist_ok=True)
            
            # 写入YAML文件
            with open(yaml_path, 'w', encoding='utf-8') as file:
                yaml.safe_dump(config_dict, file, default_flow_style=False, allow_unicode=True)
            
            self.AAXW_CLASS_LOGGER.info(f"配置已保存到: {yaml_path}")
            return True
        except Exception as e:
            self.AAXW_CLASS_LOGGER.error(f"保存配置失败: {str(e)}")
            return False

    def setWorkCfgAndloadYaml(self, workdir=None, configName=None):
        """设置工作目录和配置文件名，并加载配置"""
        if workdir: self.appWorkDir = workdir
        if configName: self.appConfigFilename = configName
        self.loadYaml()

    def logLLMConfig(self):
        """记录当前LLM配置"""
        self.AAXW_CLASS_LOGGER.debug(f"当前LLM配置: 提供商={self.llmProvider}, 模型={self.llmModel}")
        
        # 记录OpenAI配置
        self.AAXW_CLASS_LOGGER.debug(f"OpenAI配置: API基础URL={self.openaiProvider.baseUrl}")
        
        # 记录Ollama配置
        self.AAXW_CLASS_LOGGER.debug(f"Ollama配置: 服务URL={self.ollamaProvider.serviceUrl}")

    def updateLLMConfig(self, provider=None, openaiConfig=None, ollamaConfig=None, llmModel=None):
        """更新LLM配置并保存到YAML"""
        changed = False
        
        if provider and provider in ['openai', 'ollama']:
            self.llmProvider = provider
            changed = True
        
        if llmModel:
            self.llmModel = llmModel
            changed = True
            
        if openaiConfig:
            for key, value in openaiConfig.items():
                if hasattr(self.openaiProvider, key):
                    setattr(self.openaiProvider, key, value)
                    changed = True
                
        if ollamaConfig:
            for key, value in ollamaConfig.items():
                if hasattr(self.ollamaProvider, key):
                    setattr(self.ollamaProvider, key, value)
                    changed = True
        
        if changed:
            self.saveConfigToYaml()
            self.logLLMConfig()
        
        return changed

    def reloadConfig(self):
        """重新加载配置"""
        self.loadYaml()
        self.logLLMConfig()

    def initAANode(self): #init after di；当前先在自己内部执行；
        #这里日志器进程全局的，所以其实__init__初始化时就能调用；
        AAXW_JUMPIN_LOG_MGR.setLogDirAndFile(logDir=self.appWorkDir,filename="aaxw_app.log")

        #其他di胡执行的工作；
        pass

    def getActiveProviderConfig(self):
        """获取当前激活的提供商配置"""
        if self.llmProvider == "openai":
            return self.openaiProvider
        elif self.llmProvider == "ollama":
            return self.ollamaProvider
        else:
            return None

#
# AI相关
#
class AAXWAbstractAIConnOrAgent(ABC):

    # TODO 之后考虑增加回调实例/类来增回调时机处理。 或者1个实现enter exit的with处理类。
    # class AbsCallback(ABC):
    #     def onStart(self,input):...
    #     def onResponse(self,str):...
    #     def onFinish(self,wholeResponse):...
    #     def onException(self,e):...

        
    @abstractmethod
    def requestAndCallback(self, 
            prompt: str, func: Callable[[str], None],isStream: bool = True
        ):
        # raise NotImplementedError("Subclasses must implement sendRequestStream method")
        ...

    def embedding(self, prompt:str):
        ...

    def edit(self, prompt:str, instruction:str):
        ...


@AAXWJumpinDICUtilz.register(key="simpleAIConnOrAgent")
@AAXW_JUMPIN_LOG_MGR.classLogger(level=logging.DEBUG) #
class AAXWSimpleAIConnOrAgent(AAXWAbstractAIConnOrAgent):
    """
    简单实现的连接LLM/Agent的类，支持流式获取响应。
    使用Langchain封装的OpenAI的接口实现。
    """
    AAXW_CLASS_LOGGER:logging.Logger

    SYSTME_PROMPT_TEMPLE="""
    你的名字是ANAN是一个AI入口助理;
    请关注用户跟你说的内容，和善的回答用户，与用户要求。
    如果用户说的不明确，请提示用户可以说的更明确。
    """

    USER_PROMPT_TEMPLE="""
    以下是用户说的内容：
    {message}
    """
    
    def __init__(self, api_key:str =None, base_url:str=None, model_name: str = "gpt-4o-mini"): # type: ignore
        """
        初始化OpenAI连接代理。
        
        :param api_key: OpenAI API密钥。
        :param base_url: OpenAI API基础URL。
        :param model_name: 使用的模型名称。
        """
        # 从环境变量读取API密钥和URL
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        self.base_url = base_url or os.getenv('OPENAI_BASE_URL')
        self.model_name = model_name or os.getenv('OPENAI_MODEL_NAME', 'gpt-4o-mini')
        
        # 调用updateConfig方法来初始化所有配置
        self.updateConfig(
            apiKey=self.api_key, baseUrl= self.base_url, modelName= self.model_name) # type: ignore
    
    def updateConfig(
            self, apiKey: str = None, baseUrl: str = None, modelName: str = None): # type: ignore
        """
        更新OpenAI连接配置。
        
        :param api_key: 新的OpenAI API密钥。
        :param base_url: 新的OpenAI API基础URL。
        :param model_name: 新的模型名称。
        :param isInit: 是否是初始化调用。
        """
    
        # 更新模式：只更新非None的参数
        if apiKey is not None:
            self.api_key = apiKey
        
        if baseUrl is not None:
            self.base_url = baseUrl
            
        if modelName is not None:
            self.model_name = modelName
            
        # 构建LLM参数
        chat_params = {
            "temperature": 0,
            "model": self.model_name,
            "api_key": self.api_key,
        }
        
        if self.base_url:
            chat_params["base_url"] = self.base_url
            
        # 初始化或更新LLM实例
        self.llm = ChatOpenAI(**chat_params)
        
        # 仅在非初始化时记录日志
        self.AAXW_CLASS_LOGGER.info(f"OpenAI连接配置已更新，模型: {self.model_name}")
    
    @override
    def requestAndCallback(self, 
            prompt: str, 
            func: Callable[[str], None], 
            isStream: bool = True
        ):
        """
        发送请求到LLM，并通过回调函数处理流式返回的数据。
        
        :param prompt: 提供给LLM的提示文本。
        :param func: 用于处理每次接收到的部分响应的回调函数。
        :param isStream: 是否使用流式响应。
        """
        
        system_message = SystemMessage(content=self.SYSTME_PROMPT_TEMPLE)
        human_message = HumanMessage(content=self.USER_PROMPT_TEMPLE.format(message=prompt))
        messages = [system_message, human_message]

        self.AAXW_CLASS_LOGGER.debug(f"使用model_name:{self.model_name}, base_url:{self.base_url}; "
            f"以及最终 prompt-messages: {messages}")
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
            api_key=self.api_key,
            base_url=self.base_url,
            model=model
        )
        return embeddings.embed_query(prompt)
    
    def edit(self, prompt: str, instruction: str):
        """
        根据指令编辑文本。
        
        :param prompt: 原始文本。
        :param instruction: 编辑指令。
        :return: 编辑后的文本。
        """
        # 目前OpenAI不再提供专门的edit API，使用聊天完成API模拟
        system_content = f"你是一个文本编辑助手。请按照以下指令编辑提供的文本：\n{instruction}"
        system_message = SystemMessage(content=system_content)
        human_message = HumanMessage(content=prompt)
        messages = [system_message, human_message]
        
        response = self.llm.invoke(messages)
        return response.content


@AAXWJumpinDICUtilz.register(key="ollamaAIConnOrAgent")
@AAXW_JUMPIN_LOG_MGR.classLogger(level=logging.DEBUG)
class AAXWOllamaAIConnOrAgent(AAXWAbstractAIConnOrAgent):
    """
    直接使用OpenAI的接口实现。对Ollama的访问；
    """
    AAXW_CLASS_LOGGER:logging.Logger

    SYSTEM_PROMPT_DEFAULT="""
    你的名字是ANAN-Ollama是一个AI入口助理;
    请关注用户跟你说的内容，和善的回答用户，与用户要求。
    如果用户说的不明确，请提示用户可以说的更明确。
    如果没有特别说明，可考虑用markdown格式输出一般内容。
    """

    USER_PROMPT_TEMPLE="""
    以下是用户说的内容：
    {message}
    """
    
    def __init__(self, modelName: str = ""): #llama3.2:3b qwen2:1.5b qwen2.5:7b
        # 设置默认的 API URL
        self.base_url = "http://localhost:11434/v1"
        self.modelName= modelName or os.getenv("OPENAI_MODEL_NAME", "")
        self.updateConfig(baseUrl= self.base_url, modelName=self.modelName)
    
    def updateConfig(
            self, apiKey: str = "ollama", baseUrl: str = None, modelName: str = None): # type: ignore
        # 设置默认的 API URLbaseUrl
        self.base_url = baseUrl
        self.modelName= modelName

        # 
        # 如果仍为空，从可用模型中选择一个
        try:
            self.client = OpenAI(
                base_url=self.base_url,
                api_key=apiKey,
            )

            if not self.modelName:
                modelName = self._selectPreferredModel()
                
            self.modelName = modelName
            self.AAXW_CLASS_LOGGER.info(f"Selected model: {self.modelName}")

            models = self.listModels()
            self.AAXW_CLASS_LOGGER.info(f"Available Ollama models found: {', '.join(models)}")
        except Exception as e:
            self.AAXW_CLASS_LOGGER.error(
                f"Error initializing Ollama model: {str(e)};Ollama访问模块功能可能不可用或需要至少下载1个模型")
        pass
    
    def _selectPreferredModel(self) -> str:
        """从可用模型中选择首选模型"""
        preferred_models = ["qwen2.5:1.5b","qwen2.5:3b", "llama3.2:3b"]
        available_models = self.listModels()
        
        # 按优先级检查首选模型
        for model in preferred_models:
            if model in available_models:
                return model
                
        # 如果没有首选模型，选择模型大小最小的
        if available_models:
            # 提取模型大小并排序
            def get_model_size(model_name):
                try:
                    # 检查是否包含冒号
                    if ':' not in model_name:
                        return float('inf')
                    
                    # 获取冒号后的部分
                    size_part = model_name.split(':')[1]
                    
                    # 检查是否以'b'结尾且前面是数字
                    if not size_part.endswith('b'):
                        return float('inf')
                        
                    # 去掉'b'并尝试转换为数字
                    size_str = size_part[:-1]
                    try:
                        return float(size_str)
                    except ValueError:
                        return float('inf')
                        
                except:
                    return float('inf')  # 任何解析错误返回无穷大
            
            return min(available_models, key=get_model_size)
            
        raise Exception("No available models found")
        

    def listModels(self) -> List[str]:
        """列出可用的Ollama模型"""
        try:
            models = self.client.models.list()
            return [model.id for model in models.data]
        except Exception as e:
            raise Exception(f"Failed to list models: {str(e)}")


    @override
    def downloadModel(self, model_name: str, callback:Callable[[str, Dict[str, Any]], None], insecure: bool = False):
        """
        下载 Ollama 模型
        
        Args:
            model_name (str): 模型名称
            callback (callable): 下载状态回调函数，
                    下载过程中情况的变化可以由回调函数获取并处理，
                    接收状态信息字符串和状态数据字典
                    callback(status_msg: str, status_data: Dict[str, Any])
            insecure (bool): 是否允许不安全下载
        
        Returns:
            bool: 下载是否成功
        """
        if not model_name:
            return False

        try:
            # 构建请求
            req = urllib.request.Request(
                urllib.parse.urljoin(self.base_url, "/api/pull"),
                data=json.dumps({
                    "name": model_name,
                    "insecure": insecure,
                    "stream": True
                }).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            self.AAXW_CLASS_LOGGER.info(
                f"Sending request to {req.full_url}, method={req.method}, headers={req.headers}"
            )

            with urllib.request.urlopen(req) as response:
                for line in response:
                    data = json.loads(line.decode("utf-8"))
                    
                    # 构建状态数据字典
                    status_data = {
                        "total": data.get("total"),
                        "completed": data.get("completed", 0),
                        "status": data.get("status"),
                        "error": data.get("error"),
                        "digest": data.get("digest"),
                        "model": model_name
                    }
                    
                    # 构建状态消息
                    status_msg = data.get("error") or data.get("status") or "No response"
                    if "status" in data and status_data["total"]:
                        status_msg += f" [{status_data['completed']}/{status_data['total']}]"
                    
                    # 调用回调函数，传递消息和数据
                    callback(status_msg, status_data)

            self.AAXW_CLASS_LOGGER.info(f"Successfully downloaded model: {model_name}")
            return True

        except Exception as e:
            error_msg = f"Failed to download model {model_name}: {str(e)}"
            error_data = {
                "error": str(e),
                "model": model_name,
                "status": "error"
            }
            self.AAXW_CLASS_LOGGER.error(error_msg)
            callback(error_msg, error_data)
            return False
    

    @override
    def requestAndCallback(self, 
            prompt: str, 
            func: Callable[[str], None],
            isStream: bool = True
        ):
        """使用OpenAI API风格生成流式聊天完成"""
        formatted_prompt = self.USER_PROMPT_TEMPLE.format(message=prompt)
        messages = [
            ChatCompletionSystemMessageParam(content=self.SYSTEM_PROMPT_DEFAULT, role="system"),
            ChatCompletionUserMessageParam(content=formatted_prompt, role="user")
        ]
        try:
            self.AAXW_CLASS_LOGGER.debug(
                f"使用model_name:{self.modelName}, base_url:{self.base_url}; "
                f"最终prompt-messages: {messages}")
            stream = self.client.chat.completions.create(
                model=self.modelName,  #type:ignore
                messages=messages,
                stream=True
            )  #type:ignore

            for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    content = chunk.choices[0].delta.content
                    func(content)
        except Exception as e:
            raise Exception(f"Failed to generate stream chat completion: {str(e)}")

@AAXWJumpinDICUtilz.register(
    key="configurableAIConnOrAgent", 
    jumpinConfig="jumpinConfig",
    dependencyContainer="_nativeDependencyContainer"  # 添加 DI 容器注入
)
@AAXW_JUMPIN_LOG_MGR.classLogger(level=logging.DEBUG)
class ConfigurableAIConnOrAgent(AAXWAbstractAIConnOrAgent):
    """
    可配置的AI连接器代理类。
    根据jumpinConfig配置动态选择使用Ollama或标准OpenAI连接器。
    支持通过依赖注入获取内部实例。
    """
    AAXW_CLASS_LOGGER: logging.Logger
    
    def __init__(self):
        """初始化配置型AI连接器代理"""
        self.jumpinConfig: AAXWJumpinConfig = None  # type:ignore
        self.innerInstance = None
        self.dependencyContainer: AAXWDependencyContainer = None  # type:ignore
        
    def initConfig(self, jumpinConfig):
        """
        根据传入的配置初始化内部实例
        
        Args:
            jumpinConfig: 包含AI连接器配置的对象
        """
        self.jumpinConfig = jumpinConfig
        self._initializeInnerInstance()
        
    def _initializeInnerInstance(self):
        """初始化内部AI连接器实例，根据配置选择合适的实现"""
        # 获取活跃的 LLM 提供商和模型
        llmProvider = self.jumpinConfig.llmProvider
        llmModelName = self.jumpinConfig.llmModel
        
        self.AAXW_CLASS_LOGGER.info(f"初始化LLM连接器，提供商: {llmProvider}, 模型: {llmModelName}")
        
        if llmProvider == "ollama":
            # 从DI容器获取Ollama连接器
            self.AAXW_CLASS_LOGGER.info("使用Ollama连接器")
            self.innerInstance = self.dependencyContainer.getAANode("ollamaAIConnOrAgent")
            
            # 根据类型直接更新Ollama配置
            if isinstance(self.innerInstance, AAXWOllamaAIConnOrAgent):
                ollamaConfig = self.jumpinConfig.getActiveProviderConfig()
                if ollamaConfig and isinstance(ollamaConfig, OllamaProvider):
                    try:
                        serviceUrl = ollamaConfig.serviceUrl
                        self.innerInstance.updateConfig(
                            baseUrl=serviceUrl,
                            modelName=llmModelName
                        )
                        self.AAXW_CLASS_LOGGER.info(f"已更新Ollama配置，服务URL: {serviceUrl}, 模型: {llmModelName}")
                    except Exception as e:
                        self.AAXW_CLASS_LOGGER.error(f"更新Ollama配置失败: {str(e)}")
        else:
            # 从DI容器获取OpenAI连接器
            self.AAXW_CLASS_LOGGER.info("使用OpenAI连接器")
            self.innerInstance = self.dependencyContainer.getAANode("simpleAIConnOrAgent")
            
            # 根据类型直接更新OpenAI配置
            if isinstance(self.innerInstance, AAXWSimpleAIConnOrAgent):
                openaiConfig = self.jumpinConfig.getActiveProviderConfig()
                if openaiConfig and isinstance(openaiConfig, OpenAIProvider):
                    try:
                        self.innerInstance.updateConfig(
                            apiKey=openaiConfig.apiKey,
                            baseUrl=openaiConfig.baseUrl,
                            modelName=llmModelName
                        )
                        self.AAXW_CLASS_LOGGER.info(f"已更新OpenAI配置，模型: {llmModelName}")
                    except Exception as e:
                        self.AAXW_CLASS_LOGGER.error(f"更新OpenAI配置失败: {str(e)}")
    
    @override
    def requestAndCallback(self, prompt: str, func: Callable[[str], None], isStream: bool = True):
        """
        向LLM发送请求并通过回调处理响应
        
        Args:
            prompt: 输入提示词
            func: 回调函数，用于处理返回的响应文本
            isStream: 是否使用流式响应
        """
        # 确保内部实例已初始化
        if not self.innerInstance:
            self._initializeInnerInstance()
            
        # 如果内部实例仍然为空，抛出异常
        if not self.innerInstance:
            errorMsg = "未能初始化AI连接器，请检查配置"
            self.AAXW_CLASS_LOGGER.error(errorMsg)
            raise RuntimeError(errorMsg)
            
        # 委托给内部实例处理请求
        try:
            self.innerInstance.requestAndCallback(prompt, func, isStream)
        except Exception as e:
            self.AAXW_CLASS_LOGGER.error(f"AI请求失败及堆栈 {str(e)}\n{ traceback.format_exc()}")
            # 向UI回调发送错误信息
            func(f"\n\n[错误] AI请求失败: {str(e)}")
    
    @override
    def embedding(self, prompt: str):
        """
        获取文本的embedding向量
        
        Args:
            prompt: 输入文本
            
        Returns:
            文本的embedding向量
        """
        # 确保内部实例已初始化
        if not self.innerInstance:
            self._initializeInnerInstance()
            
        # 如果内部实例仍然为空，抛出异常
        if not self.innerInstance:
            errorMsg = "未能初始化AI连接器，请检查配置"
            self.AAXW_CLASS_LOGGER.error(errorMsg)
            raise RuntimeError(errorMsg)
            
        # 委托给内部实例处理embedding请求
        try:
            return self.innerInstance.embedding(prompt)
        except Exception as e:
            self.AAXW_CLASS_LOGGER.error(f"获取embedding失败: {str(e)}")
            raise RuntimeError(f"获取embedding失败: {str(e)}")
    
    @override
    def edit(self, prompt: str, instruction: str):
        """
        获取LLM的文本编辑结果
        
        Args:
            prompt: 原始文本
            instruction: 编辑指令
            
        Returns:
            编辑后的文本
        """
        # 确保内部实例已初始化
        if not self.innerInstance:
            self._initializeInnerInstance()
            
        # 如果内部实例仍然为空，抛出异常
        if not self.innerInstance:
            errorMsg = "未能初始化AI连接器，请检查配置"
            self.AAXW_CLASS_LOGGER.error(errorMsg)
            raise RuntimeError(errorMsg)
            
        # 委托给内部实例处理编辑请求
        try:
            return self.innerInstance.edit(prompt, instruction)
        except Exception as e:
            self.AAXW_CLASS_LOGGER.error(f"文本编辑失败: {str(e)}")
            raise RuntimeError(f"文本编辑失败: {str(e)}")


##
# 支持互动历史与记忆持久化管理器，
# chat history /memory persistence
##

#列出指定目录对话历史（或记录）列表；
#载入项的历史记录，成为Memory/session或可进行互动操作的访问-操作器；（内部挂用LLMconn-或外层 agent进行互动操作。）
#新建一个互动Session；
@AAXW_JUMPIN_LOG_MGR.classLogger()
class AAXWJumpinHistoriedMemory:
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
            self.AAXW_CLASS_LOGGER.debug(f"加载的消息: {messages}")
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

@AAXWJumpinDICUtilz.register(
    key="jumpinAIMemoryManager",
    jumpinConfig="jumpinConfig"
)
@AAXW_JUMPIN_LOG_MGR.classLogger()
class AAXWJumpinFileAIMemoryManager:
    """管理多个AI(LLM) 交互或记忆功能及其持久化的管理器"""
    AAXW_CLASS_LOGGER: logging.Logger

    def __init__(self):
        # 移除config参数,改为DI注入
        # self.dependencyContainer: Union[AAXWDependencyContainer,None] = None
        self.jumpinConfig: Union[AAXWJumpinConfig,None] = None
        
        self.storeDirName = "memories"
        # 使用注入的config
        self.memoriesStoreDir:str = None # 初始化为None,等config注入后再设置 #type:ignore

    def initRes(self):
        """初始化存储目录"""
        # 设置存储目录路径
        if self.jumpinConfig:
            self.memoriesStoreDir = os.path.join(self.jumpinConfig.appWorkDir, self.storeDirName)
            
        self.AAXW_CLASS_LOGGER.info(f"检测到的记忆存储目录: {self.memoriesStoreDir}")
        if not os.path.exists(self.memoriesStoreDir):
            os.makedirs(self.memoriesStoreDir)

    def listMemoryNames(self, 
        offset: int = 0, 
        limit: int = 5,
        sortByModified: bool = True,
        ascending: bool = False
    ) -> List[str]:
        """列出聊天历史的ID，支持分页和排序
    
        Args:
            offset: 起始位置，默认0表示从头开始
            limit: 返回数量限制，默认5条, 为-1表示返回全部
            sortByModified: 是否按修改时间排序，默认True
            ascending: 排序方向，默认False表示降序(新的在前)
    
        Returns:
            List[str]: 聊天历史ID列表
        """
        # 获取所有历史文件
        history_files = [f for f in os.listdir(self.memoriesStoreDir) 
                        if f.endswith('_history.json')]
        
        total_count = len(history_files)
        
        # 边界检查
        if offset < 0:
            offset = 0
        if offset >= total_count:
            return []  # 如果偏移量超过总数,返回空列表
        
        if sortByModified:
            # 获取文件修改时间并排序
            history_files.sort(
                key=lambda x: os.path.getmtime(os.path.join(self.memoriesStoreDir, x)),
                reverse=not ascending
            )
        
        # 处理分页
        if limit > 0:
            # 确保不会超出实际可用数量
            available_count = total_count - offset
            actual_limit = min(limit, available_count)
            history_files = history_files[offset:offset + actual_limit]
        elif offset > 0:
            history_files = history_files[offset:]
            
        # 移除文件扩展名返回ID列表
        return [f[:-len('_history.json')] for f in history_files]
    
    def getMemoriesCount(self) -> int:
        """获取聊天历史总数"""
        return len([f for f in os.listdir(self.memoriesStoreDir) 
                if f.endswith('_history.json')])

    def loadOrCreateMemory(self, chat_id: str = None) -> AAXWJumpinHistoriedMemory: #type:ignore
        """加载指定聊天历史"""
        chId=chat_id if chat_id else self._newName() 
            
        chat_history_path = os.path.join(self.memoriesStoreDir, f"{chId}_history.json")
        print(f"准备加载或创建 {chId} 对应文件。")
        return AAXWJumpinHistoriedMemory(chId, self.memoriesStoreDir)


    def deleteMemory(self, chat_id: str):
       """删除指定的记忆"""
       history_path = os.path.join(self.memoriesStoreDir, f"{chat_id}_history.json")
       if os.path.exists(history_path) and os.path.isfile(history_path):
           os.remove(history_path)

    def renameMemory(self, old_id: str, new_id: str) -> bool:
        """重命名记忆
        
        Args:
            old_id: 原记忆ID
            new_id: 新记忆ID
            
        Returns:
            bool: 重命名是否成功
        """
        # old_path = os.path.join(self.memoriesStoreDir, f"{old_id}_history.json")
        # new_path = os.path.join(self.memoriesStoreDir, f"{new_id}_history.json")
        # if os.path.exists(old_path):
        #     os.rename(old_path, new_path)
  
        try:
            # 加载原有记忆实例
            memory = self.loadOrCreateMemory(old_id)
            # 使用 AAXWJumpinHistoriedMemory 的 rename 方法
            return memory.rename(new_id)
        except Exception as e:
            self.AAXW_CLASS_LOGGER.error(f"重命名记忆失败: {str(e)}")
            return False
    
    def _newName(self) ->str :
        """Generate a new name based on time"""
        return f"interact{datetime.now().strftime('%Y%m%d%H%M%S')}"




# 线程异步处理AI IO任务。
@AAXW_JUMPIN_LOG_MGR.classLogger()
class AIThread(QThread):
    
    #newContent,id 对应：ShowingPanel.appendToContentById 回调
    updateUI = Signal(str,str)  

    def __init__(self,text:str,uiCellId:str,llmagent:AAXWAbstractAIConnOrAgent):
        super().__init__()
        
        # self.mutex = QMutex()
        self.text:str=text
        self.uiId:str=uiCellId
        self.llmagent:AAXWAbstractAIConnOrAgent=llmagent
        
    def run(self):
        self.msleep(500)  # 执行前先等界面渲染
        # self.mutex.lock()
        # print(f"thread inner str:{self.text} \n")
        self.llmagent.requestAndCallback(self.text, self.callUpdateUI)
        # self.mutex.unlock()
        
    def callUpdateUI(self,newContent:str):
        # 最好强制类型转换。self.uiId:str 或 str(self.uiId)
        self.updateUI.emit(str(newContent), str(self.uiId)) 
        
# ai  end





#
# Jumpin applet manager 先注册类型以及其实例化后的关联（register并没有实例化）
@AAXWJumpinDICUtilz.register(key="jumpinAppletManager",
    dependencyContainer="_nativeDependencyContainer",
    jumpinConfig="jumpinConfig",
    mainWindow="mainWindow")
@AAXW_JUMPIN_LOG_MGR.classLogger()
class AAXWJumpinAppletManager(AAXWAppletManager):
    AAXW_CLASS_LOGGER:logging.Logger

    def __init__(self):
        super().__init__(maxCapacity = self.DEFAULT_MAX_CAPACITY)
        # DI注入
        self.dependencyContainer:Union[AAXWDependencyContainer,None]=None
        self.jumpinConfig:Union['AAXWJumpinConfig',None]=None
        self.mainWindow:Union['AAXWJumpinMainWindow',None]=None


    def removeAppletByInstance(self, applet: AAXWAbstractApplet) -> bool:
        """
        通过Applet实例引用来删除Applet
        :param applet: 要删除的Applet实例
        :return: 删除是否成功
        """
        try:
            # 查找实例在列表中的索引
            for index, existing_applet in enumerate(self.applets):
                if existing_applet is applet:  # 使用 is 进行身份比较
                    return self.removeApplet(index)
            
            self.AAXW_CLASS_LOGGER.warning(f"Applet instance not found: {applet.getName()}")
            return False
            
        except Exception as e:
            self.AAXW_CLASS_LOGGER.error(f"Failed to remove applet by instance: {str(e)}")
            return False
        
        
    # TODO 等待抽象到父类
    def activateNextLoop(self) -> bool:
        """
        激活下一个 Applet，如果当前是最后一个则激活第一个
        Returns:
            bool: 是否成功激活了新的 Applet
        """
        if len(self.applets) <= 1:
            self.AAXW_CLASS_LOGGER.debug("Applets数量<=1，无需切换")
            return False
            
        try:
            # 计算下一个索引，如果超出范围则回到0
            next_index = (self.activatedAppletIndex + 1) % len(self.applets)
            
            # 激活下一个 Applet
            success = self.activateApplet(next_index)
            if success:
                self.AAXW_CLASS_LOGGER.info(
                    f"已切换到下一个Applet[{next_index}]: {self.applets[next_index].getName()}")
            return success
            
        except Exception as e:
            self.AAXW_CLASS_LOGGER.error(f"切换到下一个Applet时发生错误: {str(e)}")
            return False
    #
    # 增加资源注入给applet；
    @override
    def addApplet(self, applet: AAXWAbstractApplet, index: int = -1) -> bool:
        #
        # 先注入资源给applet
        setattr(applet, "appletManager", self) #TODO 该部分可抽象到父类。
        #
        if hasattr(applet, "dependencyContainer"):
            setattr(applet, "dependencyContainer", self.dependencyContainer)
        if hasattr(applet, "jumpinConfig"):
            setattr(applet, "jumpinConfig", self.jumpinConfig) 
        if hasattr(applet, "mainWindow"):
            setattr(applet, "mainWindow", self.mainWindow)

        # 再加入管理器
        return super().addApplet(applet=applet, index=index)
#
# Applet管理器 end
##



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


# 默认功能的applet
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
        # 默认agent
        self.agentEnvironment=AgentEnvironment(runtimeType="pyside6")
        self.aaAgent=self.agentEnvironment.createAgent("ANAN")
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
        ]
        )
        #aaAgent 创建后就启动状态。 

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

#
if __name__ == "__main__":

    try:
        # 这里使用了相对导入，但builtin_plugins做为自己模块增加包名的操作。
        import ananxw_jumpin.builtin_plugins
        pass
    except Exception as e: 
        AAXW_JUMPIN_MODULE_LOGGER.warning(
            f"额外的ananxw_jumpin.builtin_plugin未正常导入，不影响allin1f的单文件运行。{e}")
        AAXW_JUMPIN_MODULE_LOGGER.warning(
            f"错误堆栈信息: {str(e)}\n{traceback.format_exc()}")
        # traceback.print_exc()
    finally:
        pass

    try:
        # 这里使用了相对导入，但builtin_plugins做为自己模块增加包名的操作。
        import ananxw_jumpin.builtin_plugins_debug
    except Exception as e: 
        AAXW_JUMPIN_MODULE_LOGGER.warning(
            f"额外的ananxw_jumpin.builtin_plugin_debug未正常导入，不影响allin1f的单文件运行。{e}")
        AAXW_JUMPIN_MODULE_LOGGER.warning(
            f"错误堆栈信息: {str(e)}\n{traceback.format_exc()}")
    finally:
        pass


    # all in one file main function.
    def main_allin1file():
        agstool=None
        pluginManager:AAXWFileSourcePluginManager=None #type:ignore
        appletManager:AAXWJumpinAppletManager=None #type:ignore
        try:
            app = QApplication(sys.argv)

            # 实例化历史/记忆存储管理器
            aiMemoryManager:AAXWJumpinFileAIMemoryManager=AAXWJumpinDICUtilz.getAANode(
                "jumpinAIMemoryManager")
            aiMemoryManager.initRes() #初始化历史/记忆存储管理器


            # TODO mainWindow的实例化与初始化比比较特殊，需要在app启动后初始化？之后看是否特别处理？
            mainWindow = AAXWJumpinMainWindow()
            AAXWJumpinDICUtilz.setAANode(
                key="mainWindow",node=mainWindow,
                diContainer="_nativeDependencyContainer", #需要时使用di容器获取资源
                jumpinConfig='jumpinConfig',
            )
            mainWindow.initAppRes()
            

            # 实例化插件管理器，并做默认初始化；
            pluginManager=AAXWJumpinDICUtilz.getAANode(
                "jumpinPluginManager")
            pluginManager.pluginRootDirectory="./"
            pluginManager.builtinPackagePrefix="ananxw_jumpin"

            #增加默认applet
            appletManager=AAXWJumpinDICUtilz.getAANode(
                "jumpinAppletManager")
            defaultCompoApplet=AAXWJumpinDefaultCompoApplet()
            appletManager.addApplet(defaultCompoApplet)
            appletManager.activateApplet(0) #激活默认applet

            #检测内置插件 
            pluginManager.detectBuiltinPlugins() 
            nameLs=pluginManager.listPluginBuilderNames()
            AAXW_JUMPIN_MODULE_LOGGER.info(f"plugin nameLs :{nameLs}")

            #安装插件，时会实例化插件其中可能会需要各种主干资源。
            pluginManager.installAllDetectedPlugins() #安装初始化所有插件
        
            # 插件以及applet加载完成后， 初始化"伙伴与应用"的列表
            defaultCompoApplet._initBuddyAndAppletListUI()

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

            if pluginManager:pluginManager.release()
            AAXWJumpinDICUtilz.clear()
 
    #执行main
    main_allin1file()
    pass


##
# 遗留代码，待删除；
##
...
