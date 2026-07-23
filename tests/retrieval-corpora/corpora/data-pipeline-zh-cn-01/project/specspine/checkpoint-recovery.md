# 检查点与恢复

## 职责

本文拥有 checkpoint 协调、状态快照和恢复顺序。协调器先注入 barrier，所有输入
对齐后生成状态快照，再持久化输入 offset。失败恢复必须从最后一个完整检查点同时
恢复状态和 offset；未完成快照不可用于恢复。

连续三次 checkpoint 超时后任务进入 degraded 状态，但不自动跳过状态。保存周期
默认 60 秒，至少保留最近三个完整快照。

<!-- specspine:semantic-ids:begin -->
## 决策

- **DEC-checkpoint-aligned-restore** — 状态快照与输入 offset 必须来自同一个已完成的
  aligned checkpoint。
<!-- specspine:semantic-ids:end -->

## 关系

- [窗口聚合](window-aggregation.md)
- [精确一次写入](exactly-once-sinks.md)
- [故障处置](incident-response.md)
