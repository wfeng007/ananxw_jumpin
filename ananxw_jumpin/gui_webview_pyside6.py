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
# @Date:2025-03 
# @Last Modified by:wfeng007
#
##
# gui 基于pyside6的webview的实现的gui延伸实现。 
# 部分界面功能转为web页面实现。
# 基于webview，已提供：
#   1. MCP配置文件基本编辑与展示功能。
#
##

import sys
import os
import logging
import json
from typing import TYPE_CHECKING, Optional

from PySide6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QTextEdit, QSplitter, 
    QToolBar, QPushButton, QHBoxLayout, QLineEdit, QSizePolicy)
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebEngineCore import QWebEngineSettings, QWebEnginePage, QWebEngineProfile
from PySide6.QtWebChannel import QWebChannel
from PySide6.QtCore import QUrl, Qt, Slot, QObject


# 检查解决循环导入问题
if TYPE_CHECKING:
    from .gui_pyside6 import AAXWJumpinMainWindow

if TYPE_CHECKING:
    # AAXWMcpClientManager 暂时在 default_applets_aiagents 中实现
    from .default_applets_aiagents import AAXWMcpClientManager

from .comm import AAXW_JUMPIN_LOG_MGR
# 模块日志器
# 本模块，模块日志器
AAXW_JUMPIN_MODULE_LOGGER:logging.Logger=AAXW_JUMPIN_LOG_MGR.getModuleLogger(
    module=sys.modules[__name__])

