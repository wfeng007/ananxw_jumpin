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
# @Date:2025-02-19 20:15:30
# @Last Modified by:wfeng007
#
#
#  ananxw 框架从原allin1f中拆出
#   日志器实现类（不包默认含管理器实例）
#   DI容器实现类（不包默认容器实例）
# 

import sys, os,time
import re 
import traceback
from datetime import datetime
from typing import Callable, List, Dict, Type,Any,TypeVar,Union,cast, Tuple,Protocol

import logging
from logging.handlers import TimedRotatingFileHandler


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
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(module)s.%(funcName)s [%(filename)s:%(lineno)d] - %(message)s'
        )
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






# Di框架与插件框架
# framework-di , framework-plugin
class AAXWDependencyContainer:
    """
    简易的依赖注入容器
    注册依赖关系：
    @dependencyContainer.register('key', isSingleton=True, isLazy=False)
    class...
    isLazy 暂时未实现，均为False；

    创建/获取已有，资源对象，如其依赖未创建则会创建对应依赖：
    dependencyContainer.getAANode(key)
    
    """
    def __init__(self):
        self._factories: Dict[str, Callable] = {}
        self._dependencies: Dict[str, Dict[str, str]] = {}
        self._isSingletonFlags: Dict[str, bool] = {}
        self._isLazyFlags: Dict[str, bool] = {}
        self._instances: Dict[str, Any] = {}
        #放入自己作为aware 自发现使用
        self.setAANode(key='_nativeDependencyContainer',node=self)

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

