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
#  llm驱动的ai agent实现；
#  基于langchain,langgraph的实现；

from typing import Dict, TypedDict, Annotated, List, Optional, Callable, Any, Tuple, ClassVar
from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_core.runnables.config import RunnableConfig
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
import os
import math
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

# TODO 考虑增加1st-order-logic的实现；提供1st-order指令的schema
class MemoHistoryAction(BaseModel):
    """备忘录历史操作的输出模型"""
    action_name: str = Field(description="要执行的动作名称")
    memo_name: str = Field(description="要操作的备忘录名称")
    content: str = Field(description="操作的内容")
    thought: str = Field(description="对操作过程的理解和计划")

class MemoActions:
    """备忘录操作集合"""
    
    @staticmethod
    def renameMemo(old_name: str, new_name: str) -> str:
        """重命名备忘录"""
        print(f"[模拟] 将备忘录 {old_name} 重命名为 {new_name}")
        return f"已将备忘录 {old_name} 重命名为 {new_name}"

    @staticmethod
    def readMemo(memo_name: str, _: str = "") -> str:
        """读取备忘录内容"""
        print(f"[模拟] 读取备忘录 {memo_name} 的内容")
        return f"这是 {memo_name} 的模拟内容"

class ActionActuator:
    """动作执行器"""
    
    def __init__(self):
        self.actions = []
        self.action_dict = {}
        
    def setActions(self, actions: List[Tool]):
        """设置动作列表"""
        self.actions = actions
        self.action_dict = {action.name: action for action in actions}
    
    def getActionDescriptions(self) -> str:
        """获取动作描述列表"""
        return "\n".join([f"- {action.name}: {action.description}" for action in self.actions])
    
    def getAction(self, name: str) -> Tool:
        """获取指定名称的动作"""
        return self.action_dict.get(name)

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
    behaviorPattern: Optional['BehaviorPattern'] = None  # 行为模式
    
    def getEventType(self) -> str:
        """获取事件类型"""
        return self.eventType
    
    def getBehaviorPattern(self) -> Optional['BehaviorPattern']:
        """获取行为模式"""
        return self.behaviorPattern

class BaseAgent(ABC):
    """基础Agent接口"""
    def __init__(self, name: str):
        self.name = name
        self.stemQueue = queue.Queue()  # 主干回路队列
        self.isRunning = True

    @abstractmethod
    def run(self):
        """运行Agent"""
        pass

    def sendMessageToMe(self, message: str):
        """发送消息到Agent"""
        self.senseMessage(message)

    def senseMessage(self, message: str):
        """发送消息到Agent"""
        print(f"\n[用户] -> {self.name}: {message}")
        self.stemQueue.put(SensoryEvent(
            message=message,
            eventType=SensoryEvent.MESSAGE,
            source="user"
        ))

    def senseEnvironmentEvent(self, command: str, **params):
        """发送系统事件到Agent"""
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

@dataclass
class BehaviorStep:
    """行为步骤"""
    instruction: str                          # 行为指令
    result: Optional[Any] = None             # 行为结果
    timestamp: datetime = field(default_factory=datetime.now)
    thought: Optional[str] = None            # 思考过程
    actionName: Optional[str] = None         # 关联的 Action 名称

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
class AgentMemory:
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
                         actionName: Optional[str] = None) -> None:
        """记录当前步骤"""
        if self.currentPattern:
            current_instruction = self.currentPattern.getCurrentInstruction()
            if current_instruction:
                self.currentPattern.recordStep(
                    instruction=current_instruction,
                    thought=thought,
                    actionName=actionName
                )
    
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
class AgentState(BaseModel):
    """Agent状态定义"""
    # 状态常量定义
    SENSING: ClassVar[str] = "SENSING"
    PERCEIVING: ClassVar[str] = "PERCEIVING"
    THINKING: ClassVar[str] = "THINKING"
    ACTING: ClassVar[str] = "ACTING"
    END: ClassVar[str] = "END"

    # 实例字段定义
    messages: List[BaseMessage] = Field(default_factory=list, description="对话历史")
    current_state: str = Field(default=SENSING, description="当前状态")
    agent: BaseAgent = Field(description="当前Agent对象")
    memory: AgentMemory = Field(description="Agent记忆组件")

    class Config:
        arbitrary_types_allowed = True  # 允许任意类型，因为BaseAgent和AgentMemory可能不是pydantic模型

