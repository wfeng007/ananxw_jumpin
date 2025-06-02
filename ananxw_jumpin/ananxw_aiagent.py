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
# @Date:2025-02-06 23:02:50
# @Last Modified by:wfeng007
#
#
#  llm驱动的ai agent框架与实现类；基于langchain,langgraph的实现；
#
# 已实行驶入事件、推导循环（包含 感知、认知、思考、行动 ）整体过程。
# 已实现 tools 的调用。
# 已实现 基于lastEvent，lastResult的回路记忆模式。实现逐步推导处理的过程。
# 提供了Pattern的定义，但未使用。
# 提供了sensoryflex 的感觉-动作的直接链路来执行特定事件。
#   提供了事件级联与跟踪机制，提供了入口事件保持。当做外部请求的缓存保持。
# 
#
# TODO 日志打印调整；
# 


from typing import Dict,Type, TypedDict, Annotated, List, Optional, Callable, Any, Tuple, ClassVar
from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_core.runnables.config import RunnableConfig
from langchain_core.tools import BaseTool
from langchain_openai import ChatOpenAI
from langchain_core.tools import Tool
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain.memory import ConversationBufferMemory
from langgraph.graph import StateGraph, START, END
from langgraph.graph.state import CompiledStateGraph
from pydantic import BaseModel, Field
from dotenv import load_dotenv
import queue
import time
import os,sys,logging
import math
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
try:
    from typing import override
except ImportError:
    from typing_extensions import override
import threading
import traceback

# from regex import P

if __name__ == "__main__":
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)  # 插入到路径最前面

from ananxw_jumpin.ananxw_framework import AAXWLoggerManager,AAXWLoggerJsonFormatFilter
AAXW_AIAGENT_LOG_MGR = AAXWLoggerManager() 

AAXW_AIAGENT_MODULE_LOGGER:logging.Logger=AAXW_AIAGENT_LOG_MGR.getModuleLogger(
    sys.modules[__name__])

@dataclass
class AgentSensoryEvent:
    """感知事件基类"""
    # 事件类型常量定义
    INNER: ClassVar[str] = "INNER"      # 内部事件，如状态转换、内部处理等
    ENV: ClassVar[str] = "ENV"          # 环境事件，如系统命令、环境变化等
    MESSAGE: ClassVar[str] = "MESSAGE"  # 消息事件，如用户输入、对话等
    
    message: str                        # 事件消息内容
    eventType: str = MESSAGE            # 事件类型标识
    source: str = "user"                # 事件来源
    timestamp: datetime = field(default_factory=datetime.now)
    # 当前暂时 isSensoryReflex  只有MESSAGE类型使用，有对应action。
    isSensoryReflex: bool = False       # 是否为感觉反射事件，True时是要求跳过perceiving直接执行action
    # 入口事件完成标志，只对MESSAGE和ENV类型有意义
    isCompleted: bool = field(default=False)  # 标记事件是否已完成处理

    lastEvent: Optional['AgentSensoryEvent'] = field(default=None)  # 上一次事件
    lastResult: Optional[str] = field(default=None)  # 上一次执行结果
    # 入口事件，对外部请求的缓存引用
    entryEvent: Optional['AgentSensoryEvent'] = field(default=None)  # 关联的入口事件（MESSAGE或ENV类型）
    #TODO 当前暂时没想好 perceiving过程如何处理。 （1些细节，如果未被回调如何识别到？做动态代理做切面计数来实现？）
    callback: Optional[Callable[[str], None]] = field(default=None)  # 流式回调函数

    def markCompleted(self):
        """标记事件已完成处理"""
        self.isCompleted = True

    def getEventType(self) -> str:
        """获取事件类型"""
        return self.eventType
    
    def getEntryEvent(self) -> Optional['AgentSensoryEvent']:
        """获取入口事件
        
        返回顺序：
        1. 如果有保存的入口事件，返回该入口事件
        2. 如果当前事件是入口事件类型（MESSAGE或ENV），返回自身
        3. 否则返回None
        """
        if self.entryEvent is not None:
            return self.entryEvent
        if self.eventType in [self.MESSAGE, self.ENV]:
            return self
        return None

    #
    def toMarkdownStr(self) -> str:
        """返回markdown形式的字符串，使用 ## 作为标题"""
        lines = [
            "## 事件类型",
            self.eventType,
            "## 事件来源",
            self.source,
            "## 事件内容",
            self.message,
            "## 时间戳",
            self.timestamp.isoformat(),
            "## 上次执行结果",
            str(self.lastResult if self.lastResult else 'None'),
            "## 上次事件，作为Impression",
            self.lastEvent.toImpressionStr() if self.lastEvent else 'None'
        ]
        return "\n".join(lines)

    #印象形式(也兼容markdown)的字符串，用于回忆形式体现的上次事件
    def toImpressionStr(self) -> str:
        """返回属性序列化字符串，使用```包围，属性间换行"""
        lines = [
            f"eventType: {self.eventType}",
            f"source: {self.source}",
            f"message: {self.message}",
            f"timestamp: {self.timestamp.isoformat()}",
            f"lastResult: {self.lastResult if self.lastResult else 'None'}",
            #不含对上次的印象
            # f"lastEvent: {self.lastEvent.toImpressionStr() if self.lastEvent else 'None'}"
        ]
        return "```\n" + "\n".join(lines) + "\n```"

# TODO 考虑增加1st-order-logic的实现；提供1st-order指令的schema
class PerceivingOutput(BaseModel):
    """基础动作输出模型"""
    actionName: str = Field(description="执行的动作名称")
    nextActionName: str = Field(default="", description="下一步建议的动作名称")
    thought: str = Field(description="对当前情况的理解和计划")
    args: Dict[str, Any] = Field(default_factory=dict, description="动作调用的参数")

    # 使用类变量存储解析器实例
    _parser: ClassVar[PydanticOutputParser] = None

    @classmethod
    def getParser(cls) -> PydanticOutputParser:
        """获取输出解析器（延迟初始化）"""
        if cls._parser is None:
            cls._parser = PydanticOutputParser(pydantic_object=cls)
        return cls._parser

    @classmethod
    def getFormatInstructions(cls) -> str:
        """获取输出格式说明"""
        return cls.getParser().get_format_instructions()

    @classmethod
    def parseOutput(cls, output: str) -> 'PerceivingOutput':
        """解析LLM的输出"""
        return cls.getParser().parse(output)

