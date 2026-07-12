# Agent 与 LLM 应用知识

## Agent 和普通 Chatbot 的区别
考察点：是否理解 Agent 的任务执行能力。

回答要点：
- 普通 Chatbot 主要根据上下文生成回答。
- Agent 更强调目标、任务拆解、工具调用和多步骤执行。
- 多 Agent 可以把复杂任务拆成多个角色，例如 JD 分析、简历分析、评分、报告生成。

项目追问：
- 为什么项目中不把所有逻辑放进一个 Prompt？
- 多 Agent 是否一定比单 Agent 好？有什么成本？

## Tool Calling / Function Calling
考察点：是否理解模型和外部系统交互。

回答要点：
- Tool Calling 让模型在需要时调用搜索、数据库、解析器等工具。
- 工具结果应被后端校验，不能完全相信模型选择。
- 对外部工具要限制参数和权限，避免安全风险。

项目追问：
- Tavily 搜索结果为什么不能直接交给模型？
- 为什么要对岗位做过期识别和 freshness_score？

## 多 Agent 编排
考察点：是否理解任务上下文传递。

回答要点：
- JD Agent 负责提取岗位要求。
- Resume Agent 负责分析候选人能力。
- Score Agent 负责匹配评分和证据。
- Report Agent 负责生成最终结构化结果。

项目追问：
- CrewAI 中 Agent、Task、Crew 的关系是什么？
- context 参数在任务之间起什么作用？

## 降低幻觉
考察点：是否理解 AI 应用可靠性。

回答要点：
- 用 Pydantic schema 限制输出结构。
- 要求 evidence 来自简历、JD 或岗位画像。
- 保存 raw_result、parsed_result、parse_status 方便追踪。
- 对解析失败做 fallback，而不是让接口直接崩溃。

项目追问：
- 为什么 AI 应用的难点不是调通模型，而是稳定控制输出？
- 如何避免模型编造用户没有的项目经历？
