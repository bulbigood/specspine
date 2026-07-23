# 批量回填

## 职责

本文拥有历史 backfill（回填）和 replay（重放）的执行边界。每次回填创建独立
run id、独立 consumer group 和独立临时状态目录，禁止复用线上流任务的 checkpoint。

回填按日期分片，默认只使用集群 20% 的计算配额。结果先写 staging，完成质量检查后
再切换目标分区。取消回填只清理该 run 的临时资源，不移动线上消费位置。

## 关系

- [精确一次写入](exactly-once-sinks.md)
- [数据质量](data-quality.md)
- [容量管理](capacity-planning.md)