# TODO 提示词与外层逻辑进行对应执行。当前存在问题；
# TODO 需要为pattern提供解析与结果处理。模式的处理可以类似action也以底层tool的方式或者自己做的推导选择器；
class SensingPerceivingThinkingActingProcess:
    """感知-认知-思考-行动处理器"""
    
    def __init__(self):
        self.llm = ChatOpenAI(temperature=0, model="gpt-3.5-turbo")
        self.action_actuator = ActionActuator()
        self.parser = PydanticOutputParser(pydantic_object=MemoHistoryAction)
        self.prompt = self._createPrompt()
        self.pattern_prompt = self._createPatternPrompt()
    
    def _createPrompt(self) -> PromptTemplate:
        """创建提示模板"""
        template = """你是一个应用资源管理者。根据用户的请求，选择合适的动作来管理应用资源。
请先用一句话描述你对请求的理解和计划，作为thought字段的内容，然后选择合适的动作执行。

可用的动作有：
{action_descriptions}

用户输入: {input}

{format_instructions}"""

        return PromptTemplate(
            template=template,
            input_variables=["action_descriptions", "input"],
            partial_variables={"format_instructions": self.parser.get_format_instructions()}
        )
    
    def _createPatternPrompt(self) -> PromptTemplate:
        """创建行为模式提示模板"""
        template = """你是一个应用资源管理者，负责管理应用的各种资源，包括备忘录等。
基于用户的输入，请规划一个行为模式来处理这个管理任务。

用户输入: {input}

请按以下格式输出：
思考过程：[你对任务的理解和管理计划]
第一个动作：[具体的action_name]
行为步骤：
1. [第一步指令]
2. [第二步指令]
...

请确保第一个动作是一个具体的、可执行的action_name，与可用的动作列表对应。

可用的动作有：
{action_descriptions}
"""
        return PromptTemplate(
            template=template,
            input_variables=["input", "action_descriptions"]
        )

    def process(self, state: "AgentState") -> "AgentState":
        """处理状态步骤，按照感知->认知->思考->行动的顺序执行"""
        # print(f"process 当前状态: {state}")
        # 使用类常量进行状态判断和赋值
        if state.current_state == state.SENSING:
            state = self.onSensing(state)
            state.current_state = state.PERCEIVING
        
        if state.current_state == state.PERCEIVING:
            state = self.onPerceiving(state)
            state.current_state = state.THINKING
        
        if state.current_state == state.THINKING:
            state = self.onThinking(state)
            state.current_state = state.ACTING
        
        if state.current_state == state.ACTING:
            state = self.onActing(state)
            # onActing 方法内部会根据情况设置下一个状态
            # 可能是 SENSING（继续循环）或 END（结束循环）
        
        return state
    
    def onSensing(self, state: AgentState) -> AgentState:
        """感知状态处理"""
        try:
            event = state.agent.stemQueue.get_nowait()
            # print(f"收到的事件: {event}")
            
            # 处理系统停止事件
            if event.getEventType() == SensoryEvent.ENV and event.message == "stop":
                state.messages.append(AIMessage(content="正在停止..."))
                state.current_state = AgentState.END
                return state
            
            # 处理内部事件，继续执行现有pattern
            if event.getEventType() == SensoryEvent.INNER:
                # 如果内部事件携带了行为模式，则更新当前模式
                pattern = event.getBehaviorPattern()
                if pattern:
                    state.memory.currentPattern = pattern
                state.current_state = AgentState.PERCEIVING
                return state
            
            # 处理环境事件或消息事件
            if event.getEventType() in [SensoryEvent.ENV, SensoryEvent.MESSAGE]:
                state.messages.append(HumanMessage(content=event.message))
                state.current_state = AgentState.PERCEIVING
                return state
            
        except queue.Empty:
            state.current_state = AgentState.END
            return state
        
        return state
    
    def onPerceiving(self, state: AgentState) -> AgentState:
        """认知状态处理"""
        current_pattern = state.memory.currentPattern
        last_message = state.messages[-1].content if state.messages else ""
        
        # 生成pattern推导
        pattern_prompt = self.pattern_prompt.format(
            input=last_message,
            action_descriptions=self.action_actuator.getActionDescriptions()
        )
        print(f"pattern_prompt: {pattern_prompt}")
        pattern_response = self.llm.invoke(pattern_prompt)
        print(f"pattern_response: {pattern_response}")
        thought, first_action, steps = self._parsePatternResponse(pattern_response.content)
        
        if current_pattern and current_pattern.getCurrentStep():
            # 如果已有pattern，记录推导结果但继续使用当前pattern
            current_step = current_pattern.getCurrentStep()
            state.memory.recordCurrentStep(
                thought=thought,
                actionName=current_step.actionName
            )
        else:
            # 无pattern则创建新的pattern
            state.memory.startNewPattern(
                patternId=f"task_{int(time.time())}",
                instructions=steps
            )
            # 记录第一个步骤
            state.memory.recordCurrentStep(
                thought=thought,
                actionName=first_action
            )
        
        state.current_state = AgentState.THINKING
        return state
    
    def onThinking(self, state: AgentState) -> AgentState:
        """思考状态处理"""
        # 暂时简单处理，直接转到行动状态
        state.current_state = AgentState.ACTING
        return state
    
    def onActing(self, state: AgentState) -> AgentState:
        """行动状态处理"""
        current_step = state.memory.currentPattern.getCurrentStep()
        if not current_step:
            state.current_state = AgentState.END
            return state
        
        # 执行当前action
        action = self.action_actuator.getAction(current_step.actionName)
        if action:
            result = action.func(parsed_output.memo_name, parsed_output.content)
            state.memory.setCurrentStepResult(result)
            
            response_message = AIMessage(content=f"{current_step.thought}\n执行结果: {result}")
            state.messages.append(response_message)
            print(f"[{state.agent.name}]: {response_message.content}")
        
        # 检查是否有下一步
        next_step = state.memory.moveToNextStep()
        if next_step:
            # 生成内部事件，继续执行pattern
            state.agent.stemQueue.put(SensoryEvent(
                message="continue_pattern",
                eventType=SensoryEvent.INNER,
                source="system",
                behaviorPattern=state.memory.currentPattern  # 传递当前行为模式
            ))
            state.current_state = AgentState.SENSING
        else:
            # 完成当前pattern
            state.memory.completeCurrentPattern()
            state.current_state = AgentState.END
        
        return state
    
    def _parsePatternResponse(self, content: str) -> Tuple[str, str, List[str]]:
        """解析模式响应
        返回: (思考过程, 第一个动作名称, 步骤列表)
        """
        lines = content.split('\n')
        thought = ""
        first_action = ""
        steps = []
        
        for line in lines:
            if line.startswith("思考过程："):
                thought = line.replace("思考过程：", "").strip()
            elif line.startswith("第一个动作："):
                first_action = line.replace("第一个动作：", "").strip()
            elif line.strip().startswith(('1.', '2.', '3.')):
                step = line.split('.', 1)[1].strip()
                steps.append(step)
        
        return thought, first_action, steps

