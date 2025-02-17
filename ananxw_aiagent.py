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

# from regex import P

if __name__ == "__main__":
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)  # 插入到路径最前面

from ananxw_jumpin.ananxw_jumpin_allin1f import AAXW_JUMPIN_LOG_MGR
AAXW_JUMPIN_MODULE_LOGGER:logging.Logger=AAXW_JUMPIN_LOG_MGR.getModuleLogger(
    sys.modules[__name__])

@dataclass
class SensoryEvent:
    """感知事件基类"""
    # 事件类型常量定义
    INNER: ClassVar[str] = "INNER"      # 内部事件，如状态转换、内部处理等
    ENV: ClassVar[str] = "ENV"          # 环境事件，如系统命令、环境变化等
    MESSAGE: ClassVar[str] = "MESSAGE"  # 消息事件，如用户输入、对话等
    
    message: str                        # 事件消息内容
    eventType: str = MESSAGE            # 事件类型标识
    source: str = "user"                # 事件来源
    timestamp: datetime = field(default_factory=datetime.now)

    lastEvent: Optional['SensoryEvent'] = field(default=None)  # 上一次事件
    lastResult: Optional[str] = field(default=None)  # 上一次执行结果

    
    def getEventType(self) -> str:
        """获取事件类型"""
        return self.eventType
    
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

class BaseAction(BaseTool):
    """基础动作类"""
    name: str
    description: str
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
class ActionActuator:
    """动作执行器"""
    
    def __init__(self):
        self.actions: List[BaseAction] = []
        self.actionDict: Dict[str, BaseAction] = {}
    
    def addAction(self, action: BaseAction) -> bool:
        """添加单个动作
        
        Args:
            action: 要添加的动作
            
        Returns:
            bool: 添加是否成功，如果动作名称已存在则返回False
        """
        if action.name in self.actionDict:
            return False
        self.actions.append(action)
        self.actionDict[action.name] = action
        return True
    
    def addActions(self, actions: List[BaseAction]) -> List[str]:
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
        if actionName not in self.actionDict:
            return False
        action = self.actionDict[actionName]
        self.actions.remove(action)
        del self.actionDict[actionName]
        return True
    
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
    
    def setActions(self, actions: List[BaseAction]):
        """设置动作列表（清空现有动作）"""
        self.actions = []
        self.actionDict = {}
        self.addActions(actions)
    
    def getActionDescriptions(self) -> str:
        """获取动作描述列表，包含参数信息"""
        descriptions = []
        for action in self.actions:
            # 使用 BaseAction 中已实现的 getSchemaDescription 方法
            descriptions.append(action.getSchemaDescription())
        return "\n".join(descriptions)
    
    def getAction(self, name: str) -> Optional[BaseAction]:
        """获取指定名称的动作"""
        return self.actionDict.get(name)



class BaseAgent(ABC):
    """基础Agent接口"""
    def __init__(self, name: str):
        self.name = name
        self.stemQueue = queue.Queue()  # 主干回路队列
        self.isRunning = True
        self.actionActuator = ActionActuator()  # 添加动作执行器实例

    @abstractmethod
    def run(self):
        """运行Agent"""
        pass

    def sendMessageToMe(self, message: str):
        """发送消息到Agent"""
        self.senseMessage(message)

    def senseMessage(self, message: str):
        """感知（发送）消息到Agent"""
        print(f"\n[用户] -> {self.name}: {message}")
        self.stemQueue.put(SensoryEvent(
            message=message,
            eventType=SensoryEvent.MESSAGE,
            source="user"
        ))

    def senseEnvironmentEvent(self, command: str, **params):
        """感知（发送）环境事件到Agent"""
        self.stemQueue.put(SensoryEvent(
            message=command,
            eventType=SensoryEvent.ENV,
            source="system",
        ))

    def stop(self):
        """停止Agent"""
        print(f"\n[系统] 正在停止 {self.name}...")
        self.isRunning = False
        self.senseEnvironmentEvent("stop")

    def addAction(self, action: BaseAction) -> bool:
        """添加单个动作"""
        return self.actionActuator.addAction(action)

    def addActions(self, actions: List[BaseAction]) -> List[str]:
        """添加多个动作"""
        return self.actionActuator.addActions(actions)

    def removeAction(self, actionName: str) -> bool:
        """移除单个动作"""
        return self.actionActuator.removeAction(actionName)

    def removeActions(self, actionNames: List[str]) -> List[str]:
        """移除多个动作"""
        return self.actionActuator.removeActions(actionNames)

    def setActions(self, actions: List[BaseAction]):
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

    current_step: str = Field(default=START)  # Langgraph使用的状态
    currentState: str = Field(default=SENSING, description="当前状态")
    agent: BaseAgent = Field(description="当前Agent对象")
    currentActionNLRName: str = Field(default="", description="当前状态的action名称")
    nextActionNLRName: str = Field(default="", description="下一个状态的action名称线索")
    event: Optional[SensoryEvent] = Field(default=None, description="当前正在处理的事件")
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



