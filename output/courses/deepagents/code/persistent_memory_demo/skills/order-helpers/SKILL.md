---
name: order-helpers
description: 当需要对订单记录进行清洗、按状态分组、统计金额或生成订单摘要时使用。
module: index.ts
---

# order-helpers

这是一个可被解释器按需加载的 Skill。

适用场景：
- 订单记录很多，模型不适合手写分组逻辑时
- 需要稳定、可复用的分组和汇总函数时

在解释器中导入：

```typescript
const { groupByStatus, summarizeOrders } = await import("@/skills/order-helpers");
```
