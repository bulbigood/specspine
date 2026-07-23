# 流萤实时数据平台架构

## 目标

流萤接收业务事件，完成校验、窗口聚合、隐私处理，并把结果写入分析仓库。
流式任务和批量回填共用数据契约，但具有独立的资源与进度边界。

## 架构地图

### 输入与契约

- [事件接入](event-ingestion.md) — 接入协议、分区键和初始校验。
- [模式注册中心](schema-registry.md) — Schema 兼容性和版本演进。
- [运行配置](runtime-configuration.md) — 配置发布、动态参数与密钥边界。

### 流处理语义

- [事件时间](event-time.md) — 水位线、迟到事件和时间戳规则。
- [窗口聚合](window-aggregation.md) — 窗口类型、触发器和修正输出。
- [检查点恢复](checkpoint-recovery.md) — checkpoint、状态快照和故障恢复。
- [精确一次写入](exactly-once-sinks.md) — sink 事务、幂等键和提交协议。

### 数据治理与批处理

- [批量回填](backfill.md) — 历史重放、隔离和流量控制。
- [隐私脱敏](privacy-masking.md) — PII 分类、令牌化和日志边界。
- [数据质量](data-quality.md) — 质量规则、隔离区和告警。
- [数据保留](data-retention.md) — 热数据、归档与删除期限。

### 运维

- [可观测性](observability.md) — 指标、日志和 trace 关联。
- [容量管理](capacity-planning.md) — 并行度、积压和扩缩容。
- [故障处置](incident-response.md) — 降级、暂停与恢复流程。

## 系统轮廓

接入层先验证 envelope，再把不可变事件写入日志。处理器以 event time 计算结果，
通过 checkpoint 对齐状态与输入位置。所有外部写入遵循各 sink 自己的提交协议。