class BaseAgentAction(BaseTool):
    """基础动作类"""
    name: str
    description: str
    is_sensory_reflex: bool = False  # 标记是否为感觉反射动作，不参与perception流程
    # output_schema: ClassVar[Type[BaseModel]] = None  # 子类用于定义输出模型

    def getSchemaDescription(self) -> str:
        """获取动作的参数描述"""
        desc_list = []
        desc_list.append(f"## {self.name}")
        desc_list.append(f"描述: {self.description}")
        
        if self.args_schema:  # 直接使用 BaseTool 的 args_schema
            desc_list.append("参数:")
            for field_name, field in self.args_schema.model_fields.items():
                desc = field.description or "无描述"
                required = "必填" if field.is_required else "可选"
                # 获取参数类型
                field_type = field.annotation.__name__ if hasattr(field.annotation, '__name__') else str(field.annotation)
                desc_list.append(f"- {field_name}: {desc} (类型: {field_type}, {required})")
        desc_list.append("")
        return "\n".join(desc_list)

# TODO 提供action的增加功能，且注意重名问题。
class AgentActuator:
    """动作执行器"""
    
    def __init__(self):
        self.perceivedActions: List[BaseAgentAction] = []  # 觉察到的动作，参与perception流程
        self.sensoryReflexActions: List[BaseAgentAction] = []    # 感觉反射动作，不参与perception流程
        self.perceivedActionDict: Dict[str, BaseAgentAction] = {}
        self.sensoryReflexActionDict: Dict[str, BaseAgentAction] = {}
    
    def addAction(self, action: BaseAgentAction) -> bool:
        """添加单个动作
        
        Args:
            action: 要添加的动作
            
        Returns:
            bool: 添加是否成功，如果动作名称已存在则返回False
        """
        if action.is_sensory_reflex:
            # 感觉反射动作
            if action.name in self.sensoryReflexActionDict:
                return False
            self.sensoryReflexActions.append(action)
            self.sensoryReflexActionDict[action.name] = action
        else:
            # 觉察到的动作
            if action.name in self.perceivedActionDict:
                return False
            self.perceivedActions.append(action)
            self.perceivedActionDict[action.name] = action
        return True
    
    def addActions(self, actions: List[BaseAgentAction]) -> List[str]:
        """添加多个动作
        
        Args:
            actions: 要添加的动作列表
            
        Returns:
            List[str]: 添加失败的动作名称列表（由于名称重复）
        """
        failed_names = []
        for action in actions:
            if not self.addAction(action):
                failed_names.append(action.name)
        return failed_names
    
    def removeAction(self, actionName: str) -> bool:
        """移除单个动作
        
        Args:
            actionName: 要移除的动作名称
            
        Returns:
            bool: 移除是否成功，如果动作不存在则返回False
        """
        # 尝试从觉察到的动作中移除
        if actionName in self.perceivedActionDict:
            action = self.perceivedActionDict[actionName]
            self.perceivedActions.remove(action)
            del self.perceivedActionDict[actionName]
            return True
        
        # 尝试从感觉反射动作中移除
        if actionName in self.sensoryReflexActionDict:
            action = self.sensoryReflexActionDict[actionName]
            self.sensoryReflexActions.remove(action)
            del self.sensoryReflexActionDict[actionName]
            return True
        
        return False
    
    def removeActions(self, actionNames: List[str]) -> List[str]:
        """移除多个动作
        
        Args:
            actionNames: 要移除的动作名称列表
            
        Returns:
            List[str]: 移除失败的动作名称列表（由于动作不存在）
        """
        failed_names = []
        for name in actionNames:
            if not self.removeAction(name):
                failed_names.append(name)
        return failed_names
    
    def setActions(self, actions: List[BaseAgentAction]):
        """设置动作列表（清空现有动作）"""
        self.perceivedActions = []
        self.sensoryReflexActions = []
        self.perceivedActionDict = {}
        self.sensoryReflexActionDict = {}
        self.addActions(actions)
    
    def getActionDescriptions(self) -> str:
        """获取觉察到的动作描述列表，包含参数信息（只返回参与perception的动作）"""
        descriptions = []
        for action in self.perceivedActions:
            # 使用 BaseAction 中已实现的 getSchemaDescription 方法
            descriptions.append(action.getSchemaDescription())
        return "\n".join(descriptions)
    
    def getAction(self, name: str) -> Optional[BaseAgentAction]:
        """获取指定名称的动作（从所有动作中查找）"""
        return self.perceivedActionDict.get(name) or self.sensoryReflexActionDict.get(name)
    
    def getPerceivedAction(self, name: str) -> Optional[BaseAgentAction]:
        """获取指定名称的觉察到的动作"""
        return self.perceivedActionDict.get(name)
    
    def getSensoryReflexAction(self, name: str) -> Optional[BaseAgentAction]:
        """获取指定名称的感觉反射动作"""
        return self.sensoryReflexActionDict.get(name)



class BaseAgent(ABC):
    """基础Agent接口"""
    def __init__(self, name: str,
                 lifeGoalOrRole:Optional[str]=None, 
                 llm: Optional[ChatOpenAI] = None, 
                 promptTemplate: Optional[PromptTemplate] = None):
        self.name = name
        self.lifeGoalOrRole = lifeGoalOrRole  # 修复这里的赋值语法错误
        
        self.stemQueue = queue.Queue()  # 主干回路队列
        self.isRunning = True
        self.actionActuator = AgentActuator()  # 添加动作执行器实例
        
        #
        self.llm = llm  # 语言模型实例
        self.promptTemplate = promptTemplate  # 提示模板

    def setLLM(self, llm: ChatOpenAI):
        """设置语言模型"""
        self.llm = llm

    def setPromptTemplate(self, promptTemplate: PromptTemplate):
        """设置提示模板"""
        self.promptTemplate = promptTemplate

    @abstractmethod
    def run(self):
        """运行Agent"""
        raise NotImplementedError("senseMessageAndCallback 方法需要在子类中实现")

    def sendMessageToMe(self, message: str):
        """发送消息到Agent"""
        self.senseMessage(message)

    def senseMessage(self, message: str):
        """感知（发送）消息到Agent"""
        print(f"\n[用户] -> {self.name}: {message}")
        self.stemQueue.put(AgentSensoryEvent(
            message=message,
            eventType=AgentSensoryEvent.MESSAGE,
            source="user"
        ))
    
    #同步回调
    @abstractmethod
    def senseMessageAndCallback(self, message: str, callback: Callable[[str], None]):
        """感知（发送）消息到Agent,并通过回调反馈结果
        
        注意：这个方法应该是同步的，即在方法返回时，callback应该已经被完整调用完毕。
        子类在实现时必须确保这一点，以保证调用方能正确接收到完整的响应。
        """
        print(f"\n[用户] -> {self.name}: {message}")
        # self.stemQueue.put(AgentSensoryEvent(
        #     message=message,
        #     eventType=AgentSensoryEvent.MESSAGE,
        #     source="user",
        #     callback=callback,
        #     isSensoryReflex=True  # 标记为感觉反射事件，跳过perception直接执行
        # ))
        raise NotImplementedError("senseMessageAndCallback 方法需要在子类中实现")
    

    def senseEnvironmentEvent(self, command: str, **params):
        """感知（发送）环境事件到Agent"""
        self.stemQueue.put(AgentSensoryEvent(
            message=command,
            eventType=AgentSensoryEvent.ENV,
            source="system",
        ))

    def stop(self):
        """停止Agent"""
        print(f"\n[系统] 正在停止 {self.name}...")
        self.isRunning = False
        self.senseEnvironmentEvent("stop")

    def addAction(self, action: BaseAgentAction) -> bool:
        """添加单个动作"""
        return self.actionActuator.addAction(action)

    def addActions(self, actions: List[BaseAgentAction]) -> List[str]:
        """添加多个动作"""
        return self.actionActuator.addActions(actions)

    def removeAction(self, actionName: str) -> bool:
        """移除单个动作"""
        return self.actionActuator.removeAction(actionName)

    def removeActions(self, actionNames: List[str]) -> List[str]:
        """移除多个动作"""
        return self.actionActuator.removeActions(actionNames)

    def setActions(self, actions: List[BaseAgentAction]):
        """设置Agent可用的动作列表"""
        self.actionActuator.setActions(actions)




