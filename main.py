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
# 0.9+  @Date: 2025-03
#       已实现初步的agent框架能力，提供1个agent样例如：自主动态改名；
#       已实现专门的记忆/历史列表面板、单项记忆/历史card化展示及其操作功能；
#       
#
# 0.10+  @Date: 2025-04
#       已进行重构拆分ananxw_jumpin_ain1f.py。
#       已解决部分展示元素跟随系统模式的问题，先强制设置为指定颜色；
#       已增加模型管理面板，支持openai基本模型和ollama的基本管理；提供基本的yaml配置，来保存模型配置等。
#
#  @TODO:
#       MPC客户端功能；
#       代码块需支持plaintext/unknown 以及其他结构，未知，平文为全白。
#       mac运行支持与打包支持；
#       提供其他ai相关样例，如：chateveredit等
#       coze集成对接应用样例；
#       dify集成对接样例；
#       可集成密塔等搜索；
#       支持可能轻量级，流程式agent/多agent
#       轻量级meta agent；
#
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

from PySide6.QtCore import Qt, QObject, QThread, Signal, QMutex, QRunnable, QThreadPool, Slot
from PySide6.QtWidgets import QApplication, QWidget, QFrame
from pydantic import BaseModel, Field


# @FIXME 要兼容打包与工程执行；需要跟下面_setup_app_env_合并融合。
# 确定应用根目录
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# 将工程根目录添加到搜索路径
sys.path.insert(0, SCRIPT_DIR)

def get_resource_path(relative_path):
    """获取资源文件的绝对路径，兼容打包和开发环境"""
    if getattr(sys, 'frozen', False):
        # 打包环境
        base_path = getattr(sys, '_MEIPASS', SCRIPT_DIR)
    else:
        # 开发环境
        base_path = SCRIPT_DIR
    return os.path.join(base_path, relative_path)


def _setup_app_env_():
    # 设定在不同模式下环境情况

    if __name__ == "__main__": #作为入口运行

        # 将当前目录作为包的根目录
        # if base_path not in sys.path:
        #     sys.path.insert(0, base_path)

        if getattr(sys, 'frozen', False):
            # 作为入口运行 且为打包后执行：
            # 核心问题修复：确保正确设置打包后的模块查找路径
            base_dir = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
            
            # 将运行目录也加入路径搜索，因为部分资源可能在dist目录下而不是_MEIPASS中
            run_dir = os.path.dirname(sys.executable)
            if run_dir not in sys.path:
                sys.path.insert(0, run_dir)
                
            # 添加_libs目录到搜索路径
            libs_dir = os.path.join(run_dir, '_libs')
            if os.path.exists(libs_dir) and libs_dir not in sys.path:
                sys.path.insert(0, libs_dir)
                
            # 确保可以找到ananxw_jumpin包
            if base_dir not in sys.path:
                sys.path.insert(0, base_dir)
                
            # 尝试直接将ananxw_jumpin包的路径添加到sys.path
            package_path = os.path.join(base_dir, 'ananxw_jumpin')
            if os.path.exists(package_path) and package_path not in sys.path:
                sys.path.insert(0, package_path)
                
            # 额外调试信息，帮助排查问题
            print(f"Runtime sys.path: {sys.path}")
            print(f"Looking for package at: {package_path}")
            print(f"Package exists: {os.path.exists(package_path)}")
            
            # 检查是否可以直接导入
            try:
                import ananxw_jumpin
                print(f"Successfully imported ananxw_jumpin from {ananxw_jumpin.__file__}")
            except ImportError as e:
                print(f"Failed to import ananxw_jumpin: {e}")
                
        else:
            # 作为入口运行 且为开发环境直接执行
            # base_path = os.path.dirname(os.path.abspath(__file__))
            # 获取当前文件的目录，也作为包扫描路径
            project_root = os.path.dirname(os.path.abspath(__file__))
            if project_root not in sys.path:
                sys.path.insert(0, project_root)  # 插入到路径最前面
            ...
    else :
        # 作为模块导入运行     
        # 当前不存在；   
        pass
_setup_app_env_()

import ananxw_jumpin
import ananxw_jumpin.ananxw_framework
import ananxw_jumpin.backbone
import ananxw_jumpin.gui_pyside6
import ananxw_jumpin.default_applets_aiagents
import ananxw_jumpin.builtin_plugins

# 导入本地包
# from ananxw_jumpin.ananxw_framework import AAXWDependencyContainer
from ananxw_jumpin.comm import AAXW_JUMPIN_LOG_MGR, AAXWJumpinDICUtilz
from ananxw_jumpin.backbone import AAXWJumpinConfig,AAXWJumpinFileAIMemoryManager
from ananxw_jumpin.gui_pyside6 import AAXWJumpinMainWindow
from ananxw_jumpin.default_applets_aiagents import AAXWJumpinDefaultCompoApplet
from ananxw_jumpin.gui_pyside6 import AAXWJumpinTrayKit
from ananxw_jumpin.gui_pyside6 import AAXWGlobalShortcut

# 版本
from ananxw_jumpin import __version__ 


# 读取补充环境变量的配置.env，find_dotenv()
#   会以本文件为基础逐层目录往上寻找，直到寻找到为止。
from dotenv import load_dotenv, find_dotenv
__evnpath=find_dotenv()
print(f"Found evnpath: {__evnpath} , will load it.")
_ = load_dotenv(__evnpath)  #



#本模块，模块日志器
AAXW_JUMPIN_MODULE_LOGGER:logging.Logger=AAXW_JUMPIN_LOG_MGR.getModuleLogger(
    sys.modules[__name__])

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

    


##
# 遗留代码，待删除；
##
...
