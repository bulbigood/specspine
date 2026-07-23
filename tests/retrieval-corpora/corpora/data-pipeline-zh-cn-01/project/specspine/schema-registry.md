# 模式注册中心

## 职责

注册中心拥有 Schema 版本演进和兼容性判定。默认采用 backward compatibility：
新 reader 必须能读取上一主版本写出的数据。新增字段必须有默认值；删除字段前要
经过两个发布周期的 deprecated 阶段。字段改名被视为“新增加删除”，不能原地修改。

兼容性检查发生在 schema 发布时，事件接入只验证已注册的版本号。紧急豁免需要
数据平台主管批准，并记录到审计日志。

<!-- specspine:semantic-ids:begin -->
## 决策

- **CON-schema-backward-default** — 默认兼容策略为 backward compatibility，
  且新增字段必须提供默认值。
<!-- specspine:semantic-ids:end -->

## 关系

- [事件接入](event-ingestion.md)
- [数据质量](data-quality.md)
