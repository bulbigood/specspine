# 事件接入

## 职责

本文拥有事件 envelope、分区路由和接入确认规则。生产者必须提供 `event_id`、
`event_type`、`occurred_at` 与 schema version。相同业务实体使用稳定 partition key，
以保持分区内顺序。

接入网关只做结构校验和身份验证，不决定字段兼容性，也不计算窗口水位线。
成功响应表示事件已持久写入输入日志，不表示下游 sink 已提交。

## 关系

- [模式注册中心](schema-registry.md)
- [事件时间](event-time.md)
- [数据质量](data-quality.md)
