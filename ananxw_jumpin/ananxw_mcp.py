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
# @Date:2025-05-18 23:16:00
# @Last Modified by:wfeng007
#
##
# 
# MCP( Model Context Protocol) 实现
# MCP 客户端框架实现  
#   使用McpClient支持同步方法以及Future模式的异步方式处理对MCP服务端的访问；
#   利用简单McpClientSession（也需要从McpClient获取）支持async 自定义持续while循环；
#   
#  @TODO 日志器与日志升级
#  @TODO MCP 服务端框架实现
#  

import json
import sys
import asyncio
import os
import threading
import traceback
import contextlib
from concurrent.futures import TimeoutError, Future
from typing import Dict, Any, Optional, Tuple, List
from contextlib import AsyncExitStack
from mcp import ClientSession, StdioServerParameters, types
from mcp.client.stdio import stdio_client
from mcp.client.sse import sse_client
import logging
import anyio
import time
import uuid

# 调试使用添加父目录到 Python 路径
# if __name__ == "__main__":
#     # 获取当前文件的目录
#     current_dir = os.path.dirname(os.path.abspath(__file__))
#     # 获取 ananxw_jumpin 目录
#     project_dir = os.path.dirname(current_dir)
#     if project_dir not in sys.path:
#         sys.path.insert(0, project_dir)
# from ananxw_jumpin.comm import AAXW_JUMPIN_LOG_MGR
    
# 现在可以导入了
from .comm import AAXW_JUMPIN_LOG_MGR

# 模块日志器
# 本模块，模块日志器
AAXW_JUMPIN_MODULE_LOGGER:logging.Logger=AAXW_JUMPIN_LOG_MGR.getModuleLogger(
    module=sys.modules[__name__])


