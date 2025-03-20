#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""ANANXW Jumpin API层"""

from typing import Optional, List, Dict, Any, Union, Callable, Tuple
from .comm import AAXWDependencyContainer
from .backbone import (
    AAXWJumpinConfig, 
    AAXWJumpinHistoriedMemory,
    AAXWJumpinFileAIMemoryManager,
    AAXWJumpinPluginManager,
    AAXWJumpinAppletManager,
    ConfigurableAIConnOrAgent
)

class JumpinAPI:
    """ANANXW Jumpin API层，集中管理所有核心服务"""
    
    def __init__(self, dependency_container: AAXWDependencyContainer):
        self.container = dependency_container
        
    # AI服务接口
    def send_message(self, message: str, callback: Callable, stream: bool = True):
        """发送消息并通过回调接收响应"""
        ai_connector = self.container.get("configurableAIConnOrAgent")
        ai_connector.requestAndCallback(message, callback, stream)
        
    def get_available_models(self) -> List[str]:
        """获取可用模型列表"""
        ai_connector = self.container.get("configurableAIConnOrAgent")
        return ai_connector.getAvailableModels()
    
    def switch_model(self, model_name: str) -> bool:
        """切换AI模型"""
        ai_connector = self.container.get("configurableAIConnOrAgent")
        return ai_connector.switchModel(model_name)
    
    # 内存管理接口
    def list_memories(self, offset: int = 0, limit: int = 10) -> List[str]:
        """列出记忆"""
        memory_manager = self.container.get("jumpinAIMemoryManager")
        return memory_manager.listMemoryNames(offset, limit)
    
    def load_memory(self, memory_id: str) -> AAXWJumpinHistoriedMemory:
        """加载指定记忆"""
        memory_manager = self.container.get("jumpinAIMemoryManager")
        return memory_manager.loadOrCreateMemory(memory_id)
    
    def delete_memory(self, memory_id: str):
        """删除指定记忆"""
        memory_manager = self.container.get("jumpinAIMemoryManager")
        memory_manager.deleteMemory(memory_id)
    
    def rename_memory(self, old_id: str, new_id: str) -> bool:
        """重命名记忆"""
        memory_manager = self.container.get("jumpinAIMemoryManager")
        return memory_manager.renameMemory(old_id, new_id)
    
    # 插件管理接口
    def list_plugins(self) -> List[str]:
        """列出所有插件"""
        plugin_manager = self.container.get("jumpinPluginManager")
        return plugin_manager.listPluginBuilderNames()
    
    def list_installed_plugins(self) -> List[str]:
        """列出已安装的插件"""
        plugin_manager = self.container.get("jumpinPluginManager")
        return plugin_manager.listInstalledPluginNames()
    
    def install_plugin(self, plugin_id: str) -> bool:
        """安装插件"""
        plugin_manager = self.container.get("jumpinPluginManager")
        return plugin_manager.installPlugin(plugin_id)
    
    def uninstall_plugin(self, plugin_id: str) -> bool:
        """卸载插件"""
        plugin_manager = self.container.get("jumpinPluginManager")
        return plugin_manager.uninstallPlugin(plugin_id)
    
    def enable_plugin(self, plugin_id: str) -> bool:
        """启用插件"""
        plugin_manager = self.container.get("jumpinPluginManager")
        return plugin_manager.enablePlugin(plugin_id)
    
    def disable_plugin(self, plugin_id: str) -> bool:
        """禁用插件"""
        plugin_manager = self.container.get("jumpinPluginManager")
        return plugin_manager.disablePlugin(plugin_id)
    
    # Applet管理接口
    def list_applets(self) -> List[Tuple[str, str]]:
        """列出所有Applet"""
        applet_manager = self.container.get("jumpinAppletManager")
        return applet_manager.listAppletsNamesAndTitles()
    
    def activate_applet(self, index: int) -> bool:
        """激活指定Applet"""
        applet_manager = self.container.get("jumpinAppletManager")
        return applet_manager.activateApplet(index)
    
    def activate_next_applet(self) -> bool:
        """激活下一个Applet"""
        applet_manager = self.container.get("jumpinAppletManager")
        return applet_manager.activateNextLoop()
    
    def get_applet_by_name(self, name: str) -> List[Any]:
        """获取指定名称的Applet实例"""
        applet_manager = self.container.get("jumpinAppletManager")
        return applet_manager.getApplet(name)
    
    # 配置管理接口
    def get_config(self) -> AAXWJumpinConfig:
        """获取配置实例"""
        return self.container.get("jumpinConfig")
    
    def reload_config(self):
        """重新加载配置"""
        config = self.get_config()
        config.loadEnv()
        config.loadArgs()
        config.loadYaml()
        config.logConfig() 