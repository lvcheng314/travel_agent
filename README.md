# 基于多智能体编排的旅行智能决策系统

> 面向旅行场景的智能决策系统，融合多智能体协作、RAG 知识库、用户记忆和插件化 Skill 架构，为用户提供从需求理解到行程生成的一站式服务。

- **项目类型**：多智能体 Agent 应用 / 旅行智能决策系统
- **核心技术**：Python、LangChain、LangGraph、AgentScope、Milvus、BGE-m3、Redis、Streamlit

## 项目背景

传统旅行规划需要用户在景点、攻略、酒店、交通和企业差旅政策等多个平台之间切换，信息分散、决策成本高。初版 Agent 系统采用串行调度和关键词匹配，意图识别准确率约 65%，平均响应时间约 30 秒，也无法持续记忆用户偏好或查询企业知识。

## 解决方案

### 多智能体协作与 LangGraph 编排

- 使用 LangGraph 构建“意图识别 → 任务编排 → Agent 执行 → 结果聚合”的状态图，将业务流程显式化，支持可观测、可扩展的节点编排。
- 实现多意图识别，根据任务优先级进行分组，同优先级任务并行执行，不同优先级任务按顺序推进。
- 支持事项收集、偏好管理、知识问答、信息查询、行程规划和记忆查询六类 Agent 能力。
- 保留统一的 Agent 调用协议，便于后续接入更多旅行和企业服务能力。

### 两层记忆系统与 Redis 缓存

- 设计短期记忆和长期记忆：短期记忆保存当前会话上下文，长期记忆保存用户偏好、历史行程等稳定信息。
- 引入异步 LLM 总结机制，结合置信度、时间衰减和优先级管理记忆有效性。
- 针对冲突偏好设计覆盖、追加和优先级策略，避免新旧偏好相互覆盖或失真。
- 使用 Redis 缓存用户偏好热数据和 LLM 总结结果，缓存命中率达到 85%。

### RAG 企业知识库

- 基于 Milvus 构建向量检索库，使用 BGE-m3 Embedding 对差旅政策、城市攻略和 FAQ 文档进行向量化。
- 采用余弦相似度召回，并返回文档来源，支持回答溯源和结果解释。
- 对低相似度、无结果和特殊场景提供兜底处理，降低知识库问答幻觉风险。

### Skill Plugins 插件化架构

- 实现 `LazyAgentRegistry` 动态发现机制，自动扫描 Skill 目录并加载 Agent 插件。
- 通过懒加载降低系统启动成本，仅在任务实际触发时初始化对应 Agent。
- 采用渐进式暴露机制，系统启动速度优化至约 3 秒，新增能力无需修改核心编排逻辑。

### 行程状态管理

- 设计 `drafting`、`upcoming`、`completed`、`cancelled` 四态状态机，统一管理行程生命周期。
- 使用“读时派生”替代分散的写时状态流转，减少状态不一致和重复更新问题。

## 系统架构

```text
用户输入
   │
   ▼
Streamlit / CLI
   │
   ▼
LangGraph Workflow
   ├── 意图识别与 Query 改写（LangChain Model）
   ├── 优先级路由与并行调度
   ├── Skill Plugins / LazyAgentRegistry
   │    ├── 事项收集
   │    ├── 偏好管理
   │    ├── 信息查询
   │    ├── RAG 知识问答
   │    ├── 记忆查询
   │    └── 行程规划
   ├── 短期记忆 / 长期记忆 / Redis
   └── Milvus + BGE-m3 知识库
   │
   ▼
结构化结果、行程卡片与来源信息
```

## 核心指标

| 指标 | 初版 | 优化后 |
|---|---:|---:|
| 意图识别准确率 | 65% | 90%+ |
| 知识库问答准确率 | - | 95% |
| 用户偏好记忆准确率 | - | 95% |
| 平均响应时间 | 30 秒 | 约 20 秒 |
| Redis 缓存命中率 | - | 85% |
| 系统启动时间 | - | 约 3 秒 |

## 项目结构

```text
.
├── agents/                 # 意图识别、编排与懒加载 Agent 注册器
├── context/                # 短期记忆、长期记忆和记忆管理器
├── .claude/skills/         # 可插拔业务 Agent
├── langgraph_workflow.py   # LangGraph 状态图与 LangChain Runnable 适配层
├── web_app.py              # Streamlit 可视化界面
├── cli.py                  # CLI 交互入口
├── data/                   # 本地模型、记忆和知识库数据
├── tests/                  # Agent、编排和记忆系统测试
└── requirements.txt        # 项目依赖
```

## 运行方式

### 安装依赖

```powershell
.venv\Scripts\pip.exe install -r requirements.txt
```

### 启动可视化界面

```powershell
.venv\Scripts\python.exe -m streamlit run web_app.py
```

### 启动命令行界面

```powershell
.venv\Scripts\python.exe cli.py
```

## 个人职责

- 负责多智能体系统整体架构设计和核心编排流程实现。
- 设计短期记忆、长期记忆、Redis 缓存及冲突偏好处理机制。
- 搭建 Milvus + BGE-m3 RAG 知识库，实现检索、溯源和异常兜底。
- 实现多意图识别、优先级路由、并行调度和结果聚合。
- 设计 `LazyAgentRegistry` Skill Plugins 插件化机制，降低新增 Agent 的接入成本。
- 设计行程四态状态机，统一行程生命周期管理。
- 完成 CLI 与 Streamlit 双入口，并补充 Agent、编排和记忆系统测试。