@dataclass
class BehaviorStep:
    """行为步骤"""
    instruction: str                          # 行为指令
    result: Optional[Any] = None             # 行为结果
    timestamp: datetime = field(default_factory=datetime.now)
    thought: Optional[str] = None            # 思考过程
    actionName: Optional[str] = None         # 关联的 Action 名称
    actionParams: Dict[str, str] = field(default_factory=dict)  # 动作参数

# TODO 需要为pattern提供解析与结果处理。模式的处理可以类似action也以底层tool的方式或者自己做的推导选择器；
@dataclass
class BehaviorPattern:
    """行为模式 - 表示一次完整的状态机微循环执行过程"""
    patternId: str                           # 模式标识
    instructions: List[str]                  # 行为指令组/模式定义
    steps: List[BehaviorStep] = field(default_factory=list)  # 实际执行的步骤记录
    currentIndex: int = 0                    # 当前步骤索引
    startTime: datetime = field(default_factory=datetime.now)
    endTime: Optional[datetime] = None
    
    def recordStep(self, instruction: str, thought: Optional[str] = None, 
                  actionName: Optional[str] = None) -> None:
        """记录执行步骤"""
        self.steps.append(BehaviorStep(
            instruction=instruction,
            thought=thought,
            actionName=actionName
        ))
    
    def setCurrentStepResult(self, result: Any) -> None:
        """设置当前步骤的结果"""
        if self.steps and self.currentIndex < len(self.steps):
            self.steps[self.currentIndex].result = result
    
    def moveNext(self) -> bool:
        """移动到下一个步骤"""
        if self.currentIndex < len(self.instructions) - 1:
            self.currentIndex += 1
            return True
        return False
    
    def getCurrentInstruction(self) -> Optional[str]:
        """获取当前指令"""
        if 0 <= self.currentIndex < len(self.instructions):
            return self.instructions[self.currentIndex]
        return None
    
    def getCurrentStep(self) -> Optional[BehaviorStep]:
        """获取当前步骤"""
        if self.steps and self.currentIndex < len(self.steps):
            return self.steps[self.currentIndex]
        return None
    
    def complete(self) -> None:
        """完成当前行为模式"""
        self.endTime = datetime.now()

@dataclass
class ThingMemory:
    """Agent 记忆组件"""
    chatMemory: ConversationBufferMemory = field(
        default_factory=lambda: ConversationBufferMemory(memory_key="chat_history")
    )
    currentPattern: Optional[BehaviorPattern] = None
    
    def startNewPattern(self, patternId: str, instructions: List[str]) -> None:
        """开始新的行为模式"""
        if self.currentPattern:
            self.completeCurrentPattern()
        self.currentPattern = BehaviorPattern(patternId=patternId, instructions=instructions)
    
    def completeCurrentPattern(self) -> None:
        """完成当前行为模式"""
        if self.currentPattern:
            self.currentPattern.complete()
            self.currentPattern = None
    
    def recordCurrentStep(self, thought: Optional[str] = None, 
                         actionName: Optional[str] = None,
                         actionParams: Dict[str, str] = None) -> None:
        """记录当前步骤"""
        if self.currentPattern:
            current_instruction = self.currentPattern.getCurrentInstruction()
            if current_instruction:
                self.currentPattern.recordStep(
                    instruction=current_instruction,
                    thought=thought,
                    actionName=actionName
                )
                if actionParams:
                    self.currentPattern.steps[-1].actionParams.update(actionParams)
    
    def setCurrentStepResult(self, result: Any) -> None:
        """设置当前步骤的结果"""
        if self.currentPattern:
            self.currentPattern.setCurrentStepResult(result)
    
    def moveToNextStep(self) -> Optional[str]:
        """移动到下一个步骤并返回其指令"""
        if self.currentPattern and self.currentPattern.moveNext():
            return self.currentPattern.getCurrentInstruction()
        return None



# 修改 AgentState 定义
class AgentSPTAState(BaseModel):
    """Agent状态定义"""
    
    # 状态常量定义
    SENSING: ClassVar[str] = "SENSING"
    PERCEIVING: ClassVar[str] = "PERCEIVING"
    THINKING: ClassVar[str] = "THINKING"
    ACTING: ClassVar[str] = "ACTING"
    END: ClassVar[str] = "END"

    current_step: str = Field(default=START)  # Langgraph使用的状态 #必须有

    currentState: str = Field(default=SENSING, description="当前状态")
    agent: "StateMachineAgent" = Field(description="当前Agent对象")  # 使用字符串引用避免循环导入
    currentActionNLRName: str = Field(default="", description="当前状态的action名称")
    nextActionNLRName: str = Field(default="", description="下一个状态的action名称线索")
    event: Optional[AgentSensoryEvent] = Field(default=None, description="当前正在处理的事件")
    thingMemory: ThingMemory = Field(description="事项记忆，表示一组需要完成的行为，其所需要的记忆。")
    perceivingOutput: Optional[PerceivingOutput] = Field(default=None, description="感知阶段的输出结果")

    class Config:
        arbitrary_types_allowed = True

# class PerceivingOutputOutput(BaseModel):
#     """感知阶段的输出结构对象"""
#     actionName: str = Field(description="当前要执行的动作名称")
#     nextActionName: str = Field(default="", description="下一步建议的动作名称")
#     thought: str = Field(description="对当前情况的理解和计划")
#     actionCallAndParams: MemoHistoryAction = Field(description="具体工具调用信息")



