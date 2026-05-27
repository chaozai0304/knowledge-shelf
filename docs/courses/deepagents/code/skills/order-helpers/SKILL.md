---
name: order-helpers
description: 当需要对订单记录进行清洗、按状态分组、统计金额或生成订单摘要时使用。
module: index.ts
---

# order-helpers

这个 skill 提供订单数据处理的确定性工具函数。适合在解释器里复用，避免模型每次重新写分组逻辑。

在解释器中导入：

```typescript
const { groupByStatus, summarizeOrders } = await import("@/skills/order-helpers");
```
