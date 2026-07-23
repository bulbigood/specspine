# 精确一次写入

## 职责

本文拥有外部 sink 的 exactly-once 提交协议。支持事务的仓库使用两阶段提交：
checkpoint 期间 prepare，只有对应 checkpoint 完成后才 commit。恢复时先核对
transaction id，再提交或回滚悬挂事务。

不支持事务的目标使用 `event_id + transform_version` 作为幂等键执行 upsert。
批量重放必须使用独立 run id，但不能绕过幂等键。网络重试可以重复发送请求，
不能产生重复可见结果。

## 关系

- [检查点恢复](checkpoint-recovery.md)
- [批量回填](backfill.md)
- [数据质量](data-quality.md)