class ReplyUserAction(BaseAction):
    """回复用户动作"""
    name: str = "回复用户"
    description: str = "直接回复用户消息，可以关联备忘录"

    class ArgumentSchema(BaseModel):
        """回复用户的参数模型"""
        content: str = Field(..., description="回复的内容")
        memoName: Optional[str] = Field(default="", description="可选的关联备忘录名称")

    args_schema: Type[BaseModel] = ArgumentSchema

    def _run(self, content: str, memoName: str = "") -> str:
        if memoName:
            print(f"[模拟] 回复用户(关联备忘录 {memoName}): {content}")
            return f"已回复用户(关联备忘录 {memoName}): {content}"
        else:
            print(f"[模拟] 回复用户: {content}")
            return f"已回复用户: {content}"

@AAXW_JUMPIN_LOG_MGR.classLogger()
class SensingPerceivingThinkingActingProcess:
    """感知-认知-思考-行动处理器"""
    AAXW_CLASS_LOGGER:logging.Logger
    
    def __init__(self):
        self.llm = ChatOpenAI(temperature=0, model="gpt-4o-mini")
        # self.llm = ChatOpenAI(temperature=0,model="deepseek-chat")
        # 使用 PerceivingOutput 的类方法
        self.promptTemplate = self._createPrompt()


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
    
    def _createPrompt(self) -> PromptTemplate:
        """创建提示模板"""
        template = """# 角色与环境
你是一个应用资源管理者。根据用户的信息、事件输入、前次思考执行情况，选择合适的动作来管理应用资源并回复。

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

# 约束-输出格式
{format_instructions}

# 补充示例：


# 信息或事件输入，其中message为输入主干内容:
{input_event}

"""
        return PromptTemplate(
            template=template,
            input_variables=["action_descriptions", "input_event"],
            # 使用 PerceivingOutput 的类方法获取格式说明
            partial_variables={"format_instructions": PerceivingOutput.getFormatInstructions()}
        )

    def onSensing(self, state: AgentSPTAState) -> AgentSPTAState:
        """感知状态处理"""
        try:
            event = state.agent.stemQueue.get_nowait()
            # print(f"onSensing 当前事件: {event}")
            self.AAXW_CLASS_LOGGER.info(f"onSensing 当前事件: {event}")
            
            if event.getEventType() == SensoryEvent.ENV and event.message == "stop":
                state.currentState = AgentSPTAState.END
                return state
            
            # 增加对 INNER、ENV、MESSAGE 事件的统一处理
            if event.getEventType() in [SensoryEvent.INNER, SensoryEvent.ENV, SensoryEvent.MESSAGE]:
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
            
        # 生成提示并获取响应
        prompt = self.promptTemplate.format(
            action_descriptions=state.agent.actionActuator.getActionDescriptions(),
            input_event=state.event.toMarkdownStr()
        )
        
        # print(f"onPerceiving 最终提示词内容: {prompt}")
        try:
            response = self.llm.invoke(prompt)
            print(f"onPerceiving 直接输出: {response}")
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
        # 使用agent的actionActuator获取动作
        # print(f"onActing 当前状态: {state}")
        action = state.agent.actionActuator.getAction(state.currentActionNLRName)
        if action and state.perceivingOutput:
            try:
                # 使用perceivingOutput中的参数执行动作
                result = action.invoke(state.perceivingOutput.args)
                
                # 添加响应消息，包含思考过程和执行结果
                print(f"\n[{state.agent.name}] 思考: {state.perceivingOutput.thought}")
                print(f"[{state.agent.name}] 执行: {result}")
                
                # 如果有下一步动作信息，将当前执行结果和下一步动作信息一起写入事件
                if state.nextActionNLRName:
                    state.agent.stemQueue.put(SensoryEvent(
                        message=f" 需要进行：{state.nextActionNLRName}",
                        eventType=SensoryEvent.INNER,
                        source="self",
                        lastEvent=state.event,  # 保存当前事件作为下一个事件的上一个事件
                        lastResult=result  # 保存当前执行结果
                    ))
                
                state.currentState = AgentSPTAState.END
            except Exception as e:
                print(f"\n[{state.agent.name}] 执行出错: {str(e)}")
                state.currentState = AgentSPTAState.END
        else:
            print(f"\n[{state.agent.name}] 无法执行动作: {state.currentActionNLRName}")
            state.currentState = AgentSPTAState.END
        
        # print(f"onActing 当前状态结束")
        return state

