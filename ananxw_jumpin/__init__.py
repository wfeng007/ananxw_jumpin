#!/usr/bin/env python
# -*- coding: utf-8 -*-
# import os
# __package_name__ = os.path.basename(os.path.dirname(os.path.abspath(__file__)))
__version__ = "0.11.0"
__package_name__ = "ananxw_jumpin"

# 导出主要的类和函数
from .backbone import *
from .gui_pyside6 import *
from .api import *
from .comm import *
from .ananxw_framework import *
from .ananxw_aiagent import *

# plugins 涉及根据模块前缀扫描加载，不能多命名导入；否则会重复扫描到并重复加载；
# from .builtin_plugins import * 
# from .default_plugins import *
