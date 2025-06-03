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
# import concurrent.futures
from concurrent.futures import TimeoutError, Future
from typing import Dict, Any, Optional, Tuple, List
from contextlib import AsyncExitStack
from mcp import ClientSession, StdioServerParameters, types
from mcp.client.stdio import stdio_client
from mcp.client.sse import sse_client
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class McpClientSession:
    """表示MCP客户端中的一个服务器会话，管理与目标服务器的通信。
    适配了sse与stdio的实现。
    """
    
    def __init__(self, targetServerName: str, targetServerConfig: Dict[str, Any], mcpClient: 'McpClient'):
        self.targetServerName = targetServerName
        self.targetServerConfig = targetServerConfig
        self.mcpClient = mcpClient
        self.mcpSession: Optional[ClientSession] = None
        self.transportInstance: Optional[Any] = None
        self.transportType: Optional[str] = None
        self.availableTools: List[Dict[str, Any]] = []
        self._initialized = threading.Event()
        self.exitStack = AsyncExitStack()
        
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
        return await self.exitStack.enter_async_context(stdio_client(server_params))

    async def _createSseTransport(self, config: Dict[str, Any]) -> Tuple[Any, Any]:
        """创建SSE传输"""
        return await self.exitStack.enter_async_context(
            sse_client(
                url=config["url"],
                headers={"Accept": "text/event-stream"},
                timeout=5.0,
                sse_read_timeout=300.0
            )
        )

    async def aInitialize(self):
        """异步初始化会话连接"""
        try:
            if "command" in self.targetServerConfig:
                self.transportType = "stdio"
                self.transportInstance = await self._createStdioTransport(self.targetServerConfig)
            elif "url" in self.targetServerConfig:
                self.transportType = "sse"
                self.transportInstance = await self._createSseTransport(self.targetServerConfig)
            else:
                raise ValueError(f"Invalid server configuration for {self.targetServerName}")

            readStream, writeStream = self.transportInstance
            self.mcpSession = await self.exitStack.enter_async_context(
                ClientSession(readStream, writeStream)
            )
            await self.mcpSession.initialize()
            
            self.availableTools = (await self.mcpSession.list_tools()).tools
            self._initialized.set()
            
            logger.info(f"Connected to server: {self}")
            logger.info("Available tools:")
            for tool in self.availableTools:
                logger.info(f"- {tool.name}: {tool.description}")
                
        except Exception as e:
            logger.error(f"Error initializing server {self.targetServerName}: {e}")
            raise

    async def aClose(self):
        """异步关闭会话连接"""
        try:
            if self.mcpSession:
                self.mcpSession = None
            if self.transportInstance:
                self.transportInstance = None
            await self.exitStack.aclose()
            self._initialized.clear()
        except Exception as e:
            logger.error(f"Error closing server {self.targetServerName}: {e}")
            raise

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

    async def aPing(self) -> bool:
        """异步发送ping请求到目标服务器
        
        Returns:
            bool: ping是否成功
        """
        if not self.mcpSession:
            raise ValueError(f"Server {self.targetServerName} is not running")
        try:
            await self.mcpSession.ping()
            return True
        except Exception as e:
            logger.error(f"Error pinging server {self.targetServerName}: {e}")
            return False

