# ANAN Jumpin - 您，超级个体，智效启动

ANAN Jumpin 是一款面向**AI能效达人及超级个体**的PC端AI效率工具与平台；旨在迅速触达AI，一招即用、一切插件、一台Laptop掌控智效，在您本地聚合属于您自己的AI能力；

## 🤔 "我如何用？"
基础使用，进阶使用，定制开发，深度贡献；

### 👨‍💻 “我是，程序小白，就想用AI提效”：
- 启动后使用内置AI对话等功能体验AI；（可全局热键）
- 切换内置Applet功能来使用，常用的AI、Agent或提效应用；
- 获取安装社区插件扩展功能或Applet来使用；
- 提出建议、issue，帮助Jumpin提升；

### 🛠️ “我是，IT、AI能效爱好者，喜欢折腾工具提升自我”：
- 使用内置或扩展的Applet、插件使用他们的AI智效能力加速工作与学习；
- 修改配置文件自定义行为；
- 修改现有插件功能，简单定制自己个性插件；
- 运行学习all in 1 file主干程序，可快速学习体验基于LLM的AI、Agent的程序实现；
- 提出建议、issue，帮助Jumpin提升；

### 🎯 “我是，AI/程序开发者达人”：
- 使用内置或扩展的Applet、插件使用他们的AI智效能力加速工作与学习； 
- 运行学习all in 1 file主干程序，可快速学习体验基于LLM的AI、Agent的程序实现；
- 开发专业AI应用插件，引入新功能或基建资源，并设计定制Applet功能套件
- 集成自有AI模型和工具链，AI基础建设与Jumpin应用建设互相推动闭环提升；
- 分享插件提升收益；
- 插件精化，帮助沉淀至主干程序。

### 🚀 “我是，超级个体”：
- 能够进行“AI/程序开发者达人”对应的所有事项；
- 打造自身领域个性化AI化工作流，极限提效自身，完成10倍效率，拿到原需整个团队的成果；
- 整合各类功能套件，形成某个或多个行业或领域通用，可标准化的Applet应用套件与插件；
- 形成个人AI化效率体系系统，在Jumpin上能进行，知识数据，运作流程，智能体的整体沉淀，方案级甚至方法论成果达成与沉淀；分享与销售推广。

## 🌟 主要特性
- 🔑 **一招即用**: 热键唤起/隐藏，热键切换AI、Applet套件能力；
- 📝 **轻量安全**: 默认本地极致轻量部署，个人数据安全有保障；
- 🚀 **提速学AI**: all in 1 file 代码主干，可快速学习体验LLM为基础的AI、Agent；快速学习扩展插件的开发；
- 🎯 **聚合聚焦**: AI、Agent、多Agent等能力均聚合至Applet直达应用目标；
- 🔌 **一切插件**: 通过插件安装，可以获取需要的所有性能力；
- 🎨 **可高定制**: 支持自定义界面、AI资源、其他工具资源几乎所有模块组件；
- 💬 **其他基础**: 可支持RAG，ai-agent等、流程化多agent等AI平台设施范式，支持OpenAI，Ollama等各类LLM基座框架接入，支持Ollama本地维护。

## 🚀 快速开始

### ⚙️ 快速运行all in 1 file版（非安装） 
安装依赖

```bash
pip install -r requirements.txt
```

配置

1. 创建 `.env` 文件并配置你的OpenAI API密钥:
```
OPENAI_API_KEY=<your_api_key_here>
OPENAI_BASE_URL=<baseurl,http://xxx/v1>
```

2. 运行“all in 1 file”的内置主程序:
```bash
python ananxw_jumpin_allin1f.py
```

### ⚙️ 快速安装运行 
（建设中...）

### ⚙️ 快速配置
默认使用环境变量配置或 `.env` 中设置环境变量配置，默认为OpenAI api需要。**可以不做任何其他配置，均会使用默认参数。**

更多配置：
- 命令行配置： 
- 支持文件配置：

### 🛠️ 快速使用
基本操作：
- 使用全局快捷键（默认为 `Alt+c` ）呼出/隐藏主界面
- 在输入框中输入内容与AI对话（默认为是通过环境变量或.env配置LLM接入，使用）
- 已提供系统托盘，可访问更多功能。

Applet切换：  
- 程序支持多个Applet，每个Applet可以提供不同的功能。使用界面坐上角Applet切换（或默认快捷键 `Tab` ）在不同Applet间切换。


