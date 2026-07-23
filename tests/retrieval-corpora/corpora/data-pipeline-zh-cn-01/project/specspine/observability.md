# 可观测性

## 职责

平台指标包括输入速率、consumer lag、watermark delay、checkpoint duration、
失败规则数和 sink commit latency。日志使用 run id、checkpoint id 与 dataset id
关联，trace 只覆盖控制面和跨服务调用。

仪表盘展示迟到事件数量和回填进度，但指标维度禁止使用用户标识、邮箱或手机号。
告警负责发现异常，不拥有迟到处理、脱敏或恢复语义。

## 关系

- [隐私脱敏](privacy-masking.md)
- [容量管理](capacity-planning.md)
- [故障处置](incident-response.md)