class ReplyUserAction(BaseAgentAction):
    """回复用户动作"""
    name: str = "回复用户"
    description: str = "直接回复用户消息"

    class ArgumentSchema(BaseModel):
        """回复用户的参数模型"""
        content: str = Field(..., description="回复的内容")
        memoName: Optional[str] = Field(default="", description="可选的关联备忘录名称")

    args_schema: Type[BaseModel] = ArgumentSchema

    @override
    def _run(self, content: str, memoName: str = "") -> str:
        if memoName:
            print(f"[模拟] 回复用户(关联备忘录 {memoName}): {content}")
            return f"已回复用户(关联备忘录 {memoName}): {content}"
        else:
            print(f"[模拟] 回复用户: {content}")
            return f"已回复用户: {content}"


class DirectReplyAction(BaseAgentAction):
    """直接回复动作 - 支持流式回调的 LLM 回复"""
    name: str = "直接回复"
    description: str = "与LLM进行直接回复，支持流式响应"
    is_sensory_reflex: bool = True  # 标记为感觉反射动作，不参与perception流程

    # Pydantic 字段定义，exclude=True 表示不参与序列化
    llm: Optional[Any] = Field(default=None, exclude=True, description="LLM实例")
    agent_name: str = Field(default="ANAN", exclude=True, description="Agent名称")

    class ArgumentSchema(BaseModel):
        """直接回复的参数模型"""
        message: str = Field(..., description="用户消息内容")
        isStream: bool = Field(default=True, description="是否使用流式响应")
        callback: Optional[Callable[[str], None]] = Field(default=None, description="流式响应回调函数")

    args_schema: Type[BaseModel] = ArgumentSchema

    #资源注入的初始化
    def __init__(self, llm=None, agent_name: str = None, **kwargs):
        # 调用父类的 __init__，传递 llm 和 agent_name 作为参数
        super().__init__(
            llm=llm,
            agent_name=agent_name or "ANAN",
            **kwargs
        )

    @override
    def _run(self, message: str, isStream: bool = True, callback: Callable[[str], None] = None) -> str:
        """执行直接回复"""
        if not self.llm:
            error_msg = "LLM实例未配置，无法执行直接回复"
            if callback:
                callback(f"\n\n[错误] {error_msg}")
            return error_msg

        try:
            # 构建简单的回复提示
            simple_prompt = f"""你是一个AI助手，名字是{self.agent_name}。
请根据用户的消息进行友好、准确的回复。

用户消息：{message}

请回复："""
            
            if isStream and callback:
                # 流式响应
                full_response = ""
                
                try:
                    # ChatOpenAI 的流式调用
                    for chunk in self.llm.stream(simple_prompt):
                        content = chunk.content if hasattr(chunk, 'content') else str(chunk)
                        if content:
                            full_response += content
                            callback(content)
                except Exception as stream_error:
                    # 如果流式调用失败，尝试普通调用
                    response = self.llm.invoke(simple_prompt)
                    content = response.content if hasattr(response, 'content') else str(response)
                    full_response = content
                    if callback:
                        callback(content)
                
                return full_response
            else:
                # 非流式响应
                response = self.llm.invoke(simple_prompt)
                result = response.content if hasattr(response, 'content') else str(response)
                if callback:
                    callback(result)
                return result
                
        except Exception as e:
            error_msg = f"LLM调用失败: {str(e)}"
            if callback:
                callback(f"\n\n[错误] {error_msg}")
            return error_msg


class StateMachineProcessor(ABC):
    """Agent处理器抽象基类"""
    @abstractmethod
    def createInitialState(self, agent: "StateMachineAgent") -> BaseModel:
        """创建初始状态"""
        pass
    
    @abstractmethod
    def process(self, state: BaseModel) -> BaseModel:
        """处理状态"""
        pass