@AAXW_JUMPIN_LOG_MGR.classLogger(level=logging.DEBUG)
class McpClientSession:
    """表示MCP客户端中的一个服务器会话，管理与目标服务器的通信。
    适配了sse与stdio的实现。
    支持异步上下文管理。
    """
    AAXW_CLASS_LOGGER: logging.Logger
    
    def __init__(self, targetServerName: str, targetServerConfig: Dict[str, Any], mcpClient: 'McpClient'):
        self.targetServerName = targetServerName
        self.targetServerConfig = targetServerConfig
        self.mcpClient = mcpClient
        self.mcpSession: Optional[ClientSession] = None
        self.transportInstance: Optional[Any] = None
        self.transportType: Optional[str] = None
        self.availableTools: List[Dict[str, Any]] = []
        self._initialized = threading.Event()
        self._parent_stack: Optional[AsyncExitStack] = None
        
    async def __aenter__(self):
        """异步上下文管理器入口"""
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器退出"""
        await self.aClose()
        
    def __str__(self):
        return f"Session(target={self.targetServerName}, transport={self.transportType or 'not_connected'}, connected={self.mcpSession is not None})"

    def getConnectionInfo(self) -> Dict[str, Any]:
        """获取会话连接信息"""
        return {
            "targetServerName": self.targetServerName,
            "transportType": self.transportType,
            "isConnected": self.mcpSession is not None,
            "availableToolCount": len(self.availableTools)
        }
        
    def isInitialized(self) -> bool:
        """检查会话是否已初始化"""
        return self._initialized.is_set()

    def waitForInitialized(self, timeout: float = None) -> bool:
        """等待会话初始化完成"""
        return self._initialized.wait(timeout=timeout)

    async def _createStdioTransport(self, config: Dict[str, Any]) -> Tuple[Any, Any]:
        """创建stdio传输"""
        server_params = StdioServerParameters(
            command=config["command"],
            args=config.get("args", []),
            env={"PATH": os.getenv("PATH", "")}
        )
        return await self._parent_stack.enter_async_context(stdio_client(server_params))

    async def _createSseTransport(self, config: Dict[str, Any]) -> Tuple[Any, Any]:
        """创建SSE传输"""
        return await self._parent_stack.enter_async_context(
            sse_client(
                url=config["url"],
                headers={"Accept": "text/event-stream"},
                timeout=5.0,
                sse_read_timeout=300.0
            )
        )

    async def aInitialize(self, parent_stack: AsyncExitStack):
        """异步初始化会话连接"""
        try:
            self._parent_stack = parent_stack  # 保存父级stack引用
            
            if "command" in self.targetServerConfig:
                self.transportType = "stdio"
                self.transportInstance = await self._createStdioTransport(self.targetServerConfig)
            elif "url" in self.targetServerConfig:
                self.transportType = "sse"
                self.transportInstance = await self._createSseTransport(self.targetServerConfig)
            else:
                raise ValueError(f"Invalid server configuration for {self.targetServerName}")

            readStream, writeStream = self.transportInstance
            self.mcpSession = await self._parent_stack.enter_async_context(
                ClientSession(readStream, writeStream)
            )
            await self.mcpSession.initialize()
            
            self.availableTools = (await self.mcpSession.list_tools()).tools
            self._initialized.set()
            
            self.AAXW_CLASS_LOGGER.info(f"Connected to server: {self}")
            self.AAXW_CLASS_LOGGER.info("Available tools:")
            for tool in self.availableTools:
                self.AAXW_CLASS_LOGGER.info(f"- {tool.name}: {tool.description}")
                
        except Exception as e:
            self.AAXW_CLASS_LOGGER.error(f"Error initializing server {self.targetServerName}: {e}\n{traceback.format_exc()}")
            raise

    async def aClose(self):
        """异步关闭会话连接
        
        注意：
        1. 只关闭 transport 层资源（readStream, writeStream）
        2. mcpSession 由 ExitStack 管理，不在这里直接关闭
        3. 清理引用防止内存泄漏
        """
        try:
            # mcpSession 由 ExitStack 管理，这里不直接关闭
            # 只关闭 transport 层资源
            if self.transportInstance:
                self.AAXW_CLASS_LOGGER.debug(f"正在关闭传输实例: {self.transportInstance}")
                if isinstance(self.transportInstance, tuple):
                    readStream, writeStream = self.transportInstance
                    if hasattr(readStream, 'aclose'):
                        await readStream.aclose()
                        self.AAXW_CLASS_LOGGER.debug("关闭readStream实例(aclose)")
                    if hasattr(readStream, 'close'):
                        readStream.close()
                        self.AAXW_CLASS_LOGGER.debug("关闭readStream实例(close)")
                    if not hasattr(readStream, 'aclose') and not hasattr(readStream, 'close'):
                        self.AAXW_CLASS_LOGGER.warning("readStream传输实例没有close/aclose方法")
                        
                    if hasattr(writeStream, 'aclose'):
                        await writeStream.aclose()
                        self.AAXW_CLASS_LOGGER.debug("关闭writeStream实例(aclose)")
                    if hasattr(writeStream, 'close'):
                        writeStream.close()
                        self.AAXW_CLASS_LOGGER.debug("关闭writeStream实例(close)")
                    if not hasattr(writeStream, 'aclose') and not hasattr(writeStream, 'close'):
                        self.AAXW_CLASS_LOGGER.warning("writeStream传输实例没有close/aclose方法")
                        
                elif hasattr(self.transportInstance, 'aclose'):
                    await self.transportInstance.aclose()
                    self.AAXW_CLASS_LOGGER.debug("关闭单一传输实例(aclose)")
                elif hasattr(self.transportInstance, 'close'):
                    await self.transportInstance.close()
                    self.AAXW_CLASS_LOGGER.debug("关闭单一传输实例(close)")
                else:
                    self.AAXW_CLASS_LOGGER.warning("transportInstance 没有close/aclose方法")
                
                self.AAXW_CLASS_LOGGER.info(f"传输实例关闭完成: {self.targetServerName}")
        except Exception as e:
            self.AAXW_CLASS_LOGGER.error(f"Error closing server {self.targetServerName}: {e}\n{traceback.format_exc()}")
            raise
        finally:
            # 清理所有引用
            self.mcpSession = None  # 由 ExitStack 管理清理
            self.transportInstance = None
            self._initialized.clear()
            # 不清除 parent_stack 的引用，因为它是共享资源
            # self._parent_stack = None

    async def aListTools(self) -> List[types.Tool]:
        """异步获取工具列表"""
        if not self.mcpSession:
            raise ValueError(f"Server {self.targetServerName} is not running")
        toolsResponse = await self.mcpSession.list_tools()
        return toolsResponse.tools

    async def aCallTool(self, toolName: str, args: Dict[str, Any]) -> Any:
        """异步调用工具"""
        if not self.mcpSession:
            raise ValueError(f"Server {self.targetServerName} is not running")
        return await self.mcpSession.call_tool(toolName, args)

    async def aPing(self):
        """异步发送ping请求到目标服务器
        
        Returns:
            bool: ping是否成功
        """
        if not self.mcpSession:
            raise ValueError(f"Server {self.targetServerName} is not running")
        try:
            # send_ping 返回 EmptyResult 没有意义不处理。
            await self.mcpSession.send_ping()
            return True
        except Exception as e:
            self.AAXW_CLASS_LOGGER.error(f"Error pinging server {self.targetServerName}: {e}\n{traceback.format_exc()}")
            return False

@AAXW_JUMPIN_LOG_MGR.classLogger(level=logging.DEBUG)
class McpClient:
    """统一的MCP客户端实现"""
    AAXW_CLASS_LOGGER: logging.Logger
    
    def __init__(self, configPath: str= "./mcp.json", configContentDict: Optional[Dict[str, Any]] = None):
        """
        初始化MCP客户端
        
        Args:
            configPath: 配置文件路径,如果为None且configContentDict也为None,则使用默认路径"mcp.json"
            configContentDict: 配置内容字典,如果提供则优先使用此配置
        """
        self.configPath = configPath or "./mcp.json"
        self.mcpClientSessions: Dict[str, McpClientSession] = {}
        self.exitStack = AsyncExitStack()
        self._unified_client_loop: Optional[asyncio.AbstractEventLoop] = None  # 统一的客户端事件循环
        self._loop_thread: Optional[threading.Thread] = None  # 事件循环的后台线程
        self._initialized = threading.Event()
        self._main_task: Optional[asyncio.Task] = None  # 主任务
        self._operation_queue: Optional[asyncio.Queue] = None  # 操作队列

        # 优先使用传入的配置内容
        if configContentDict is not None:
            self.config = configContentDict
        else:
            self.config = self._loadConfig()
    
    # mcp底层的逻辑导致暂时只能用这种循环处理start stop在同一个协程task中处理对应动作
    #   否则就会报错。对于部分实现如stdio，start，stop并不是类似jdbc的数据连轻量或后台有pool化实现。
    #   无法兼容用成统一的 单方法中完成start stop。但sse的底层实现又用了 async context manager方式。
    #   很难介入管理生命周期资源，又要在同一个协程task中处理对应动作。
    async def _main_loop_context(self):
        """使用 AsyncExitStack 管理所有资源的主循环"""
        async with self.exitStack as main_stack:
            while True:
                try:
                    operation = await self._operation_queue.get()
                    operation_type = operation["type"]
                    operation_future = operation.get("future")  # 从操作中获取 Future
                    
                    try:
                        if operation_type == "start_server":
                            server_name = operation["server_name"]
                            config = operation["config"]
                            
                            # 创建新的会话
                            session = McpClientSession(server_name, config, self)
                            # 将会话添加到主 exitStack
                            await main_stack.enter_async_context(session)
                            # 初始化会话
                            await session.aInitialize(main_stack)
                            # 保存会话引用
                            self.mcpClientSessions[server_name] = session
                            
                            if operation_future:
                                operation_future.set_result(True)
                            
                        elif operation_type == "stop_server":
                            server_name = operation["server_name"]
                            if server_name in self.mcpClientSessions:
                                session = self.mcpClientSessions[server_name]
                                # 在同一个task中清理资源
                                await session.aClose()
                                del self.mcpClientSessions[server_name]
                                
                                if operation_future:
                                    operation_future.set_result(True)
                            
                        elif operation_type == "shutdown":
                            # 按FILO顺序清理所有会话
                            server_names = list(self.mcpClientSessions.keys())
                            for name in reversed(server_names):
                                session = self.mcpClientSessions[name]
                                await session.aClose()
                                del self.mcpClientSessions[name]
                            break
                            
                    except Exception as e:
                        self.AAXW_CLASS_LOGGER.error(
                            f"Error in operation {operation_type}: {e}\n{traceback.format_exc()}"
                        )
                        if operation_future:
                            operation_future.set_exception(e)
                    finally:
                        self._operation_queue.task_done()  # 标记任务完成
                        
                except Exception as e:
                    self.AAXW_CLASS_LOGGER.error(
                        f"Error in main loop: {e}\n{traceback.format_exc()}"
                    )

    def afStartServer(self, serverName: str) -> Future:
        """异步启动服务器，返回Future"""
        if not self._unified_client_loop:
            raise RuntimeError("Client not initialized")
            
        if serverName not in self.config["mcpServers"]:
            raise ValueError(f"Server {serverName} not found in config")

        # 创建Future对象
        future = self._unified_client_loop.create_future()
        
        async def _start_server():
            # 创建操作事件，直接包含future
            operation = {
                "type": "start_server",
                "server_name": serverName,
                "config": self.config["mcpServers"][serverName],
                "future": future  # 直接将future作为事件的一部分
            }
            await self._operation_queue.put(operation)
            return await future

        return self._run_coro_and_get_future(_start_server())

    def afStopServer(self, serverName: str) -> Future:
        """异步停止服务器，返回Future"""
        if not self._unified_client_loop:
            raise RuntimeError("Client not initialized")

        # 创建Future对象
        future = self._unified_client_loop.create_future()
        
        async def _stop_server():
            # 创建操作事件，直接包含future
            operation = {
                "type": "stop_server",
                "server_name": serverName,
                "future": future  # 直接将future作为事件的一部分
            }
            await self._operation_queue.put(operation)
            return await future

        return self._run_coro_and_get_future(_stop_server())

    def _run_event_loop(self):
        """在后台运行事件循环"""
        asyncio.set_event_loop(self._unified_client_loop)
        # 创建主循环任务
        self._main_task = self._unified_client_loop.create_task(self._main_loop_context())
        self._unified_client_loop.run_forever()

    def _loadConfig(self) -> Dict[str, Any]:
        """加载配置文件"""
        try:
            with open(self.configPath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            self.AAXW_CLASS_LOGGER.error(f"Error loading config file: {e}\n{traceback.format_exc()}")
            return {}

    def _run_coro_and_get_future(self, coro) -> Future:
        """在统一事件循环中执行协程并返回Future对象
        
        本方法会立即开始执行协程，返回的Future仅用于等待结果。
        
        Args:
            coro: 要执行的协程对象
            
        Returns:
            Future对象，可用于等待协程执行完成并获取结果
            
        Raises:
            RuntimeError: 如果客户端未初始化（事件循环不存在）
        """
        if not self._unified_client_loop:
            raise RuntimeError("Client not initialized")
        return asyncio.run_coroutine_threadsafe(coro, self._unified_client_loop)

    async def _init_client_task(self):
        """初始化客户端主任务"""
        self._main_task = asyncio.current_task()
        await self.exitStack.__aenter__()
        self._initialized.set()

    def initialize(self, timeout: float = 10.0) -> bool:
        """同步初始化客户端
        
        Args:
            timeout: 初始化超时时间(秒)
            
        Returns:
            bool: 是否初始化成功
        """
        try:
            # 创建新的事件循环
            self._unified_client_loop = asyncio.new_event_loop()
            
            # 创建操作队列
            self._operation_queue = asyncio.Queue()
            
            # 启动事件循环的后台线程
            self._loop_thread = threading.Thread(target=self._run_event_loop)
            self._loop_thread.daemon = True
            self._loop_thread.start()
            
            # 初始化主任务
            future = self._run_coro_and_get_future(self._init_client_task())
            future.result(timeout=timeout)
            return True
            
        except Exception as e:
            self.AAXW_CLASS_LOGGER.error(f"Error during initialization: {e}\n{traceback.format_exc()}")
            if self._unified_client_loop:
                self._unified_client_loop.call_soon_threadsafe(self._unified_client_loop.stop)
            return False

    async def aClose(self):
        """异步关闭客户端，停止所有服务器并清理资源"""
        try:
            self.AAXW_CLASS_LOGGER.info("开始关闭客户端...")
            
            # 发送关闭信号
            if self._operation_queue:
                self.AAXW_CLASS_LOGGER.debug("发送shutdown信号到操作队列")
                await self._operation_queue.put({"type": "shutdown"})
            
            # 先关闭所有session的资源
            server_names = list(self.mcpClientSessions.keys())
            for name in reversed(server_names):
                try:
                    session = self.mcpClientSessions[name]
                    await session.aClose()
                except Exception as e:
                    self.AAXW_CLASS_LOGGER.error(f"Error closing session {name}: {e}")
                finally:
                    del self.mcpClientSessions[name]
            
            # 等待主任务完成
            if self._main_task:
                self.AAXW_CLASS_LOGGER.debug("等待主任务完成...")
                try:
                    await asyncio.wait_for(self._main_task, timeout=5.0)
                    self.AAXW_CLASS_LOGGER.debug("主任务已完成")
                except asyncio.TimeoutError:
                    self.AAXW_CLASS_LOGGER.warning("等待主任务超时")
                except Exception as e:
                    self.AAXW_CLASS_LOGGER.error(f"等待主任务时发生错误: {e}")

            # 最后关闭 ExitStack
            if self.exitStack:
                self.AAXW_CLASS_LOGGER.debug("关闭 ExitStack...")
                await self.exitStack.aclose()

            # 关闭事件循环
            if self._unified_client_loop and self._unified_client_loop.is_running():
                self.AAXW_CLASS_LOGGER.debug("准备停止事件循环...")
                
                # 使用 call_soon_threadsafe 确保在正确的线程中停止循环
                self._unified_client_loop.call_soon_threadsafe(self._unified_client_loop.stop)
                
                # 只有在非当前线程时才尝试join
                current_thread = threading.current_thread()
                if self._loop_thread and self._loop_thread.is_alive() and current_thread != self._loop_thread:
                    self.AAXW_CLASS_LOGGER.debug("等待事件循环线程结束...")
                    try:
                        self._loop_thread.join(timeout=3.0)
                        self.AAXW_CLASS_LOGGER.debug("事件循环线程已结束")
                    except Exception as e:
                        self.AAXW_CLASS_LOGGER.warning(f"等待事件循环线程时发生错误: {e}")

            #
            # Windows Proactor 事件循环的特殊处理
            # 否则会卡主；
            if sys.platform == 'win32' and isinstance(self._unified_client_loop, asyncio.ProactorEventLoop):
                self.AAXW_CLASS_LOGGER.debug("Windows Proactor事件循环特殊处理...")
                with contextlib.suppress(ValueError, RuntimeError):
                    self._unified_client_loop.close()

        except Exception as e:
            self.AAXW_CLASS_LOGGER.error(f"关闭客户端时发生错误: {e}\n{traceback.format_exc()}")
            raise
        finally:
            self.AAXW_CLASS_LOGGER.debug("清理资源引用...")
            # 清理所有引用
            self._initialized.clear()
            self._main_task = None
            self._unified_client_loop = None
            self._loop_thread = None
            self._operation_queue = None
            self.mcpClientSessions.clear()
            self.AAXW_CLASS_LOGGER.info("客户端关闭完成")

    def close(self):
        """同步关闭客户端"""
        try:
            future = self._run_coro_and_get_future(self.aClose())
            future.result(timeout=10.0)  # 增加超时时间
        except TimeoutError:
            self.AAXW_CLASS_LOGGER.warning("Timeout during synchronous close")
        except Exception as e:
            self.AAXW_CLASS_LOGGER.error(f"Error during synchronous close: {e}\n{traceback.format_exc()}")
            raise

    def startServer(self, serverName: str, timeout: float = 5.0) -> bool:
        """同步启动服务器"""
        if not self._initialized.is_set():
            raise RuntimeError("Client not initialized")
            
        try:
            future = self.afStartServer(serverName)
            return future.result(timeout=timeout)
        except Exception as e:
            self.AAXW_CLASS_LOGGER.error(f"Error starting server {serverName}: {e}\n{traceback.format_exc()}")
            return False

    def stopServer(self, serverName: str, timeout: float = 5.0) -> bool:
        """同步停止服务器"""
        if not self._initialized.is_set():
            raise RuntimeError("Client not initialized")
            
        try:
            future = self.afStopServer(serverName)
            return future.result(timeout=timeout)
        except Exception as e:
            self.AAXW_CLASS_LOGGER.error(f"Error stopping server {serverName}: {e}\n{traceback.format_exc()}")
            return False

    def stopAllServers(self, timeout: float = 5.0) -> bool:
        """同步停止所有服务器
        
        Args:
            timeout: 停止超时时间(秒)
            
        Returns:
            bool: 是否全部停止成功
        """
        if not self._initialized.is_set():
            raise RuntimeError("Client not initialized")
            
        try:
            # 获取服务器名称列表并反转，确保最后创建的先关闭
            server_names = list(self.mcpClientSessions.keys())
            server_names.reverse()
            
            for serverName in server_names:
                if not self.stopServer(serverName, timeout=timeout):
                    return False
            return True
        except Exception as e:
            self.AAXW_CLASS_LOGGER.error(f"Error stopping all servers: {e}\n{traceback.format_exc()}")
            return False

    def listTools(self, serverName: str, timeout: float = 5.0) -> List[types.Tool]:
        """同步获取服务器工具列表
        
        Args:
            serverName: 服务器名称
            timeout: 超时时间(秒)
            
        Returns:
            List[types.Tool]: 工具列表
        """
        if not self._initialized.is_set():
            raise RuntimeError("Client not initialized")
            
        future = self.afListTools(serverName)
        return future.result(timeout=timeout)

    def afListTools(self, serverName: str) -> Future:
        """异步获取服务器工具列表，返回Future"""
        if not self._unified_client_loop:
            raise RuntimeError("Client not initialized")
        
        serverSession = self.mcpClientSessions.get(serverName)
        if not serverSession:
            raise ValueError(f"Server {serverName} is not running")
        
        return self._run_coro_and_get_future(serverSession.aListTools())

    def callTool(self, serverName: str, toolName: str, args: Dict[str, Any], 
                 timeout: float = 10.0) -> Any:
        """同步调用工具
        
        Args:
            serverName: 服务器名称
            toolName: 工具名称
            args: 工具参数
            timeout: 超时时间(秒)
            
        Returns:
            Any: 工具调用结果
        """
        if not self._initialized.is_set():
            raise RuntimeError("Client not initialized")
            
        future = self.afCallTool(serverName, toolName, args)
        return future.result(timeout=timeout)

    def afCallTool(self, serverName: str, toolName: str, args: Dict[str, Any]) ->Future:
        """异步调用工具，返回Future
        
        Args:
            serverName: 服务器名称
            toolName: 工具名称
            args: 工具参数
            
        Returns:
            Future: 异步操作的Future对象
        """
        if not self._unified_client_loop:
            raise RuntimeError("Client not initialized")
            
        serverSession = self.mcpClientSessions.get(serverName)
        if not serverSession:
            raise ValueError(f"Server {serverName} is not running")
            
        return self._run_coro_and_get_future(serverSession.aCallTool(toolName, args))

    def getConfiguredServers(self) -> List[str]:
        """获取配置文件中所有可用的服务器名称列表"""
        return list(self.config["mcpServers"].keys())

    def getServerInfo(self, serverName: str) -> Optional[Dict[str, Any]]:
        """获取指定服务器的信息"""
        serverSession = self.mcpClientSessions.get(serverName)
        if serverSession:
            return serverSession.getConnectionInfo()
        return None

    def sendPing(self, serverName: str, timeout: float = 5.0) -> bool:
        """同步发送ping请求到指定服务器
        
        Args:
            serverName: 目标服务器名称
            timeout: 超时时间(秒)
            
        Returns:
            bool: ping是否成功
        """
        if not self._initialized.is_set():
            raise RuntimeError("Client not initialized")
            
        try:
            future = self.afSendPing(serverName)
            return future.result(timeout=timeout)
        except ResourceWarning as rw:
            self.AAXW_CLASS_LOGGER.warning(f"Failed sending ping to server {serverName} , ResourceWarning:{rw}") 
            return False
        except anyio.ClosedResourceError as cre:
            self.AAXW_CLASS_LOGGER.warning(f"Failed sending ping to server {serverName} , ClosedResourceError:{cre}") 
            return False
        except Exception as e:
            self.AAXW_CLASS_LOGGER.warning(f"Error sending ping to server {serverName}: {e}\n{traceback.format_exc()}")
            return False

    def afSendPing(self, serverName: str) -> Future:
        """异步发送ping请求到指定服务器，返回Future
        
        Args:
            serverName: 目标服务器名称
            
        Returns:
            Future: 异步操作的Future对象
        """
        if not self._unified_client_loop:
            raise RuntimeError("Client not initialized")
            
        session = self.mcpClientSessions.get(serverName)
        if not session:
            raise ResourceWarning(f"Server {serverName} is not running")
            
        return self._run_coro_and_get_future(session.aPing())

async def cmdInteractServerMonitor(client: McpClient, serverName: str):
    """交互式服务器监控"""
    print(f"开始监控服务器 {serverName}")
    print("按 Ctrl+C 停止监控")
    
    # 获取session
    session = client.mcpClientSessions.get(serverName)
    if not session:
        print(f"错误: 服务器 {serverName} 未连接")
        return
        
    try:
        while True:
            try:
                await session.aPing()
                print(f"[心跳检测] {serverName} ping 成功")
            except Exception as e:
                print(f"[心跳检测] {serverName} ping 失败: {e}")
                client.AAXW_CLASS_LOGGER.error(f"Error in server monitor ping: {e}\n{traceback.format_exc()}")
            await asyncio.sleep(3)
    except asyncio.CancelledError:
        print(f"停止监控服务器 {serverName}")
    except Exception as e:
        print(f"监控服务器出错: {e}")
        client.AAXW_CLASS_LOGGER.error(f"Error in server monitor: {e}\n{traceback.format_exc()}")

async def cmdInteract(client: McpClient):
    """命令行交互界面"""
    # 初始化客户端
    if not client.initialize(timeout=10.0):
        print("Failed to initialize client")
        return
        
    try:
        while True:
            print("\nMCP Client Commands:")
            print("1. List available servers")
            print("2. Start server")
            print("3. Stop server")
            print("4. Stop all servers")
            print("5. List server tools")
            print("6. Call tool")
            print("7. Monitor server")
            print("8. Exit")
            
            choice = input("\nEnter your choice (1-8): ")
            
            try:
                if choice == "1":
                    servers = client.getConfiguredServers()
                    print("\nAvailable servers:")
                    for server in servers:
                        info = client.getServerInfo(server)
                        status = "running" if info else "stopped"
                        print(f"- {server} ({status})")
                
                elif choice == "2":
                    serverName = input("Enter server name to start: ")
                    if serverName not in client.config["mcpServers"]:
                        print(f"错误: 服务器 {serverName} 未在配置中")
                        continue
                        
                    serverConfig = client.config["mcpServers"][serverName]
                    session = McpClientSession(serverName, serverConfig, client)
                    client.mcpClientSessions[serverName] = session
                    await session.aInitialize(client.exitStack)
                    print(f"Server {serverName} started successfully")
                
                elif choice == "3":
                    serverName = input("Enter server name to stop: ")
                    session = client.mcpClientSessions.get(serverName)
                    if not session:
                        print(f"错误: 服务器 {serverName} 未连接")
                        continue
                        
                    await session.aClose()
                    del client.mcpClientSessions[serverName]
                    print(f"Server {serverName} stopped successfully")
                
                elif choice == "4":
                    for serverName in list(client.mcpClientSessions.keys()):
                        session = client.mcpClientSessions[serverName]
                        await session.aClose()
                        del client.mcpClientSessions[serverName]
                    print("All servers stopped successfully")
                
                elif choice == "5":
                    serverName = input("Enter server name: ")
                    session = client.mcpClientSessions.get(serverName)
                    if not session:
                        print(f"错误: 服务器 {serverName} 未连接")
                        continue
                        
                    tools = await session.aListTools()
                    print("\nAvailable tools:")
                    for tool in tools:
                        print(f"- {tool.name}: {tool.description}")
                
                elif choice == "6":
                    serverName = input("Enter server name: ")
                    session = client.mcpClientSessions.get(serverName)
                    if not session:
                        print(f"错误: 服务器 {serverName} 未连接")
                        continue
                        
                    toolName = input("Enter tool name: ")
                    argsStr = input("Enter arguments (key1=value1 key2=value2): ")
                    args = dict(arg.split('=') for arg in argsStr.split() if '=' in arg)
                    result = await session.aCallTool(toolName, args)
                    print(f"Result: {result}")
                
                elif choice == "7":
                    serverName = input("Enter server name to monitor: ")
                    try:
                        # 创建监控任务
                        monitor_task = asyncio.create_task(cmdInteractServerMonitor(client, serverName))
                        # 等待用户按Ctrl+C
                        await monitor_task
                    except KeyboardInterrupt:
                        print("\nMonitoring stopped")
                        monitor_task.cancel()
                        try:
                            await monitor_task
                        except asyncio.CancelledError:
                            pass
                
                elif choice == "8":
                    print("Exiting...")
                    # 关闭所有会话
                    for serverName in list(client.mcpClientSessions.keys()):
                        session = client.mcpClientSessions[serverName]
                        await session.aClose()
                    break
                
            except Exception as e:
                print(f"Error: {e}")
                client.AAXW_CLASS_LOGGER.error(f"Error in command execution: {e}\n{traceback.format_exc()}")
    finally:
        # 确保关闭客户端
        client.close()


if __name__ == "__main__":
    import argparse
    
    # 默认配置
    defaultConfig=None
    # defaultConfig = {
    #     "mcpServers": {
    #         "test_server": {
    #             "command": "python",
    #             "args": ["test_server.py"]
    #         },
    #         "echo_server": {
    #             "command": "python",
    #             "args": ["echo_server.py"]
    #         }
    #     }
    # }
    
    # 命令行参数解析器
    parser = argparse.ArgumentParser(description='MCP Client CLI')
    parser.add_argument('--config', default='mcp.json',
                      help='Path to config file')
    
    args = parser.parse_args()

    async def main():
        client = None
        try:
            # 创建客户端实例
            client = McpClient(configPath=args.config, configContentDict=defaultConfig)
            # 运行交互式命令行界面
            await cmdInteract(client)
        except KeyboardInterrupt:
            print("\nReceived keyboard interrupt, shutting down...")
        except Exception as e:
            print(f"\nError: {e}")
            AAXW_JUMPIN_MODULE_LOGGER.error(f"Error in main: {e}\n{traceback.format_exc()}")
        finally:
            # 确保关闭所有资源
            if client:
                for serverName in list(client.mcpClientSessions.keys()):
                    try:
                        session = client.mcpClientSessions[serverName]
                        await session.aClose()
                    except Exception as e:
                        AAXW_JUMPIN_MODULE_LOGGER.error(f"Error closing session {serverName}: {e}\n{traceback.format_exc()}")
                client.close()
            print("Program terminated.")

    # asyncio.run(main())

    # 设置日志级别
    # logging.basicConfig(level=logging.DEBUG)
    logging.basicConfig(level=logging.INFO)
    AAXW_JUMPIN_MODULE_LOGGER.setLevel(logging.DEBUG)
    try:
        # 1. 创建客户端并初始化
        AAXW_JUMPIN_MODULE_LOGGER.info("Creating MCP client...")
        client = McpClient("./mcp.json")
        if not client.initialize():
            AAXW_JUMPIN_MODULE_LOGGER.error("Failed to initialize client")
            exit(1)
        
        # 2. 获取所有配置的服务器
        servers = client.getConfiguredServers()
        AAXW_JUMPIN_MODULE_LOGGER.info(f"Configured servers: {servers}")
        
        # 3. 测试第一个服务器
        test_server = servers[2]
        AAXW_JUMPIN_MODULE_LOGGER.info(f"Testing server: {test_server}")
        
        try:
            # 4. 启动服务器
            AAXW_JUMPIN_MODULE_LOGGER.info(f"Starting server {test_server}...")
            if not client.startServer(test_server):
                AAXW_JUMPIN_MODULE_LOGGER.error(f"Failed to start server {test_server}")
            AAXW_JUMPIN_MODULE_LOGGER.info(f"Server {test_server} started successfully")
            
            # 5. 获取工具列表
            time.sleep(2)
            AAXW_JUMPIN_MODULE_LOGGER.info(f"Listing tools for server {test_server}...")
            tools = client.listTools(test_server)
            AAXW_JUMPIN_MODULE_LOGGER.info(f"Available tools: {tools}")
            
            # 6. 等待3秒
            AAXW_JUMPIN_MODULE_LOGGER.info("Waiting for 3 seconds...")
            time.sleep(3)
            
            # 7. 停止服务器
            AAXW_JUMPIN_MODULE_LOGGER.info(f"Stopping server {test_server}...")
            if not client.stopServer(test_server):
                AAXW_JUMPIN_MODULE_LOGGER.error(f"Failed to stop server {test_server}")
            AAXW_JUMPIN_MODULE_LOGGER.info(f"Server {test_server} stopped successfully")
            
        finally:
            # 8. 关闭客户端
            AAXW_JUMPIN_MODULE_LOGGER.info("Closing client...")
            client.close()
            AAXW_JUMPIN_MODULE_LOGGER.info("Client closed")
            
    except Exception as e:
        AAXW_JUMPIN_MODULE_LOGGER.error(f"Test failed with error: {e}", exc_info=True)
        exit(1)