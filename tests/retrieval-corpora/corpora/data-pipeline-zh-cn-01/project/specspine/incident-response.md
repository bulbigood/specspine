# 故障处置

## 职责

值班人员可以暂停 sink 提交、停止新的回填并固定任务并行度。暂停输入仅用于数据损坏
风险；普通下游故障应保留输入日志并让 consumer lag 可见。

恢复顺序是验证最近完整 checkpoint、恢复单个 canary 任务、核对 sink 提交记录，
最后逐步恢复流量。事故期间不得关闭 PII masking 或绕过 schema compatibility。

## 关系

- [检查点恢复](checkpoint-recovery.md)
- [可观测性](observability.md)
- [运行配置](runtime-configuration.md)
