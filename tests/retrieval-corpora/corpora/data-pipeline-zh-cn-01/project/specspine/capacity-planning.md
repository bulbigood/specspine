# 容量管理

## 职责

容量控制器根据 consumer lag、处理速率和 checkpoint 开销调整并行度。扩容优先于
缩短 checkpoint 周期；缩容必须等待一次完整检查点。实时任务保留最低资源，
backfill 只能使用剩余配额。

热点分区需要先检查 partition key 倾斜，不能仅靠增加全局 worker 掩盖。资源预测使用
过去七天同时间段的峰值并保留 30% 余量。

## 关系

- [批量回填](backfill.md)
- [运行配置](runtime-configuration.md)
- [可观测性](observability.md)
