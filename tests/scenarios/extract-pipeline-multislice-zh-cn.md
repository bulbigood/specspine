# 场景：隔离回填与幂等输出

## User request

```text
我要重放一个月的历史数据。需要同时确认回填如何与线上任务隔离，以及重试写入时怎样避免产生重复可见结果；请覆盖
run、consumer group、checkpoint、幂等键和 staging 发布。请准备最小的架构 context
handoff，只把 SpecSpine 作为权威来源，不要修改项目文件。
```