class MCPConfigHandler(QObject):
    """MCP配置处理器，处理与前端的交互"""
    
    def __init__(self, workDir=None):
        super().__init__()
        self.workDir = workDir if workDir else os.path.dirname(os.path.abspath(sys.argv[0]))
        self.configPath = os.path.join(self.workDir, "mcp.json")
        self.mcpClientManager = None

    def setMcpClientManager(self, manager: 'AAXWMcpClientManager'):
        """设置MCP客户端管理器"""
        self.mcpClientManager = manager

    @Slot(str, bool, result=bool)
    def toggleServer(self, serverName: str, isChecked: bool) -> bool:
        """切换服务器状态
        
        Args:
            serverName: 服务器名称
            isChecked: 是否开启
            
        Returns:
            bool: 操作是否成功
        """
        if not self.mcpClientManager:
            print("MCP客户端管理器未初始化")
            return False
            
        try:
            return self.mcpClientManager.setSessionAutoStart(
                sessionName=serverName,
                setAutoStart=isChecked,
                doStartStop=isChecked
            )
        except Exception as e:
            print(f"切换服务器状态失败: {str(e)}")
            return False

    @Slot(str, result=str)
    def getServerStatus(self, serverName: str) -> str:
        """获取服务器状态
        
        Args:
            serverName: 服务器名称
            
        Returns:
            str: 服务器状态
                - "running": 运行中
                - "error": 错误（配置了自动启动但未能正常运行）
                - "stopped": 已停止（未配置自动启动或手动停止）
        """
        AAXW_JUMPIN_MODULE_LOGGER.debug(f"[{serverName}] 开始检查服务器状态")
        
        if not self.mcpClientManager or not self.mcpClientManager.getMcpClient():
            AAXW_JUMPIN_MODULE_LOGGER.error(f"[{serverName}] MCP客户端管理器未初始化")
            return "error"
            
        try:
            # 先检查是否配置为自动启动
            isAutoStart = self.mcpClientManager.isSessionAutoStart(serverName)
            AAXW_JUMPIN_MODULE_LOGGER.debug(f"[{serverName}] 自动启动状态: {isAutoStart}")
            
            if not isAutoStart:
                return "stopped"  # 未配置自动启动，直接返回stopped状态
                
            mcpClient = self.mcpClientManager.getMcpClient()
            try:
                # 使用 sendPing 方法来检测服务器是否在线
                if mcpClient.sendPing(serverName, timeout=1.0):
                    AAXW_JUMPIN_MODULE_LOGGER.info(f"[{serverName}] 服务器运行中，ping成功")
                    return "running"
                AAXW_JUMPIN_MODULE_LOGGER.warning(f"[{serverName}] 服务器配置了自动启动但ping失败")
                return "error"  # 配置了自动启动但ping失败
            except Exception as e:
                if "is not running" in str(e):
                    AAXW_JUMPIN_MODULE_LOGGER.error(f"[{serverName}] 服务器配置了自动启动但未运行: {e}")
                    return "error"  # 配置了自动启动但服务器未运行
                raise  # 其他错误继续抛出
        except Exception as e:
            AAXW_JUMPIN_MODULE_LOGGER.error(f"[{serverName}] 获取服务器状态失败: {e}")
            return "error"

    @Slot(str, result=bool)
    def isServerAutoStart(self, serverName: str) -> bool:
        """检查服务器是否配置为自动启动
        
        Args:
            serverName: 服务器名称
            
        Returns:
            bool: 是否配置为自动启动
        """
        if not self.mcpClientManager:
            return False
            
        return self.mcpClientManager.isSessionAutoStart(serverName)

    @Slot(result=str)
    def loadConfig(self):
        """加载MCP配置文件"""
        try:
            if os.path.exists(self.configPath):
                with open(self.configPath, 'r', encoding='utf-8') as f:
                    return f.read()
            return json.dumps({"error": "配置文件不存在"})
        except Exception as e:
            return json.dumps({"error": f"加载配置失败: {str(e)}"})

    @Slot(str, result=bool)
    def saveConfig(self, configStr):
        """保存MCP配置文件"""
        try:
            # 验证JSON格式
            config = json.loads(configStr)
            
            # 保存到文件
            with open(self.configPath, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            return True
        except json.JSONDecodeError:
            print("Invalid JSON format")
            return False
        except Exception as e:
            print(f"Save config failed: {str(e)}")
            return False

class AAXWWebEnginePage(QWebEnginePage):
    """扩展的WebEnginePage，用于捕获JavaScript控制台消息"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self._view = parent
        self._window = None  # 保存对主窗口的引用

    def setWindow(self, window):
        """设置主窗口引用"""
        self._window = window

    def javaScriptConsoleMessage(self, level, message, lineNumber, sourceID):
        """重写控制台消息处理方法"""
        # print(f"接收到控制台消息: level={level}, message={message}")  # 调试输出
        
        # 直接使用保存的主窗口引用
        if self._window:
            # 根据不同级别添加不同的前缀
            prefix = {
                QWebEnginePage.JavaScriptConsoleMessageLevel.InfoMessageLevel: "[INFO]",
                QWebEnginePage.JavaScriptConsoleMessageLevel.WarningMessageLevel: "[WARN]",
                QWebEnginePage.JavaScriptConsoleMessageLevel.ErrorMessageLevel: "[ERROR]"
            }.get(level, "[LOG]")
            
            msg = f"{prefix} {message}"
            if sourceID:
                msg += f" (来自 {sourceID})"
            if lineNumber > 0:
                msg += f" [行 {lineNumber}]"
            
            try:
                self._window.logMessage(msg)
            except Exception as e:
                print(f"输出消息时发生错误: {e}")  # 调试输出

@AAXW_JUMPIN_LOG_MGR.classLogger()
class AAXWJumpinWebViewWindow(QWidget):
    """内置webview的浏览器gui窗口。"""
    AAXW_CLASS_LOGGER: logging.Logger

    def __init__(self, workDir=None, parent=None):
        super().__init__(parent)
        self.workDir = workDir if workDir else os.path.dirname(os.path.abspath(sys.argv[0]))
        self.setWindowTitle("ANANXW Jumpin WebView")
        # 设置窗口属性，但保留标准窗口装饰
        # self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.WindowStaysOnTopHint)
        self._mainAppClosed = False  # 标记主应用是否已关闭
        self._altPressed = False  # 添加Alt键状态跟踪
        self._mainWindow: 'AAXWJumpinMainWindow' = None  # 保存主窗口引用

        # 创建主布局
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(2)

        # 创建开发者工具条
        self.devToolbar = QToolBar()
        self.devToolbar.setStyleSheet("""
            QToolBar {
                background-color: #f0f0f0;
                border: none;
                padding: 5px;
            }
            QPushButton {
                background-color: #ffffff;
                border: 1px solid #cccccc;
                padding: 5px 10px;
                margin: 0 2px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #e6e6e6;
                border-color: #adadad;
            }
            QLineEdit {
                background-color: #ffffff;
                border: 1px solid #cccccc;
                padding: 5px;
                border-radius: 3px;
                min-width: 200px;
            }
        """)
        
        # 创建资源地址编辑器和加载按钮的容器
        addressContainer = QWidget()
        addressLayout = QHBoxLayout(addressContainer)
        addressLayout.setContentsMargins(0, 0, 0, 0)
        addressLayout.setSpacing(5)
        
        # 创建资源地址编辑器
        self.addressEdit = QLineEdit()
        self.addressEdit.setPlaceholderText("输入资源地址...")
        # 设置尺寸策略，使编辑器能够自动扩展
        self.addressEdit.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        
        # 创建加载按钮
        self.loadButton = QPushButton("加载")
        self.loadButton.clicked.connect(self.loadResource)
        
        # 将编辑器和按钮添加到容器
        addressLayout.addWidget(self.addressEdit)
        addressLayout.addWidget(self.loadButton)
        
        # 创建工具条按钮
        self.refreshButton = QPushButton("刷新页面")
        self.toggleConsoleButton = QPushButton("显示/隐藏控制台")
        self.clearConsoleButton = QPushButton("清理控制台")
        self.toggleStaysOnTopButton = QPushButton("切换置顶")  # 新增置顶按钮
        
        # 添加所有控件到工具条
        self.devToolbar.addWidget(addressContainer)  # 添加地址编辑器容器
        self.devToolbar.addSeparator()  # 添加分隔符
        self.devToolbar.addWidget(self.refreshButton)
        self.devToolbar.addWidget(self.toggleConsoleButton)
        self.devToolbar.addWidget(self.clearConsoleButton)
        self.devToolbar.addWidget(self.toggleStaysOnTopButton)  # 添加置顶按钮到工具条
        
        # 连接按钮信号
        self.refreshButton.clicked.connect(self.refreshPage)
        self.toggleConsoleButton.clicked.connect(self.toggleConsole)
        self.clearConsoleButton.clicked.connect(self.clearConsole)
        self.toggleStaysOnTopButton.clicked.connect(self.toggleStaysOnTop)  # 连接置顶按钮信号
        
        # 默认隐藏工具条
        self.devToolbar.hide()
        
        # 添加工具条到布局
        layout.addWidget(self.devToolbar)

        # 创建分割器
        self.splitter = QSplitter(Qt.Orientation.Vertical)
        layout.addWidget(self.splitter)

        # 创建 WebView
        self.browser = QWebEngineView()
        # 使用自定义的WebEnginePage
        webPage = AAXWWebEnginePage(self.browser)
        webPage.setWindow(self)  # 设置主窗口引用
        self.browser.setPage(webPage)
        
        # 创建控制台输出显示区域
        self.consoleOutput = QTextEdit()
        self.consoleOutput.setReadOnly(True)
        self.consoleOutput.setPlaceholderText("JavaScript控制台输出...")
        self.consoleOutput.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #ffffff;
                font-family: 'Courier New', monospace;
                font-size: 12px;
                padding: 5px;
            }
        """)
        
        # 添加到分割器
        self.splitter.addWidget(self.browser)
        self.splitter.addWidget(self.consoleOutput)
        # 设置分割器的初始大小比例
        self.splitter.setSizes([600, 200])  # 保持原有高度设置
        self.consoleOutput.hide()  # 只需要隐藏控制台即可
        
        # 启用更多调试设置
        settings = self.browser.settings()
        settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessFileUrls, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.ErrorPageEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptCanOpenWindows, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptCanAccessClipboard, True)
        
        # 设置WebChannel @TODO 之后迁移到应用初始化的配置阶段
        self.channel = QWebChannel()
        self.mcpHandler = MCPConfigHandler(self.workDir)
        # mcpClientManager 将在 setMainWindow 中设置
        self.channel.registerObject("mcpHandler", self.mcpHandler)
        self.browser.page().setWebChannel(self.channel)
        
        # 添加页面加载完成的回调
        self.browser.loadFinished.connect(self.onLoadFinished)
        self.browser.page().loadFinished.connect(self.onPageLoadFinished)
        
        # 加载本地的Web应用程序
        self.webDir = os.path.join(self.workDir, "web")
        indexPath = os.path.join(self.webDir, "index.html")
        self.loadLocalFile(indexPath)
        
        # 设置窗口大小
        self.resize(1024, 768)

        # 安装事件过滤器
        self.installEventFilter(self)

    def setMainWindow(self, mainWindow: 'AAXWJumpinMainWindow'):
        """设置主窗口引用"""
        self._mainWindow = mainWindow
        
        # 设置主窗口引用后，重新尝试获取并设置 mcpClientManager
        mcpClientManager = self._getMcpClientManager()
        if mcpClientManager:
            self.mcpHandler.setMcpClientManager(mcpClientManager)
            self.AAXW_CLASS_LOGGER.info("[系统] MCP客户端管理器初始化成功")
        else:
            self.AAXW_CLASS_LOGGER.error("[错误] 未能获取到MCP客户端管理器，部分功能可能不可用")

    def _getMcpClientManager(self) -> Optional['AAXWMcpClientManager']:
        """获取MCP客户端管理器
        
        通过DI容器获取appletManager，然后获取默认applet实例，从而获取其中的mcpClientManager
        """
        try:
            if not self._mainWindow:
                self.AAXW_CLASS_LOGGER.error("主窗口引用未设置")
                return None
                
            # 获取主窗口中的DI容器
            diContainer = getattr(self._mainWindow, 'diContainer', None)
            if not diContainer:
                self.AAXW_CLASS_LOGGER.error("未找到DI容器")
                return None
            
            # 从DI容器获取appletManager
            appletManager = diContainer.getAANode('jumpinAppletManager')
            if not appletManager:
                self.AAXW_CLASS_LOGGER.error("未找到appletManager")
                return None
            self.AAXW_CLASS_LOGGER.debug("已找到appletManager")
            
            # 获取默认applet实例
            defaultApplet = appletManager.getApplet('jumpinDefaultCompoApplet')[0]
            if not defaultApplet:
                self.AAXW_CLASS_LOGGER.error("未找到默认applet")
                return None
            self.AAXW_CLASS_LOGGER.debug("已找到jumpinDefaultCompoApplet")
                
            # 获取mcpClientManager
            mcpClientManager = getattr(defaultApplet, 'mcpClientManager', None)
            if not mcpClientManager:
                self.AAXW_CLASS_LOGGER.error("未找到MCP客户端管理器")
                return None
            self.AAXW_CLASS_LOGGER.info("未找到MCP客户端管理器")
                
            return mcpClientManager
            
        except Exception as e:
            self.AAXW_CLASS_LOGGER.error(f"获取MCP客户端管理器失败: {str(e)}")
            return None

    def setMainAppClosed(self, closed=True):
        """设置主应用关闭状态"""
        self._mainAppClosed = closed
        if closed:
            # 如果主应用关闭，则关闭本窗口
            self.close()

    def closeEvent(self, event):
        """重写关闭事件，点击关闭按钮时只隐藏窗口"""
        event.ignore()  # 忽略关闭事件
        self.hide()     # 隐藏窗口
        self.logMessage("[系统] WebView窗口已隐藏")

    def logMessage(self, message):
        """添加日志消息到控制台输出"""
        # print(f"正在输出消息到控制台: {message}")  # 调试输出
        self.consoleOutput.append(message)
        # 确保滚动到最新内容
        self.consoleOutput.verticalScrollBar().setValue(
            self.consoleOutput.verticalScrollBar().maximum()
        )
            
    def onLoadFinished(self, ok):
        if ok:
            # 更新地址栏为当前URL
            currentUrl = self.browser.url().toString()
            self.addressEdit.setText(currentUrl)
            
            self.logMessage("[系统] 页面加载成功")
            
            # 注入测试代码
            self.browser.page().runJavaScript("""
                console.log('测试: WebView初始化成功');
                // 测试所有控制台方法
                console.info('测试: Info消息');
                console.warn('测试: Warning消息');
                console.error('测试: Error消息');
            """)
        else:
            self.logMessage("[系统] 页面加载失败")
            
    def onPageLoadFinished(self, ok):
        if ok:
            print("页面内容加载完成")
            self.logMessage("[系统] 页面内容加载完成")
            self.browser.page().runJavaScript(
                "console.log('页面内容加载完成');",
                0
            )
        else:
            print("页面加载失败")
            self.logMessage("[系统] 页面内容加载失败")

    def eventFilter(self, obj, event):
        """事件过滤器，用于处理Alt键切换工具条显示状态"""
        if event.type() == event.Type.KeyPress and event.key() == Qt.Key.Key_Alt:
            if not self._altPressed:  # 防止按住Alt重复触发
                self._altPressed = True
        elif event.type() == event.Type.KeyRelease and event.key() == Qt.Key.Key_Alt:
            if self._altPressed:  # 确保是之前按下的Alt释放
                self._altPressed = False
                # 切换工具条显示状态
                self.devToolbar.setVisible(not self.devToolbar.isVisible())
                if self.devToolbar.isVisible():
                    self.logMessage("[系统] 开发者工具条已显示")
                else:
                    self.logMessage("[系统] 开发者工具条已隐藏")
        return super().eventFilter(obj, event)

    def refreshPage(self):
        """刷新当前页面"""
        self.browser.reload()
        self.logMessage("[系统] 页面刷新")

    def toggleConsole(self):
        """切换控制台显示状态"""
        if self.consoleOutput.isVisible():
            self.consoleOutput.hide()
            self.logMessage("[系统] 控制台已隐藏")
        else:
            self.consoleOutput.show()
            self.logMessage("[系统] 控制台已显示")

    def clearConsole(self):
        """清理控制台内容"""
        self.consoleOutput.clear()
        self.logMessage("[系统] 控制台已清理")

    def loadLocalFile(self, filePath):
        """加载本地文件"""
        print(f"加载文件：{filePath}")
        # 更新地址编辑器
        self.addressEdit.setText(filePath)
        # 加载文件
        self.browser.setUrl(QUrl.fromLocalFile(filePath))

    def loadResource(self):
        """加载资源地址"""
        address = self.addressEdit.text().strip()
        if not address:
            self.logMessage("[错误] 请输入有效的资源地址")
            return
            
        # 判断是否是本地文件路径
        if os.path.exists(address):
            self.loadLocalFile(address)
        else:
            # 尝试作为URL加载
            try:
                url = QUrl(address)
                if url.isValid():
                    self.browser.setUrl(url)
                    self.logMessage(f"[系统] 正在加载URL: {address}")
                else:
                    self.logMessage("[错误] 无效的URL地址")
            except Exception as e:
                self.logMessage(f"[错误] 加载资源失败: {str(e)}")

    def toggleStaysOnTop(self):
        """切换窗口置顶状态"""
        # if self.windowFlags() & Qt.WindowType.WindowStaysOnTopHint:
        #     # 如果当前是置顶状态，取消置顶
        #     self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowStaysOnTopHint)
        #     self.toggleStaysOnTopButton.setText("切换置顶")
        #     self.logMessage("[系统] 窗口已取消置顶")
        # else:
        #     # 如果当前不是置顶状态，设置置顶
        #     self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
        #     self.toggleStaysOnTopButton.setText("取消置顶")
        #     self.logMessage("[系统] 窗口已置顶")
        self.logMessage("[系统]toggleStaysOnTop:暂未实现")
        pass
        
        # 重新显示窗口（因为更改窗口标志后窗口会隐藏）
        self.show()
        self.raise_()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AAXWJumpinWebViewWindow()
    window.show()
    sys.exit(app.exec())
