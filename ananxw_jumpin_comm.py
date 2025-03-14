#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# @Author:wfeng007
# @Date:2025-02-19 20:33:24
# @Last Modified by:wfeng007
#
#
#  ananxw jumpin 共用资源，从原allin1f中拆出
#   app 日志器实例
#   app DI容器实例
#

# import pstats
import sys, os,time
import re 
import traceback
from datetime import datetime
from typing import Callable, List, Dict, Type,Any,TypeVar,Union,cast, Tuple,Protocol
from typing import cast
import threading

import logging

from ananxw_jumpin.ananxw_framework import AAXWLoggerManager,AAXWDependencyContainer

# 创建日志管理器实例 模块globe层次，也作为APP共用管理
AAXW_JUMPIN_LOG_MGR = AAXWLoggerManager() 

# 本模块，模块日志器
AAXW_JUMPIN_MODULE_LOGGER:logging.Logger=AAXW_JUMPIN_LOG_MGR.getModuleLogger(
    sys.modules[__name__])


AAXWJumpinDICUtilz=AAXWDependencyContainer()

# TODO 这个类写法用处不大吧？ 实例化用全局大写即可？
# class AAXWJumpinDICUtilz: #单例化
#     """AAXWDependencyContainer的单例化工具类"""
#     __instance = None
#     _insLock = threading.Lock()
#     # _opLock = threading.Lock()

#     @classmethod
#     def getInstance(cls):
#         if cls.__instance is None:
#             with cls._insLock:
#                 if cls.__instance is None:
#                     cls.__instance = AAXWDependencyContainer()
#         return cls.__instance

#     @classmethod
#     def register(cls, key: str, isSingleton: bool = True, isLazy: bool = False, **dependencies):
#         return cls.getInstance().register(key, isSingleton, isLazy, **dependencies)

#     @classmethod
#     def getAANode(cls, key: str) -> Any:
#         # with cls._opLock:
#             return cls.getInstance().getAANode(key)

#     @classmethod
#     def setAANode(cls, key: str, node: Any, isSingleton: bool = True, **dependencies):
#         return cls.getInstance().setAANode(key, node, isSingleton, **dependencies)

#     @classmethod
#     def clear(cls):
#         with cls._insLock:
#             if cls.__instance:
#                 cls.__instance.clear()
#             cls.__instance = None