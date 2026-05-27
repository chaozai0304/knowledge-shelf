interface Order {
  id: string;
  status: string;
  amount: number;
}

export function groupByStatus(orders: Order[]) {
  return orders.reduce<Record<string, Order[]>>((acc, order) => {
    acc[order.status] = acc[order.status] ?? [];
    acc[order.status].push(order);
    return acc;
  }, {});
}

export function summarizeOrders(orders: Order[]) {
  const total = orders.reduce((sum, order) => sum + order.amount, 0);
  const byStatus = groupByStatus(orders);
  return {
    count: orders.length,
    total,
    statusCounts: Object.fromEntries(
      Object.entries(byStatus).map(([status, rows]) => [status, rows.length]),
    ),
  };
}
