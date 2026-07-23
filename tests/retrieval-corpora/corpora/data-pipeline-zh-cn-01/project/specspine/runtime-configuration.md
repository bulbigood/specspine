# 运行配置

## 职责

配置服务发布任务并行度、批量大小、连接端点和功能开关。动态配置通过带版本的
snapshot 生效；任务只在 checkpoint 边界切换版本，避免同一批次读取两套参数。

密钥只保存引用，不进入普通配置或日志。配置服务可以调整延迟阈值和容量参数，
但不拥有 schema 兼容策略、迟到事件语义或 sink 提交规则。

## 关系

- [检查点恢复](checkpoint-recovery.md)
- [容量管理](capacity-planning.md)
- [故障处置](incident-response.md)
