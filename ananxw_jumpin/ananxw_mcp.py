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
#  MCP( Model Context Protocol) 实现
#  MCP 客户端框架实现
#  @TODO MCP 服务端框架实现
#  

import json
import sys
import asyncio
import os
from typing import Dict, Any, Optional, Tuple, List
from contextlib import AsyncExitStack
from mcp import ClientSession, StdioServerParameters, types
from mcp.client.stdio import stdio_client
from mcp.client.sse import sse_client
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ServerConnection:
    """表示单个MCP服务器连接的类"""
    
    def __init__(self, serverName: str, serverConfig: Dict[str, Any]):
        self.serverName = serverName
        self.serverConfig = serverConfig
        self.mcpSession: Optional[ClientSession] = None
        self.transportInstance: Optional[Any] = None
        self.transportType: Optional[str] = None
        self.availableTools: List[Dict[str, Any]] = []
        
    def __str__(self):
        return f"Server({self.serverName}, transport={self.transportType or 'not_connected'}, connected={self.mcpSession is not None})"

    def getConnectionInfo(self) -> Dict[str, Any]:
        """获取连接信息"""
        return {
            "serverName": self.serverName,
            "transportType": self.transportType,
            "isConnected": self.mcpSession is not None,
            "availableToolCount": len(self.availableTools)
        }

class McpClient:
    """统一的MCP客户端实现"""
    
    def __init__(self, configPath: str= "mcp.json", configContentDict: Optional[Dict[str, Any]] = None):
        """
        初始化MCP客户端
        
        Args:
            configPath: 配置文件路径,如果为None且configContentDict也为None,则使用默认路径"mcp.json"
            configContentDict: 配置内容字典,如果提供则优先使用此配置
        """
        self.configPath = configPath
        self.serverConnections: Dict[str, ServerConnection] = {}
        self.exitStack = AsyncExitStack()
        
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
            return {}  # 返回空配置而不是退出

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

    async def startServer(self, serverName: str) -> None:
        """启动指定的MCP服务器并建立连接"""
        if serverName not in self.config["mcpServers"]:
            logger.error(f"Server {serverName} not found in config")
            return

        serverConfig = self.config["mcpServers"][serverName]
        try:
            # 创建服务器连接对象
            serverConnection = ServerConnection(serverName, serverConfig)
            self.serverConnections[serverName] = serverConnection
            
            # 根据配置创建相应的传输
            transport = None
            if "command" in serverConfig:
                transport = await self._createStdioTransport(serverConfig)
                serverConnection.transportType = "stdio"
            elif "url" in serverConfig:
                transport = await self._createSseTransport(serverConfig)
                serverConnection.transportType = "sse"
            else:
                raise ValueError(f"Invalid server configuration for {serverName}")
                
            readStream, writeStream = transport
            mcpSession = await self.exitStack.enter_async_context(
                ClientSession(readStream, writeStream)
            )
            await mcpSession.initialize()
            
            serverConnection.mcpSession = mcpSession
            serverConnection.transportInstance = transport
            serverConnection.availableTools = (await mcpSession.list_tools()).tools
            
            logger.info(f"Connected to server: {serverConnection}")
            logger.info("Available tools:")
            for tool in serverConnection.availableTools:
                logger.info(f"- {tool.name}: {tool.description}")

        except Exception as e:
            logger.error(f"Error starting server {serverName}: {e}")
            if serverName in self.serverConnections:
                await self.stopServer(serverName)

    async def stopServer(self, serverName: str) -> None:
        """停止指定的MCP服务器"""
        if serverName in self.serverConnections:
            try:
                serverConnection = self.serverConnections[serverName]
                if serverConnection.mcpSession:
                    serverConnection.mcpSession = None
                del self.serverConnections[serverName]
                logger.info(f"Stopped server: {serverName}")
            except Exception as e:
                logger.error(f"Error stopping server {serverName}: {e}")

    async def stopAllServers(self) -> None:
        """停止所有运行的服务器"""
        try:
            self.serverConnections.clear()
            await self.exitStack.aclose()
            self.exitStack = AsyncExitStack()
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

    def getAvailableServers(self) -> List[str]:
        """获取配置文件中所有可用的服务器名称列表"""
        return list(self.config["mcpServers"].keys())

    def getServerInfo(self, serverName: str) -> Optional[Dict[str, Any]]:
        """获取指定服务器的信息"""
        serverConnection = self.serverConnections.get(serverName)
        if serverConnection:
            return serverConnection.getConnectionInfo()
        return None

    async def listTools(self, serverName: str) -> List[Dict[str, Any]]:
        """获取指定服务器的可用工具列表"""
        serverConnection = self.serverConnections.get(serverName)
        if not serverConnection or not serverConnection.mcpSession:
            raise ValueError(f"Server {serverName} is not running")
        toolsResponse = await serverConnection.mcpSession.list_tools()
        
        # 打印完整的工具信息
        for tool in toolsResponse.tools: #mcp.types.Tool
            logger.info(f"\nTool: {tool.name}")
            logger.info(f"Description: {tool.description}")
            if hasattr(tool, 'inputSchema'):
                inputSchema: Dict[str, Any] = tool.inputSchema
                logger.info(f"schema: {inputSchema}")
            if hasattr(tool, 'annotations'):
                annotations: Dict[str, Any] = tool.annotations
                logger.info(f"annotations: {annotations}")
            
        return toolsResponse.tools

    async def callTool(self, serverName: str, toolName: str, args: Dict[str, Any]) -> Any:
        """调用指定服务器的指定工具"""
        serverConnection = self.serverConnections.get(serverName)
        if not serverConnection or not serverConnection.mcpSession:
            raise ValueError(f"Server {serverName} is not running")
        return await serverConnection.mcpSession.call_tool(toolName, args)

    async def sendPing(self, serverName: str) -> None:
        """向指定服务器发送ping请求"""
        serverConnection = self.serverConnections.get(serverName)
        if not serverConnection or not serverConnection.mcpSession:
            raise ValueError(f"Server {serverName} is not running")
        await serverConnection.mcpSession.send_ping()

    async def getToolDetails(self, serverName: str, toolName: str) -> Dict[str, Any]:
        """获取指定工具的详细信息"""
        serverConnection = self.serverConnections.get(serverName)
        if not serverConnection or not serverConnection.mcpSession:
            raise ValueError(f"Server {serverName} is not running")
        
        tools = await serverConnection.mcpSession.list_tools()
        for tool in tools.tools:
            if tool.name == toolName:
                return {
                    "name": tool.name,
                    "description": tool.description,
                    "schema": getattr(tool, 'schema', {}),
                    "parameters": getattr(tool, 'parameters', {}),
                    "metadata": getattr(tool, 'metadata', {})
                }
        raise ValueError(f"Tool {toolName} not found")

