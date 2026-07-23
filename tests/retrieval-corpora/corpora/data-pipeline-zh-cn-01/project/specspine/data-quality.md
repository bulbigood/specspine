# 数据质量

## 职责

质量服务运行完整性、唯一性、取值范围和跨字段一致性规则。硬规则失败进入 quarantine，
软规则失败保留数据并产生告警。规则结果记录 dataset、rule version 与 sample count。

质量检查覆盖实时事件与回填结果，但不定义 schema compatibility，也不决定 watermark。
回填只有通过阻断级规则后才能从 staging 发布。

## 关系

- [模式注册中心](schema-registry.md)
- [批量回填](backfill.md)
- [可观测性](observability.md)