@AAXW_AIAGENT_LOG_MGR.classLogger(level=logging.DEBUG)
class SPTAProcessor(StateMachineProcessor):
    """感知-认知-思考-行动处理器; Sensing Perceiving Thinking Acting processor"""
    AAXW_CLASS_LOGGER:logging.Logger
    
    def __init__(self):
        """初始化处理器"""
        pass
        
    @override
    def createInitialState(self, agent: "StateMachineAgent"):
        return AgentSPTAState(
            current_step=START,
            currentState=AgentSPTAState.SENSING,
            agent=agent,
            thingMemory=ThingMemory(),
            currentActionNLRName="",
            nextActionNLRName="",
            event=None
        )

    @override
    def process(self, state: AgentSPTAState) -> AgentSPTAState:
        """处理状态步骤，按照感知->认知->思考->行动的顺序执行"""
        try:
            # print(f"process 当前状态: {state}")
            # 使用类常量进行状态判断和赋值
            if state.currentState == state.SENSING:
                state = self.onSensing(state)
            if state.currentState == state.PERCEIVING:
                state = self.onPerceiving(state)
                # print(f"PERCEIVING 执行后 当前状态: {state}")
            if state.currentState == state.THINKING:
                state = self.onThinking(state)
            if state.currentState == state.ACTING:
                state = self.onActing(state)
                # onActing 方法内部会根据情况设置下一个状态
                # 可能是 SENSING（继续循环）或 END（结束循环）
            # print(f"process 当前状态: {state}")
        except Exception as e:
            import traceback
            print(f"process 异常: {e}")
            print(traceback.format_exc())
        finally:
            state.current_step = state.END
        return state
    
    def onSensing(self, state: AgentSPTAState) -> AgentSPTAState:
        """感知状态处理"""
        try:
            event = state.agent.stemQueue.get_nowait()
            # print(f"onSensing 当前事件: {event}")
            self.AAXW_CLASS_LOGGER.info(f"onSensing 当前事件: {event}")
            
            if event.getEventType() == AgentSensoryEvent.ENV and event.message == "stop":
                state.currentState = AgentSPTAState.END
                return state
            
            # 处理感觉反射事件 - 跳过perception和thinking，直接转到acting
            if event.isSensoryReflex:
                state.event = event  # 保存当前事件到状态
                state.currentState = AgentSPTAState.ACTING
                return state
            
            # 增加对 INNER、ENV、MESSAGE 事件的统一处理
            if event.getEventType() in [AgentSensoryEvent.INNER, AgentSensoryEvent.ENV, AgentSensoryEvent.MESSAGE]:
                state.event = event  # 保存当前事件到状态
                state.currentState = AgentSPTAState.PERCEIVING
                return state
            
        except queue.Empty:
            state.currentState = AgentSPTAState.END
            return state
        
        return state
    
    def onPerceiving(self, state: AgentSPTAState) -> AgentSPTAState:
        """知觉状态处理"""
        if not state.event:
            state.currentState = AgentSPTAState.END
            return state
            
        # 从agent获取资源
        if not state.agent.llm or not state.agent.promptTemplate:
            self.AAXW_CLASS_LOGGER.error("Agent未配置LLM或PromptTemplate")
            state.currentState = AgentSPTAState.END
            return state
            
        # 生成提示并获取响应
        prompt = state.agent.promptTemplate.format(
            life_goal_or_role=state.agent.lifeGoalOrRole or "",
            action_descriptions=state.agent.actionActuator.getActionDescriptions(),
            input_event=state.event.toMarkdownStr()
        )
        
        self.AAXW_CLASS_LOGGER.debug(f"最终prompt:\n{prompt}\n")
        try:
            response = state.agent.llm.invoke(prompt)
            # print(f"onPerceiving 直接输出: {response}")
            self.AAXW_CLASS_LOGGER.debug(
                f"onPerceiving 直接输出: {response.content}",
                extra={AAXWLoggerJsonFormatFilter.HAS_POTENTIAL_JSON_KEY: True})
            # 使用 PerceivingOutput 的类方法解析输出
            state.perceivingOutput = PerceivingOutput.parseOutput(response.content)
            
            # 更新状态
            state.currentActionNLRName = state.perceivingOutput.actionName
            state.nextActionNLRName = state.perceivingOutput.nextActionName
            
        except Exception as e:
            self.AAXW_CLASS_LOGGER.error(f"onPerceiving 异常: {e}", exc_info=True)
            self.AAXW_CLASS_LOGGER.error(f"onPerceiving 提示词内容: {prompt}")
            if response:
                self.AAXW_CLASS_LOGGER.error(f"onPerceiving 直接输出: {response}")
            raise e
        
        state.currentState = state.THINKING
        return state
    
    def onThinking(self, state: AgentSPTAState) -> AgentSPTAState:
        """思考状态处理"""
        # 简单处理，直接转到行动状态
        state.currentState = AgentSPTAState.ACTING
        return state
    
    def onActing(self, state: AgentSPTAState) -> AgentSPTAState:
        """行动状态处理"""
        # 检查是否为感觉反射事件
        if state.event and state.event.isSensoryReflex:
            # 处理感觉反射事件 - 直接执行对应的感觉反射动作
            return self._handleSensoryReflexEvent(state)
        
        # 处理常规事件 - 通过perception结果执行动作
        action = state.agent.actionActuator.getAction(state.currentActionNLRName)
        if action and state.perceivingOutput:
            try:
                # 使用perceivingOutput中的参数执行动作
                result = action.invoke(state.perceivingOutput.args)
                
                # 添加响应消息，包含思考过程和执行结果
                print(f"\n[{state.agent.name}] 思考: {state.perceivingOutput.thought}")
                print(f"[{state.agent.name}] 执行: {result}")
                
                # 如果当前事件是内部事件, 则将该事件设置为完成
                if state.event.eventType == AgentSensoryEvent.INNER:
                    state.event.markCompleted()
                
                # 如果有下一步动作信息，将当前执行结果和下一步动作信息一起写入事件
                if state.nextActionNLRName:
                    # 创建新的内部事件
                    new_event = AgentSensoryEvent(
                        message=f" 需要进行：{state.nextActionNLRName}",
                        eventType=AgentSensoryEvent.INNER,
                        source="self",
                        lastEvent=state.event,  # 保存当前事件作为下一个事件的上一个事件
                        lastResult=result,  # 保存当前执行结果
                        # 关联入口事件：优先使用上一个事件的入口事件，如果没有则使用上一个事件本身（如果是入口事件的话）
                        entryEvent=state.event.entryEvent or state.event.getEntryEvent()
                    )
                    state.agent.stemQueue.put(new_event)
                else:
                    # 如果没有下一步动作，标记入口事件为完成
                    entry_event = state.event.entryEvent or state.event.getEntryEvent()
                    if entry_event:
                        entry_event.markCompleted()
                
                
        # @FIXME 之后需要把错误情况也回执给 入口事件？
            except Exception as e:
                print(f"\n[{state.agent.name}] 执行出错: {str(e)}")
                # 发生错误时也要标记入口事件为完成
                entry_event = state.event.entryEvent or state.event.getEntryEvent()
                if entry_event:
                    entry_event.markCompleted()
            finally:
                #必然设置为结束
                state.currentState = AgentSPTAState.END
        else:
            print(f"\n[{state.agent.name}] 无法执行动作: {state.currentActionNLRName}")
            # 无法执行动作时也要标记入口事件为完成
            entry_event = state.event.entryEvent or state.event.getEntryEvent()
            if entry_event:
                entry_event.markCompleted()
                
            state.currentState = AgentSPTAState.END
        
        return state
    
    def _handleSensoryReflexEvent(self, state: AgentSPTAState) -> AgentSPTAState:
        """处理感觉反射事件"""
        try:
            event = state.event
            agent = state.agent
            
            # 根据事件类型查找对应的感觉反射动作
            sensory_reflex_action = self._findSensoryReflexAction(event, agent)
            
            if sensory_reflex_action:
                # 构建执行参数
                invoke_params = {
                    "message": event.message
                }
                
                # 如果有回调，添加回调和流式参数
                if event.callback:
                    invoke_params["callback"] = event.callback
                    invoke_params["isStream"] = True
                
                # 执行感觉反射动作
                result = sensory_reflex_action.invoke(invoke_params)
                print(f"\n[{agent.name}] 感觉反射执行: {result}")
                
                # 标记入口事件为完成
                entry_event = event.entryEvent or event.getEntryEvent()
                if entry_event:
                    entry_event.markCompleted()
                
            else:
                error_msg = f"未找到对应的感觉反射动作处理事件: {event.eventType}"
                print(f"\n[{agent.name}] {error_msg}")
                if event.callback:
                    event.callback(f"\n\n[错误] {error_msg}")
                # 错误时也要标记入口事件为完成
                entry_event = event.entryEvent or event.getEntryEvent()
                if entry_event:
                    entry_event.markCompleted()
            
        except Exception as e:
            self.AAXW_CLASS_LOGGER.error(f"处理感觉反射事件失败: {str(e)}", exc_info=True)
            if state.event and state.event.callback:
                state.event.callback(f"\n\n[错误] 处理感觉反射事件失败: {str(e)}")
            # 异常时也要标记入口事件为完成
            entry_event = event.entryEvent or event.getEntryEvent()
            if entry_event:
                entry_event.markCompleted()

        finally:
            state.currentState = AgentSPTAState.END
        
        return state
    
    def _findSensoryReflexAction(self, event: AgentSensoryEvent, agent: 'StateMachineAgent') -> Optional[BaseAgentAction]:
        """根据事件查找对应的感觉反射动作"""
        # 对于MESSAGE类型的感觉反射事件，查找直接回复动作
        if event.eventType == AgentSensoryEvent.MESSAGE and event.callback:
            # 获取或创建 DirectReplyAction
            direct_reply_action = agent.actionActuator.getSensoryReflexAction("直接回复")
            if not direct_reply_action:
                # 如果没有找到，创建并添加一个
                direct_reply_action = DirectReplyAction(llm=agent.llm, agent_name=agent.name)
                agent.actionActuator.addAction(direct_reply_action)
            return direct_reply_action
        
        # 可以在这里添加更多感觉反射事件类型的处理
        return None


