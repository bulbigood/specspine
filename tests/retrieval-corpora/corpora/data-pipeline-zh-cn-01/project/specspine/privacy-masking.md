# 隐私脱敏

## 职责

本文拥有 PII 识别、字段脱敏和令牌化规则。邮箱、手机号和政府证件号在进入分析层前
必须处理：可关联分析使用 deterministic tokenization，不需要关联的字段使用不可逆
redaction。原始值只允许停留在受限 raw zone。

日志、metric label 和 trace attribute 禁止包含 PII；排障样本必须经过同一套
masking policy。脱敏失败时事件进入受限隔离区，不能降级为明文输出。

## 关系

- [事件接入](event-ingestion.md)
- [可观测性](observability.md)
- [数据保留](data-retention.md)
