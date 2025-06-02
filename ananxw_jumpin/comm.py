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
# @Date:2025-02-19 20:33:24
# @Last Modified by:wfeng007
#
#
#  ananxw jumpin 共用资源，从原allin1f中拆出
#   app 日志器实例
#   app DI容器实例
#

# import pstats
import sys
import os
import time
import re 
import traceback
import threading
import logging
from datetime import datetime
from typing import Callable, List, Dict, Type, Any, TypeVar, Union, cast, Tuple, Protocol

from .ananxw_framework import AAXWLoggerManager, AAXWDependencyContainer

# 创建日志管理器实例 模块globe层次，也作为APP共用管理
AAXW_JUMPIN_LOG_MGR = AAXWLoggerManager() 

# 本模块，模块日志器
AAXW_JUMPIN_MODULE_LOGGER:logging.Logger=AAXW_JUMPIN_LOG_MGR.getModuleLogger(
    sys.modules[__name__])

# 创建依赖注入容器实例
AAXWJumpinDICUtilz = AAXWDependencyContainer()