class CallbackWrapper:
    """回调函数包装器，用于跟踪回调的执行情况"""
    def __init__(self, callback: Callable[[str], None]):
        self.callback = callback
        self.call_count = 0
        self.last_call_time = None
        self.is_completed = False
        self._lock = threading.Lock()

    def __call__(self, content: str):
        """执行回调并记录执行信息"""
        with self._lock:
            self.call_count += 1
            self.last_call_time = time.time()
            self.callback(content)

    def mark_completed(self):
        """标记回调执行完成"""
        with self._lock:
            self.is_completed = True

@AAXW_AIAGENT_LOG_MGR.classLogger()
class StateMachineAgent(BaseAgent):
    """提供基本状态机实现的Agent"""
    AAXW_CLASS_LOGGER:logging.Logger

    PROCESS = "process"

    def __init__(self, name: str, 
                 processor: StateMachineProcessor,
                 lifeGoalOrRole: Optional[str]=None,
                 runtimeIdleFunc: Optional[Callable[[], None]] = None,
                 llm: Optional[ChatOpenAI] = None, 
                 promptTemplate: Optional[PromptTemplate] = None):
        """
        初始化状态机Agent
        Args:
            name: Agent名称
            processor: 状态机处理器实例
            runtimeIdleFunc: 运行时空闲处理函数，默认为None则使用内部实现
        """
        super().__init__(name=name,lifeGoalOrRole=lifeGoalOrRole,llm=llm, promptTemplate=promptTemplate)
        self.processor = processor
        self.runtimeIdleFunc = runtimeIdleFunc if runtimeIdleFunc is not None else self._defaultRuntimeIdleFunc
        self.stateMachine:CompiledStateGraph = self._createStateMachine()
        self.isReqStop = False

    # @TODO 与其他感知事件的回调方式融合统一。
    # @TODO 当前要求实现为同步，需要考虑同时提供可异步的方式。至少提供Future模式的异步方式。
    #   比如用 afSenseMessageAndCallback -> from concurrent.futures.Future
    #   当前只是简单的写入Queue是纯异步实现。
    @override
    def senseMessageAndCallback(self, message: str, callback: Callable[[str], None]):
        """感知（发送）消息到Agent,并通过回调反馈结果
        
        注意：这个方法应该是同步的，即在方法返回时，callback应该已经被完整调用完毕。
        子类在实现时必须确保这一点，以保证调用方能正确接收到完整的响应。
        """
        print(f"\n[用户] -> {self.name}: {message}")
        
        try:
            # 创建事件并放入队列
            event = AgentSensoryEvent(
                message=message,
                eventType=AgentSensoryEvent.MESSAGE,
                source="user",
                callback=callback,
                isSensoryReflex=True  # 标记为感觉反射事件
            )
            self.stemQueue.put(event)
            
            # 等待事件完成
            start_time = time.time()
            while not event.isCompleted:
                if time.time() - start_time > 30.0:  # 30秒超时
                    error_msg = "等待事件处理完成超时"
                    self.AAXW_CLASS_LOGGER.error(error_msg)
                    callback(f"[错误] {error_msg}")
                    return error_msg
                time.sleep(0.1)  # 短暂休眠避免CPU占用
            
            return "已完成消息处理"
            
        except Exception as e:
            error_msg = f"消息处理失败: {str(e)}"
            self.AAXW_CLASS_LOGGER.error(f"{error_msg}\n{traceback.format_exc()}")
            callback(f"[错误] {error_msg}")
            return error_msg
        
    def _defaultRuntimeIdleFunc(self):
        """默认的运行时空闲处理函数"""
        time.sleep(0.5)

    def _createStateMachine(self)->CompiledStateGraph:
        """
        创建状态机
        通过处理器的初始状态来确定状态类型，该类型必须包含 current_step 属性
        """
        # 获取一个初始状态实例来确定状态类型
        initial_state = self.processor.createInitialState(self)
        if not hasattr(initial_state, 'current_step'): # 这个是langgraph必须用
            raise ValueError("状态类型必须包含 current_step 属性 (langgraph使用)")
            
        stateMachine = StateGraph(type(initial_state))
        stateMachine.add_node(self.PROCESS, self.processor.process)
        stateMachine.add_edge(START, self.PROCESS)
        stateMachine.add_edge(self.PROCESS, END)
        return stateMachine.compile()

    def stop(self):
        """请求停止Agent"""
        self.isReqStop = True
        super().stop()

    def run(self):
        """运行循环"""
        self.AAXW_CLASS_LOGGER.info(f"{self.name} 已启动，等待输入...")

        while not self.isReqStop:
            try:
                state = self.processor.createInitialState(self)
                self.stateMachine.invoke(state, config=RunnableConfig(recursion_limit=10))
                # self.runtimeIdleFunc()
            except Exception as e:
                self.AAXW_CLASS_LOGGER.error(f"运行时发生异常: {e} 但继续mainloop", exc_info=True)
            finally:
                #出错也idle
                self.runtimeIdleFunc()
        self.AAXW_CLASS_LOGGER.info(f"{self.name} 已停止.")

class AgentRuntime(ABC):
    """Agent运行时抽象基类"""
    @abstractmethod
    def submitAgent(self, agent: BaseAgent):
        """提交Agent到运行时"""
        pass

    @abstractmethod
    def shutdown(self):
        """关闭运行时"""
        pass

class ThreadPoolRuntime(AgentRuntime):
    """Python原生线程池运行时"""
    def __init__(self, maxWorkers: int = 4):
        self.threadPool = ThreadPoolExecutor(max_workers=maxWorkers)
        self.agentDict = {}

    def submitAgent(self, agent: BaseAgent):
        """提交Agent到线程池"""
        self.agentDict[agent.name] = agent
        self.threadPool.submit(agent.run)

    def shutdown(self):
        """关闭线程池"""
        for agent in self.agentDict.values():
            agent.stop()
        self.threadPool.shutdown(wait=True)

try:
    from PySide6.QtCore import QRunnable, QThreadPool
    PYSIDE6_AVAILABLE = True
except ImportError:
    PYSIDE6_AVAILABLE = False

