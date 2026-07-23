# 窗口聚合

## 职责

聚合器拥有 tumbling window、sliding window 和 session window 的计算方式。
窗口由 event time 划分，watermark 到达时首次触发。允许迟到的数据产生带相同
aggregate key 和递增 revision 的 upsert 修正，而不是追加第二条最终记录。

窗口状态由 checkpoint 保存。业务团队选择窗口尺寸，但不能改变平台统一的
超迟数据隔离规则。

## 关系

- [事件时间](event-time.md)
- [检查点恢复](checkpoint-recovery.md)
- [精确一次写入](exactly-once-sinks.md)
