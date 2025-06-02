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
# @Date:2024-03-20
# @Last Modified by:wfeng007
##
#
# 从原ananxw_jumpin_ain1f.py中拆离而来。包含核心应用框架。
#
##
"""
核心业务逻辑模块，包含：
1. 配置管理
2. 内存管理
3. Applet管理
4. 插件管理
"""

import os
import sys
import time
import json
import logging
import argparse
import yaml
import importlib
import traceback
import urllib.parse
import urllib.request
from datetime import datetime
from typing import List, Dict, Any, Union, Optional, cast, TYPE_CHECKING, Type, Callable, Tuple
from abc import ABC, abstractmethod

try:
    from typing import override
except ImportError:
    from typing_extensions import override

from PySide6.QtCore import Qt, QObject, QThread, Signal, QMutex, QRunnable, QThreadPool, Slot
from PySide6.QtWidgets import QWidget, QFrame
from pydantic import BaseModel, Field

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

from . import __version__
from .comm import AAXW_JUMPIN_LOG_MGR, AAXWDependencyContainer, AAXWJumpinDICUtilz

if TYPE_CHECKING:
    from .gui_pyside6 import AAXWJumpinMainWindow

# 本模块，模块日志器
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
        else:
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
    3. onDeactivate(): Applet不再是当前活动Applet时调用
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
    def onDeactivate(self):
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
                activated_applet.onDeactivate()

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
                applet.onDeactivate()
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
    
    # 信息展示面板的配置默认 QSS
    MSGSHOWINGPANEL_QSS = """
    QFrame {
        border: 1px solid #ccc;
        border-radius: 5px;
        background-color: #f0f0f0 !important;
    }
    QScrollArea {
        background-color: #f0f0f0 !important;
        border: none; /* 这个是实际scrollArea外部边框 */
    }
    QScrollArea > QWidget { 
        /* background-color: #f0f0f0 !important;*/
    }
    QScrollArea > QWidget > QWidget {/* 这个是实际scrollArea展示出的背景色，可以设置为d4f2e7 查看到变化*/
        background-color: #f0f0f0 !important;
    }
    
    /* 下面的对QTextBrowser的样式配置，对用了AAXWCompoMarkdownContentBlock的 AAXWScrollPanel 没有用。
    这些应该由创建 QTextBrowser或AAXWCompoMarkdownContentBlock的 QSS 来配置。
    当前有效的应该是AAXWCompoMarkdownContentBlock.BASE_QSS 这个配置。
    */
    QTextBrowser {
        background-color: #e0e0e0;
        border: 1px solid #ccc;
        border-radius: 3px;
        padding: 5px;
    }
    QTextBrowser[contentOwnerType="ROW_CONTENT_OWNER_TYPE_USER"] {
        background-color: #e0e0e0; /*d4f2e7 e0e0e0*/
        margin-left: 200px;
    }
    QTextBrowser[contentOwnerType="ROW_CONTENT_OWNER_TYPE_OTHERS"] {
        background-color: #e6e6fa; /*d4f2e7 e6e6fa*/
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
        "background-color": "#d4f2e7",  # 添加固定白色背景
        "color": "#000000"  # 添加固定黑色文字颜色
    }

    # 新增 INPUT_PANEL_STYLE
    INPUT_PANEL_QSS = """
        AAXWJumpinInputPanel {
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

    # 添加新的样式配置
    # SCROLL_PANEL_QSS = """
    # QFrame {
    #     border: 1px solid #ccc;
    #     border-radius: 5px;
    #     background-color: #f9f9f9;
    # }
    # """

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
    直接使用OpenAI API实现，不再依赖Langchain的ChatOpenAI封装。
    但仍使用langchain的Message对象来构建消息。
    """
    AAXW_CLASS_LOGGER:logging.Logger

    SYSTEM_PROMPT_TEMPLATE="""
    你的名字是ANAN是一个AI入口助理;
    请关注用户跟你说的内容，和善的回答用户，与用户要求。
    如果用户说的不明确，请提示用户可以说的更明确。
    """

    USER_PROMPT_TEMPLATE="""
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
        self.client = None
        
        # 尝试初始化客户端，但不强制要求成功
        try:
            self.updateConfig(
                apiKey=self.api_key, 
                baseUrl=self.base_url, 
                modelName=self.model_name
            )
        except Exception as e:
            self.AAXW_CLASS_LOGGER.warning(f"初始化OpenAI客户端时出现警告: {str(e)}")
    
    def updateConfig(
            self, apiKey: str = None, baseUrl: str = None, modelName: str = None): # type: ignore
        """
        更新OpenAI连接配置。
        
        :param api_key: 新的OpenAI API密钥。
        :param base_url: 新的OpenAI API基础URL。
        :param model_name: 新的模型名称。
        """
        self.AAXW_CLASS_LOGGER.debug(f"to updateConfig: apiKey:***, baseUrl:{baseUrl}, modelName:{modelName}")

        # 更新模式：只更新非None的参数
        if apiKey and apiKey.strip() !="":
            self.api_key = apiKey
        
        if baseUrl and baseUrl.strip() !="":
            self.base_url = baseUrl
            
        if modelName and modelName.strip() !="":
            self.model_name = modelName
        
        # 验证API密钥是否存在
        if not self.api_key:
            self.AAXW_CLASS_LOGGER.warning("OpenAI API密钥为空，请配置有效的API密钥")
            return
            
        # 初始化OpenAI客户端
        client_params = {
            "api_key": self.api_key,
        }
        
        if self.base_url:
            client_params["base_url"] = self.base_url
            
        # 初始化或更新OpenAI客户端实例
        try:
            self.client = OpenAI(**client_params)
            # 记录日志
            self.AAXW_CLASS_LOGGER.info(f"OpenAI连接配置已更新，模型: {self.model_name}")
        except Exception as e:
            self.AAXW_CLASS_LOGGER.error(f"初始化OpenAI客户端失败: {str(e)}\n{traceback.format_exc()}")
            # raise  # 重新抛出异常，让调用者知道初始化失败
    
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
        
        # 检查API密钥和客户端是否已初始化
        if not self.api_key:
            error_msg = "OpenAI API密钥未配置，无法发送请求"
            self.AAXW_CLASS_LOGGER.error(error_msg)
            func(f"\n\n[错误] {error_msg}")
            return
            
        if not hasattr(self, 'client') or self.client is None:
            error_msg = "OpenAI客户端未初始化，无法发送请求"
            self.AAXW_CLASS_LOGGER.error(error_msg)
            func(f"\n\n[错误] {error_msg}")
            return
        
        # 仍然使用langchain的Message对象构建消息
        system_message = SystemMessage(content=self.SYSTEM_PROMPT_TEMPLATE)
        human_message = HumanMessage(content=self.USER_PROMPT_TEMPLATE.format(message=prompt))
        
        # 转换为OpenAI API的消息格式
        messages = [
            ChatCompletionSystemMessageParam(content=system_message.content, role="system"),
            ChatCompletionUserMessageParam(content=human_message.content, role="user")
        ]

        self.AAXW_CLASS_LOGGER.debug(f"使用model_name:{self.model_name}, base_url:{self.base_url}; "
            f"以及最终 prompt-messages: {messages}")
        try:
            if isStream:
                # 流式请求
                stream = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=messages,
                    stream=True
                )
                
                for chunk in stream:
                    # 防止空块或没有选项的块导致索引错误
                    if not hasattr(chunk, 'choices') or len(chunk.choices) == 0:
                        continue
                    # 检查是否有delta属性    
                    if not hasattr(chunk.choices[0], 'delta'):
                        continue
                    # 检查delta内容
                    delta = chunk.choices[0].delta
                    if hasattr(delta, 'content') and delta.content is not None:
                        content = delta.content
                        # time.sleep(0.1)  # 已被注释掉
                        func(content)
            else:
                # 非流式请求
                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=messages,
                    stream=False
                )
                func(response.choices[0].message.content)
        except Exception as e:
            request_type = "流式" if isStream else "非流式"
            self.AAXW_CLASS_LOGGER.error(f"{request_type}请求处理失败: {str(e)}\n{traceback.format_exc()}")
            func(f"\n\n[错误] 请求处理失败: {str(e)}")

    def embedding(self, prompt: str, model: str = "text-embedding-ada-002"):
        """
        获取文本嵌入。
        
        :param prompt: 需要嵌入的文本。
        :param model: 使用的嵌入模型。
        :return: 文本的嵌入向量。
        """
        # 检查API密钥和客户端是否已初始化
        if not self.api_key or not hasattr(self, 'client') or self.client is None:
            self.AAXW_CLASS_LOGGER.error("OpenAI API密钥未配置或客户端未初始化，无法获取嵌入")
            return None
            
        try:
            # 直接使用OpenAI API获取嵌入
            response = self.client.embeddings.create(
                model=model,
                input=prompt
            )
            return response.data[0].embedding
        except Exception as e:
            self.AAXW_CLASS_LOGGER.error(f"嵌入处理失败: {str(e)}\n{traceback.format_exc()}")
            return None
    
    def edit(self, prompt: str, instruction: str):
        """
        根据指令编辑文本。
        
        :param prompt: 原始文本。
        :param instruction: 编辑指令。
        :return: 编辑后的文本。
        """
        # 检查API密钥和客户端是否已初始化
        if not self.api_key or not hasattr(self, 'client') or self.client is None:
            error_msg = "OpenAI API密钥未配置或客户端未初始化，无法执行编辑"
            self.AAXW_CLASS_LOGGER.error(error_msg)
            return f"[错误] {error_msg}"
            
        # 目前OpenAI不再提供专门的edit API，使用聊天完成API模拟
        system_content = f"你是一个文本编辑助手。请按照以下指令编辑提供的文本：\n{instruction}"
        
        # 仍然使用langchain的Message对象构建消息
        system_message = SystemMessage(content=system_content)
        human_message = HumanMessage(content=prompt)
        
        # 转换为OpenAI API的消息格式
        messages = [
            ChatCompletionSystemMessageParam(content=system_message.content, role="system"),
            ChatCompletionUserMessageParam(content=human_message.content, role="user")
        ]
        
        try:
            # 使用OpenAI API
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages
            )
            return response.choices[0].message.content
        except Exception as e:
            self.AAXW_CLASS_LOGGER.error(f"编辑请求处理失败: {str(e)}\n{traceback.format_exc()}")
            return f"[错误] 编辑请求处理失败: {str(e)}"


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
        self.apiKey = "ollama"
        self.updateConfig(baseUrl= self.base_url, modelName=self.modelName)
    
    def updateConfig(
            self, apiKey: str = "ollama", baseUrl: str = None, modelName: str = None): # type: ignore
        # 设置默认的 API URLbaseUrl

        if apiKey and apiKey.strip() !="" :
            self.apiKey = apiKey

        if baseUrl and baseUrl.strip() !="":
            self.base_url = baseUrl

        if modelName and modelName.strip() !="":
            self.modelName= modelName

        # 
        try:
            #@TODO 这里上一个 client 是否要关闭
            self.client = OpenAI(
                base_url=self.base_url,
                api_key=self.apiKey,
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
                # 防止空块或没有选项的块导致索引错误
                if not hasattr(chunk, 'choices') or len(chunk.choices) == 0:
                    continue
                # 检查是否有delta属性
                if not hasattr(chunk.choices[0], 'delta'):
                    continue
                # 检查delta内容
                delta = chunk.choices[0].delta
                if hasattr(delta, 'content') and delta.content is not None:
                    content = delta.content
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