if PYSIDE6_AVAILABLE:
    class PySide6RunnableWrapper(QRunnable):
        """QRunnable包装器"""
        def __init__(self, runFunc):
            super().__init__()
            self.runFunc = runFunc
            self.setAutoDelete(False)

        def run(self):
            """代理运行方法"""
            self.runFunc()

    class PySide6Runtime(AgentRuntime):
        """PySide6运行时"""
        def __init__(self):
            self.qtThreadPool = QThreadPool.globalInstance()
            self.agentDict = {}

        def submitAgent(self, agent: BaseAgent):
            """提交Agent到Qt线程池"""
            wrapper = PySide6RunnableWrapper(agent.run)
            self.agentDict[agent.name] = (agent, wrapper)
            self.qtThreadPool.start(wrapper)

        def shutdown(self):
            """关闭所有Agent"""
            for agent, _ in self.agentDict.values():
                agent.stop()
            self.qtThreadPool.waitForDone()


class PromptTemplateProvider:
    """Prompt模板提供者，负责创建和管理prompt模板"""
    
    @staticmethod
    def createDefaultPrompt() -> PromptTemplate:
        """创建默认的提示模板"""
        template = """# 使命与角色(life goal)
你是一个综合能力很强的智能主体。根据用户的信息、事件输入、前次思考执行情况，选择合适的动作来执行以及回复用户。
后续信息或任务事件中"事件内容"是本次具体任务。具体任务的执行时的偏向，需要围绕本"使命与角色"的上层目标来执行。
你也会根据"用户要求的使命与角色"进行补充角色与使命的补充、增强与偏向。
## 用户要求的使命与角色
{life_goal_or_role}

# 执行要求
请先理解用户需求，然后规划动作执行计划。
回复用户动作时，如有上次运行结果与内容，请将其作为复述内容的形式放入本次回复中。
回复用户动作时且被要求提供对动作结果做分析或计划时，请将上次运行结果与内容进行理解分析，并将结论放入。没有，则忽略本规则。
每次输入都有当前动作，但并不是每次信息都是有下一步动作的。
下一步动作是根据当前信息与本次动作来预判的。

# 可用的动作及其参数：
{action_descriptions}

# 约束-输出要求
你需要规划以下内容：
1. 当前动作：选择一个最适合当前情况的动作来执行；
2. 下一步动作：预判下一步可能需要的动作，帮助连贯性处理；可以没有下一步动作，任务或Thing完成，无需发起新的INNER事件；
3. 思考过程：解释你对当前情况的理解和处理计划；
4. 具体调用：提供完整的工具调用信息，包括具体动作、操作对象和内容；
5. 输出结构必须完整，字段必须有，内容可以根据字段情况为空字符串或None；
6. 在可用的动作列表中有足够动作时，可进行多步运行；如:先用动作"对话历史读取",下一步"generateName"生成新名字，再下一步"对话历史重命名"进行重命名，这样的流程；

# 约束-输出格式
{format_instructions}

# 补充示例：

# 信息或任务事件，其中"事件内容"中的内容为具体任务主干:
{input_event}
"""
        return PromptTemplate(
            template=template,
            input_variables=["life_goal_or_role","action_descriptions", "input_event"],
            partial_variables={"format_instructions": PerceivingOutput.getFormatInstructions()}
        )

class AgentEnvironment:
    """Agent运行环境"""
    def __init__(self, runtimeType: str = "thread_pool"):
        if runtimeType == "thread_pool":
            self.runtime = ThreadPoolRuntime()
        elif runtimeType == "pyside6" and PYSIDE6_AVAILABLE:
            self.runtime = PySide6Runtime()
        else:
            raise ValueError(f"不支持的运行时类型: {runtimeType}")
        self.agentDict = {}

    def createAgent(self, name: str, 
                    lifeGoalOrRole:str=None,
                    processor: Optional[StateMachineProcessor] = None,
                    llm: Optional[ChatOpenAI] = None,
                    promptTemplate: Optional[PromptTemplate] = None) -> BaseAgent:
        """
        创建并启动一个Agent
        
        Args:
            name: Agent名称
            processor: 可选的状态机处理器实例，如果不提供则使用默认的SPTA处理器
            llm: 可选的语言模型实例，如果不提供则使用默认配置
            promptTemplate: 可选的提示模板，如果不提供则使用默认模板
            
        Returns:
            BaseAgent: 创建的Agent实例
        """

        if not lifeGoalOrRole:
            lifeGoalOrRole="你是一个综合能力很强的智能主体，名字叫ANAN。根据已有天生能力处理具体任务。"

        if processor is None:
            processor = SPTAProcessor()


        if llm is None:
            llm = ChatOpenAI(temperature=0, model="gpt-4o-mini")

        if promptTemplate is None:
            promptTemplate = PromptTemplateProvider.createDefaultPrompt()



        agent = StateMachineAgent(
            name=name,
            lifeGoalOrRole=lifeGoalOrRole,
            processor=processor,
            # llm=llm,
            # promptTemplate=promptTemplate
        )
        
        # 设置llm资源
        agent.setLLM(llm)
        agent.setPromptTemplate(promptTemplate)


        # 初始化并注入动作
        actions = [
            ReplyUserAction()
        ]
        agent.actionActuator.setActions(actions)
        self.agentDict[name] = agent
        self.runtime.submitAgent(agent)
        return agent

    def stopAgent(self, name: str):
        """停止指定的Agent"""
        if name in self.agentDict:
            self.agentDict[name].stop()
            del self.agentDict[name]

    def stopAll(self):
        """停止所有Agent并关闭运行时"""
        self.runtime.shutdown()



class SafetyFallbackAgent(BaseAgent):
    """安全故障转移Agent实现，用于在主要Agent初始化失败时作为备用。
    提供基本的日志记录和友好的错误提示，确保系统可以继续运行。
    """
    
    def __init__(self, name: str):
        super().__init__(name)
        self.AAXW_CLASS_LOGGER = AAXW_AIAGENT_LOG_MGR.getClassLogger(self.__class__)
        self.AAXW_CLASS_LOGGER.warning(f"使用安全故障转移Agent: {name}，这表明主要Agent初始化失败")

    @override
    def run(self):
        """空实现的运行方法"""
        self.AAXW_CLASS_LOGGER.warning(f"安全故障转移Agent {self.name} 尝试运行")
        self.isRunning = True

    @override
    def sendMessageToMe(self, message: str) -> str:
        """记录接收到的消息并返回友好提示"""
        self.AAXW_CLASS_LOGGER.warning(f"安全故障转移Agent {self.name} 收到消息: {message}")
        return "Agent未能正确初始化，请检查LLM配置并确保所需服务可用。如需帮助，请查看日志获取详细信息。"

    @override
    def senseEnvironmentEvent(self, command: str) -> None:
        """记录接收到的环境事件"""
        self.AAXW_CLASS_LOGGER.warning(f"安全故障转移Agent {self.name} 收到环境事件: {command}")

    @override
    def senseMessageAndCallback(self, message: str, callback: Callable[[str], None]):
        """同步版本的消息感知与回调，返回友好的错误提示"""
        self.AAXW_CLASS_LOGGER.warning(f"安全故障转移Agent {self.name} 收到消息: {message}")
        error_msg = "Agent未能正确初始化，请检查LLM配置并确保所需服务可用。如需帮助，请查看日志获取详细信息。"
        callback(error_msg)

    @override
    def addActions(self, actions: List[BaseAgentAction]) -> None:
        """记录尝试添加的动作"""
        action_names = [action.name for action in actions]
        self.AAXW_CLASS_LOGGER.warning(f"安全故障转移Agent {self.name} 尝试添加动作: {action_names}")

    @override
    def stop(self) -> None:
        """记录停止事件"""
        self.AAXW_CLASS_LOGGER.warning(f"安全故障转移Agent {self.name} 停止运行")
        self.isRunning = False