class StateMachineAgent(BaseAgent):
    """提供基本状态机实现的Agent"""
    PROCESS = "process"
    
    def __init__(self, name: str, 
                 processFunc: Callable[[AgentState], AgentState],
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
        time.sleep(0.1)

    def _createStateMachine(self)->CompiledStateGraph:
        """创建状态机"""
        stateMachine = StateGraph(AgentState)
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
        print(f"\n[系统] {self.name} 已启动，等待输入...")
        while not self.isReqStop:
            
            state = {
                "messages": [],
                "current_state": AgentState.SENSING,
                "agent": self,
                "memory": AgentMemory()
            }
            print(f"当前状态: {state}")
            self.stateMachine.invoke(state, config=RunnableConfig(recursion_limit=10))
            self.runtimeIdleFunc()
        print(f"\n[系统] {self.name} 已停止.")

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
            Tool(
                name="重命名备忘",
                func=MemoActions.renameMemo,
                description="将指定名称的备忘录重命名为新名称。需要输入旧的备忘录名称和新的备忘录名称。"
            ),
            Tool(
                name="读取备忘",
                func=MemoActions.readMemo,
                description="读取指定名称备忘录的内容。输入备忘录名称。"
            )
        ]
        processor.action_actuator.setActions(actions)
        
        agent = StateMachineAgent(
            name=name,
            processFunc=processor.process
        )
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
    
    def test_env_event():
        """测试环境事件触发的Agent"""
        env = AgentEnvironment("thread_pool")
        try:
            agent = env.createAgent("资源管理助手")
            time.sleep(1)
            
            # 发送环境事件
            agent.senseEnvironmentEvent(command="rename_memo", 
                                memo_name="旧备忘录",
                                new_name="新备忘录")
            
            time.sleep(15)  # 等待处理完成
            
        except KeyboardInterrupt:
            print("\n[系统] 接收到中断信号，正在停止...")
        finally:
            env.stopAll()
    
    if not os.getenv("OPENAI_API_KEY"):
        raise ValueError("请在.env文件中设置OPENAI_API_KEY")
    
    test_env_event()