class McpClient:
    """统一的MCP客户端实现"""
    
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
        
        # 优先使用传入的配置内容
        if configContentDict is not None:
            self.config = configContentDict
        else:
            self.config = self._loadConfig()

    def _loadConfig(self) -> Dict[str, Any]:
        """加载配置文件"""
        try:
            with open(self.configPath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading config file: {e}")
            return {}

    def _run_event_loop(self):
        """在后台运行事件循环"""
        asyncio.set_event_loop(self._unified_client_loop)
        self._unified_client_loop.run_forever()

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
            
            # 启动事件循环的后台线程
            self._loop_thread = threading.Thread(target=self._run_event_loop)
            self._loop_thread.daemon = True
            self._loop_thread.start()
            
            future = self._run_coro_and_get_future(self.exitStack.__aenter__())
            future.result(timeout=timeout)
            self._initialized.set()
            return True
            
        except Exception as e:
            logger.error(f"Error during initialization: {e}")
            logger.error(traceback.format_exc())
            if self._unified_client_loop:
                self._unified_client_loop.call_soon_threadsafe(self._unified_client_loop.stop)
            return False

    def close(self, timeout: float = 5.0):
        """同步关闭客户端
        
        Args:
            timeout: 关闭超时时间(秒)
        """
        try:
            if not self._unified_client_loop:
                return
                
            future = self._run_coro_and_get_future(self.aClose())
            future.result(timeout=timeout)
            
            self._unified_client_loop.call_soon_threadsafe(self._unified_client_loop.stop)
            if self._loop_thread:
                self._loop_thread.join(timeout=timeout)
                
        except Exception as e:
            logger.error(f"Error during close: {e}")
            logger.error(traceback.format_exc())
        finally:
            self._initialized.clear()
            self._unified_client_loop = None
            self._loop_thread = None

    async def aClose(self):
        """异步关闭客户端"""
        try:
            for serverName in list(self.mcpClientSessions.keys()):
                await self.aStopServer(serverName)
            await self.exitStack.aclose()
        except Exception as e:
            logger.error(f"Error during async close: {e}")
            raise

    def startServer(self, serverName: str, timeout: float = 5.0) -> bool:
        """同步启动服务器
        
        Args:
            serverName: 服务器名称
            timeout: 启动超时时间(秒)
            
        Returns:
            bool: 是否启动成功
        """
        if not self._initialized.is_set():
            raise RuntimeError("Client not initialized")
            
        try:
            future = self.afStartServer(serverName)
            future.result(timeout=timeout)
            return True
        except Exception as e:
            logger.error(f"Error starting server {serverName}: {e}")
            return False

    def afStartServer(self, serverName: str) -> Future:
        """异步启动服务器，返回Future
        
        Args:
            serverName: 服务器名称
            
        Returns:
            Future: 异步操作的Future对象
        """
        if not self._unified_client_loop:
            raise RuntimeError("Client not initialized")
            
        if serverName not in self.config["mcpServers"]:
            raise ValueError(f"Server {serverName} not found in config")

        serverConfig = self.config["mcpServers"][serverName]
        serverSession = McpClientSession(serverName, serverConfig, self)
        self.mcpClientSessions[serverName] = serverSession
        return self._run_coro_and_get_future(serverSession.aInitialize())

    def stopServer(self, serverName: str, timeout: float = 5.0) -> bool:
        """同步停止服务器
        
        Args:
            serverName: 服务器名称
            timeout: 停止超时时间(秒)
            
        Returns:
            bool: 是否停止成功
        """
        if not self._initialized.is_set():
            raise RuntimeError("Client not initialized")
            
        try:
            future = self.afStopServer(serverName)
            future.result(timeout=timeout)
            return True
        except Exception as e:
            logger.error(f"Error stopping server {serverName}: {e}")
            return False

    def afStopServer(self, serverName: str) -> Future:
        """异步停止服务器，返回Future
        
        Args:
            serverName: 服务器名称
            
        Returns:
            Future: 异步操作的Future对象
        """
        if not self._unified_client_loop:
            raise RuntimeError("Client not initialized")
            
        serverSession = self.mcpClientSessions.get(serverName)
        if not serverSession:
            raise ValueError(f"Server {serverName} is not running")
            
        async def _stop_server():
            await serverSession.aClose()
            del self.mcpClientSessions[serverName]
                
        return self._run_coro_and_get_future(_stop_server())

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
            future = self.afStopAllServers()
            future.result(timeout=timeout)
            return True
        except Exception as e:
            logger.error(f"Error stopping all servers: {e}")
            return False

    def afStopAllServers(self) -> Future:
        """异步停止所有服务器，返回Future
        
        Returns:
            Future: 异步操作的Future对象
        """
        if not self._unified_client_loop:
            raise RuntimeError("Client not initialized")
            
        async def _stop_all_servers():
            for serverName in list(self.mcpClientSessions.keys()):
                await self.afStopServer(serverName)
                
        return self._run_coro_and_get_future(_stop_all_servers())

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
        except Exception as e:
            logger.error(f"Error sending ping to server {serverName}: {e}")
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
            raise ValueError(f"Server {serverName} is not running")
            
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
            await asyncio.sleep(3)
    except asyncio.CancelledError:
        print(f"停止监控服务器 {serverName}")

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
                    await session.aInitialize()
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
            logger.error(f"Error in main: {e}", exc_info=True)
        finally:
            # 确保关闭所有资源
            if client:
                for serverName in list(client.mcpClientSessions.keys()):
                    try:
                        session = client.mcpClientSessions[serverName]
                        await session.aClose()
                    except Exception as e:
                        logger.error(f"Error closing session {serverName}: {e}")
                client.close()
            print("Program terminated.")

    asyncio.run(main())