if __name__ == "__main__":
    
    load_dotenv()
    class MemoReadAction(BaseAgentAction):
        """读取备忘录动作"""
        name: str = "读取备忘"
        description: str = "读取指定名称备忘录的内容"

        # 这是用来获取参数的Schema信息，用来生成prompt或来解析。
        class ArgumentSchema(BaseModel):
            """读取备忘录的参数模型"""
            memoName: str = Field(..., description="备忘录名称")
            content: str = Field(default="", description="可选参数")

        args_schema: Type[BaseModel] = ArgumentSchema

        @override
        def _run(self, memoName: str, content: str = "") -> str:
            print(f"[模拟] 读取备忘录 {memoName} 的内容：---你好，{memoName}是1个比较重要的事情，需要尽快完成---")
            return f"---你好，{memoName}是1个比较重要的事情，需要尽快完成---"

    class MemoRenameAction(BaseAgentAction):
        """重命名备忘录动作"""
        name: str = "重命名备忘"
        description: str = "将指定名称的备忘录重命名为新名称"

        class ArgumentSchema(BaseModel):
            """重命名备忘录的参数模型"""
            memoName: str = Field(..., description="原备忘录名称")
            newName: str = Field(..., description="新的备忘录名称")

        args_schema: Type[BaseModel] = ArgumentSchema

        @override
        def _run(self, memoName: str, newName: str) -> str:
            print(f"[模拟] 将备忘录 {memoName} 重命名为 {newName}")
            return f"已将备忘录 {memoName} 重命名为 {newName}"

    
    def test_env_event():
        """测试环境事件触发的Agent"""
        env = AgentEnvironment("thread_pool")
        try:
            # 创建自定义的prompt模板（这里使用一个简化版的示例）
            custom_template = """# 角色与环境
你是一个专注于备忘录管理的AI助手。你的主要职责是帮助用户管理和操作备忘录。

# 执行要求
1. 仔细理解用户的备忘录相关需求
2. 选择合适的动作来处理备忘录
3. 给出清晰的执行反馈

# 可用的动作及其参数：
{action_descriptions}

# 约束-输出格式
{format_instructions}

# 当前任务：
{input_event}
"""
            custom_prompt = PromptTemplate(
                template=custom_template,
                input_variables=["action_descriptions", "input_event"],
                partial_variables={"format_instructions": PerceivingOutput.getFormatInstructions()}
            )
            
            # 创建自定义的LLM实例
            custom_llm = ChatOpenAI(temperature=0, model="gpt-4o-mini")
            
            # 创建处理器实例
            processor = SPTAProcessor()
            
            # 创建agent并设置处理器
            agent = env.createAgent(
                name="资源管理助手",
                processor=processor,
                llm=custom_llm,
                promptTemplate=custom_prompt
            )
            
            # 增加备忘录的action
            agent.addActions([
                MemoReadAction(),
                MemoRenameAction(),
            ])
    
            time.sleep(1)
            
            # 发送测试消息
            agent.sendMessageToMe("请帮我将'工作计划'的备忘录改名，改名使用对备忘读取内容的小结。备忘录名字不能超过15个字符。改完请回复我一下。")
            
            time.sleep(60)  # 等待处理完成
            
        except KeyboardInterrupt:
            AAXW_AIAGENT_MODULE_LOGGER.info("接收到中断信号，正在停止...")
        finally:
            env.stopAll()
    
    def test_direct_reply():
        """测试直接回复功能"""
        env = AgentEnvironment("thread_pool")
        try:
            # 创建处理器实例
            processor = SPTAProcessor()
            
            # 创建 agent
            agent = env.createAgent(
                name="直接回复助手",
                processor=processor,
                llm=ChatOpenAI(temperature=0, model="gpt-4o-mini")
            )
            
            time.sleep(1)
            
            print("开始测试直接回复功能...")
            
            # 定义回调函数来处理流式响应
            def response_callback(content: str):
                print(content, end='', flush=True)
            
            # 发送直接回复消息
            print(f"\n[用户] -> {agent.name}: 你好，请介绍一下你自己")
            agent.senseMessageAndCallback("你好，请介绍一下你自己", response_callback)
            
            time.sleep(5)  # 等待响应完成
            
            print("\n" + "="*50)
            
            # 再测试一次
            print(f"\n[用户] -> {agent.name}: 你能做什么？")
            agent.senseMessageAndCallback("你能做什么？", response_callback)
            
            time.sleep(5)  # 等待响应完成
            
            print(f"\n测试完成")
            
        except KeyboardInterrupt:
            AAXW_AIAGENT_MODULE_LOGGER.info("接收到中断信号，正在停止...")
        finally:
            env.stopAll()

    if not os.getenv("OPENAI_API_KEY"):
        AAXW_AIAGENT_MODULE_LOGGER.error("请在.env文件中设置OPENAI_API_KEY")
        raise ValueError("请在.env文件中设置OPENAI_API_KEY")
    
    test_direct_reply()



# 以下注释内容不要删除
#     def _createPatternPrompt(self) -> PromptTemplate:
#         """创建行为模式提示模板"""
#         template = """你是一个应用资源管理者，负责管理应用的各种资源，包括备忘录等。
# 基于用户的输入，请规划一个行为模式来处理这个管理任务。

# 用户输入: {input}

# 请按以下格式输出：
# 思考过程：[你对任务的理解和管理计划]
# 第一个动作：[具体的action_name]
# 行为步骤：
# 1. [第一步指令]
# 2. [第二步指令]
# ...

# 请确保第一个动作是一个具体的、可执行的action_name，与可用的动作列表对应。

# 可用的动作有：
# {action_descriptions}
# """
# #

