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

from PySide6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QTextEdit, QSplitter, 
    QToolBar, QPushButton, QHBoxLayout, QLineEdit, QSizePolicy)
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebEngineCore import QWebEngineSettings, QWebEnginePage, QWebEngineProfile
from PySide6.QtWebChannel import QWebChannel
from PySide6.QtCore import QUrl, Qt, Slot, QObject
import sys
import os
import json

class MCPConfigHandler(QObject):
    """MCP配置处理器，处理与前端的交互"""
    
    def __init__(self, workDir=None):
        super().__init__()
        self.workDir = workDir if workDir else os.path.dirname(os.path.abspath(sys.argv[0]))
        self.configPath = os.path.join(self.workDir, "mcp.json")

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

class AAXWJumpinWebViewWindow(QWidget):
    def __init__(self, workDir=None, parent=None):
        super().__init__(parent)
        self.workDir = workDir if workDir else os.path.dirname(os.path.abspath(sys.argv[0]))
        self.setWindowTitle("ANANXW Jumpin WebView")
        # 设置窗口属性，但保留标准窗口装饰
        # self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.WindowStaysOnTopHint)
        self._mainAppClosed = False  # 标记主应用是否已关闭
        self._altPressed = False  # 添加Alt键状态跟踪

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