@AAXW_JUMPIN_LOG_MGR.classLogger()
class StateMachineAgent(BaseAgent):
    """提供基本状态机实现的Agent"""
    AAXW_CLASS_LOGGER:logging.Logger

    PROCESS = "process"
    
    def __init__(self, name: str, 
                 processFunc: Callable[[AgentSPTAState], AgentSPTAState],
                 runtimeIdleFunc: Optional[Callable[[], None]] = None):
        """
        初始化状态机Agent
        :param name: Agent名称
        :param processFunc: 处理状态的处理函数
        :param runtimeIdleFunc: 运行时空闲处理函数，默认为None则使用内部实现
        """
        super().__init__(name)
        self.processFunc = processFunc
        self.runtimeIdleFunc = runtimeIdleFunc if runtimeIdleFunc is not None else self._defaultRuntimeIdleFunc
        self.stateMachine:CompiledStateGraph = self._createStateMachine()
        self.isReqStop = False
        
    def _defaultRuntimeIdleFunc(self):
        """默认的运行时空闲处理函数"""
        time.sleep(0.5)

    def _createStateMachine(self)->CompiledStateGraph:
        """创建状态机"""
        stateMachine = StateGraph(AgentSPTAState)
        stateMachine.add_node(self.PROCESS, self.processFunc)
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
                state = AgentSPTAState(
                    current_step=START,
                    currentState=AgentSPTAState.SENSING,
                    agent=self,
                    thingMemory=ThingMemory(),
                    currentActionNLRName="",
                    nextActionNLRName="",
                    event=None
                )
                # print(f"run 当前状态: {state}")
                self.stateMachine.invoke(state, config=RunnableConfig(recursion_limit=10))
                self.runtimeIdleFunc()
            except Exception as e:
                self.AAXW_CLASS_LOGGER.error(f"运行时发生异常: {e} 但继续mainloop", exc_info=True)
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

    def createAgent(self, name: str) -> BaseAgent:
        """创建并启动一个Agent"""
        processor = SensingPerceivingThinkingActingProcess()
        
        # 初始化并注入动作
        actions = [
            ReplyUserAction()
        ]

        agent = StateMachineAgent(
            name=name,
            processFunc=processor.process
        )
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



if __name__ == "__main__":
    
    load_dotenv()
    class MemoReadAction(BaseAction):
        """读取备忘录动作"""
        name: str = "读取备忘"
        description: str = "读取指定名称备忘录的内容"

        # 这是用来获取参数的Schema信息，用来生成prompt或来解析。
        class ArgumentSchema(BaseModel):
            """读取备忘录的参数模型"""
            memoName: str = Field(..., description="备忘录名称")
            content: str = Field(default="", description="可选参数")

        args_schema: Type[BaseModel] = ArgumentSchema

        def _run(self, memoName: str, content: str = "") -> str:
            print(f"[模拟] 读取备忘录 {memoName} 的内容：---你好，{memoName}是1个比较重要的事情，需要尽快完成---")
            return f"---你好，{memoName}是1个比较重要的事情，需要尽快完成---"

    class MemoRenameAction(BaseAction):
        """重命名备忘录动作"""
        name: str = "重命名备忘"
        description: str = "将指定名称的备忘录重命名为新名称"

        class ArgumentSchema(BaseModel):
            """重命名备忘录的参数模型"""
            memoName: str = Field(..., description="原备忘录名称")
            newName: str = Field(..., description="新的备忘录名称")

        args_schema: Type[BaseModel] = ArgumentSchema

        def _run(self, memoName: str, newName: str) -> str:
            print(f"[模拟] 将备忘录 {memoName} 重命名为 {newName}")
            return f"已将备忘录 {memoName} 重命名为 {newName}"

    
    def test_env_event():
        """测试环境事件触发的Agent"""
        env = AgentEnvironment("thread_pool")
        try:
            agent = env.createAgent("资源管理助手")
            # 增加备忘录的action
            agent.addActions([
                MemoReadAction(),
                MemoRenameAction(),
            ])
    
            time.sleep(1)
            
            # 发送测试消息
            # agent.sendMessageToMe("请帮我读取名为'工作计划'的备忘录")
            agent.sendMessageToMe("请帮我将'工作计划'的备忘录改名，改名使用对备忘读取内容的小结。备忘录名字不能超过15个字符。改完请回复我一下。")
            
            time.sleep(60)  # 等待处理完成
            
        except KeyboardInterrupt:
            AAXW_JUMPIN_MODULE_LOGGER.info("接收到中断信号，正在停止...")
        finally:
            env.stopAll()
    
    if not os.getenv("OPENAI_API_KEY"):
        AAXW_JUMPIN_MODULE_LOGGER.error("请在.env文件中设置OPENAI_API_KEY")
        raise ValueError("请在.env文件中设置OPENAI_API_KEY")
    
    test_env_event()



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