## 🔧 开发者快速指南

主干程序均在[`ananxw_jumpin_allin1f.py`](ananxw_jumpin_allin1f.py)文件实现。如当前版本迭代后如未及时更新说明，请按照实际代码为准。
### 📦 主要外部依赖
- python 3.9+
- pyside6：界面主要为qt开发；
- pynput：全局快捷键；
- openai-api：AI-LLM对接；
- langchain：AI建设；

### 📝 插件开发

1. 在内置插件文件（默认为ananxw_jumpin包下的`builtin_plugins.py`，）中增加插件类。
1. 创建新的插件类继承 `AAXWAbstractPlugin`；
2. 重写必要的接口方法，如：
3. 启动主干程序自动扫描加载并安装插件；

```python
class MyPlugin(AAXWAbstractPlugin):
    @override
    def onInstall(self):
        """
        插件安装时的回调方法
        建议实现:
            - 初始化插件所需的资源
            - 注册插件提供的服务到DI容器
            - 设置插件的配置信息
            - 创建必要的UI组件
        """
        pass

    @override
    def onUninstall(self):
        """
        插件卸载时的回调方法
        建议实现:
            - 清理插件创建的资源
            - 从DI容器注销服务
            - 保存配置信息
            - 移除UI组件
        """
        pass

    @override
    def enable(self):
        """
        启用插件功能时的回调方法
        建议实现:
            - 激活插件的功能
            - 显示插件的UI组件
            - 注册事件监听器
            - 启动后台服务
        """
        pass
    @override
    def disable(self):
        """
        禁用插件功能时的回调方法
        建议实现:
            - 停用插件的功能
            - 隐藏插件的UI组件
            - 注销事件监听器
            - 停止后台服务
        """
        pass
```

- 插件机制支持用户插件目录，默认在程序运行当前目录，其插件默认为plugin_前缀的py文件；**（目录变更或开关用户插件目录加载，需要进行配置或自定义main来完成修改）**

### 📝 Applet开发（插件方式）

1. 继承 `AAXWAbstractApplet` 类；
2. 实现必要的界面和功能逻辑；
3. 关联到某个插件或自定义新的插件；
4. 在插件中获取`AppletManager`并用其`addApplet()`方法加入你的Applet；

### 📝 详细说明以及参考：
（建设中...）

### 🔍 示例代码与样例：

1. 内置的插件样例，附加输入框的快键键功能等（位置可能会有变化）：   
[`ananxw_jumpin_allin1f.py #L2486 AAXWJumpinDefaultBuiltinPlugin` ](ananxw_jumpin_allin1f.py#L2486) # 内置插件实现样例

2. 内置的Applet样例，1个由插件去加载的简单applet实现~~ollama访问~~ （位置可能会有变化）；
[`ananxw_jumpin_allin1f.py #L2440 AAXWJumpinDefaultSimpleApplet` ](ananxw_jumpin_allin1f.py#L2440) # 内置applet样例

3. 内置的Applet样例，默认applet实现各种默认主要应用功能（位置可能会有变化）；
[`ananxw_jumpin_allin1f.py #L2440 AAXWJumpinDefaultCompoApplet` ](ananxw_jumpin_allin1f.py#L2578) # 内置applet样例

## 📝 版本历史与计划

- v0.5+: 增加可切换Applet功能，完善插件框架与机制；
- v0.4+: 增加工作目录配置，日志功能，简易注入框架
- v0.3+: 增加Markdown展示气泡
- v0.2+: 增加托盘功能，支持全局热键

### 🌈 计划与路线概要
v0.6+ 计划
- 增加通用工具消息面板和展示功能面板
- 增加Ollama管理功能
- 完成打包与发布版初步建设
- 完善项目文档与二次开发说明

v0.7+ 计划  
- 集成密塔等搜索功能(插件方式)
- coze集成对接应用样例；
- dify集成对接样例；
- 流程化或工作流、调度器集成；


## 🤝 贡献

欢迎提交Issue和Pull Request！

## 📄 许可证

 ananxw_jumpin(ANAN Jumpin，安安将品) is open source and licensed under [Apache 2.0](LICENSE)

## 👨‍💻 作者

小王同学 wfeng007 (wfeng007@163.com) B站:小王同学009