async def cmdInteractServerMonitor(client: McpClient, serverName: str):
    """交互式服务器监控"""
    print(f"开始监控服务器 {serverName}")
    print("按 Ctrl+C 停止监控")
    
    try:
        while True:
            try:
                await client.sendPing(serverName)
                print(f"[心跳检测] {serverName} ping 成功")
            except Exception as e:
                print(f"[心跳检测] {serverName} ping 失败: {e}")
            await asyncio.sleep(3)
    except asyncio.CancelledError:
        print(f"停止监控服务器 {serverName}")

async def cmdInteract(client: McpClient):
    """命令行交互界面"""
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
                servers = client.getAvailableServers()
                print("\nAvailable servers:")
                for server in servers:
                    info = client.getServerInfo(server)
                    status = "running" if info else "stopped"
                    print(f"- {server} ({status})")
            
            elif choice == "2":
                serverName = input("Enter server name to start: ")
                await client.startServer(serverName)
            
            elif choice == "3":
                serverName = input("Enter server name to stop: ")
                await client.stopServer(serverName)
            
            elif choice == "4":
                await client.stopAllServers()
            
            elif choice == "5":
                serverName = input("Enter server name: ")
                tools = await client.listTools(serverName)
                print("\nAvailable tools:")
                for tool in tools:
                    print(f"- {tool.name}: {tool.description}")
            
            elif choice == "6":
                serverName = input("Enter server name: ")
                toolName = input("Enter tool name: ")
                argsStr = input("Enter arguments (key1=value1 key2=value2): ")
                args = dict(arg.split('=') for arg in argsStr.split() if '=' in arg)
                result = await client.callTool(serverName, toolName, args)
                print(f"Result: {result}")
            
            elif choice == "7":
                serverName = input("Enter server name to monitor: ")
                try:
                    await cmdInteractServerMonitor(client, serverName)
                except KeyboardInterrupt:
                    print("\nMonitoring stopped")
            
            elif choice == "8":
                print("Exiting...")
                await client.stopAllServers()
                break
            
        except Exception as e:
            print(f"Error: {e}")

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
    
    try:
        # 创建客户端实例
        # 调试时可以直接使用默认配置
        client = McpClient(configPath=args.config,configContentDict=defaultConfig)
        # 或者使用配置文件
        # client = McpClient(configPath=args.config)
        
        # 运行交互式命令行界面
        asyncio.run(cmdInteract(client))
    except KeyboardInterrupt:
        print("\nReceived keyboard interrupt, shutting down...")
    except Exception as e:
        print(f"\nError: {e}")
    finally:
        print("Program terminated.")