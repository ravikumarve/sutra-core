const orders = [
  {
    id: "#INV-0042",
    customer: "Sharma Textiles",
    items: "50x Silk Saree (Red)",
    amount: "₹1,24,500",
    status: "completed",
    time: "2 min ago",
  },
  {
    id: "#INV-0041",
    customer: "Gupta Kirana Store",
    items: "25kg Basmati Rice, 10L Oil",
    amount: "₹3,850",
    status: "completed",
    time: "15 min ago",
  },
  {
    id: "#INV-0040",
    customer: "Patel Hardware",
    items: "100x PVC Pipe 1inch",
    amount: "₹8,200",
    status: "processing",
    time: "42 min ago",
  },
  {
    id: "#INV-0039",
    customer: "Singh Electronics",
    items: "5x LED Bulb 12W",
    amount: "₹2,250",
    status: "pending",
    time: "1 hr ago",
  },
  {
    id: "#INV-0038",
    customer: "Verma Fabrics",
    items: "20m Cotton (Blue), 15m Polyester",
    amount: "₹11,300",
    status: "completed",
    time: "2 hr ago",
  },
];

const statusStyles: Record<string, string> = {
  completed: "bg-emerald-dim text-emerald border-emerald/20",
  processing: "bg-[rgba(0,240,255,0.08)] text-cyan-400 border-cyan-400/20",
  pending: "bg-[rgba(245,158,11,0.08)] text-amber-400 border-amber-400/20",
};

export function RecentOrders() {
  return (
    <div className="bg-bg-surface border border-border-dim rounded-xl overflow-hidden">
      <div className="px-6 py-5 border-b border-border-dim flex items-center justify-between">
        <h3 className="text-base font-semibold text-text-main">Recent Orders</h3>
        <a href="/dashboard/orders" className="text-xs font-mono text-emerald hover:underline">
          View all →
        </a>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-border-dim">
              <th className="text-left px-6 py-3.5 font-mono text-[0.65rem] text-text-faint uppercase tracking-wider">
                Order
              </th>
              <th className="text-left px-6 py-3.5 font-mono text-[0.65rem] text-text-faint uppercase tracking-wider">
                Customer
              </th>
              <th className="text-left px-6 py-3.5 font-mono text-[0.65rem] text-text-faint uppercase tracking-wider max-md:hidden">
                Items
              </th>
              <th className="text-right px-6 py-3.5 font-mono text-[0.65rem] text-text-faint uppercase tracking-wider">
                Amount
              </th>
              <th className="text-right px-6 py-3.5 font-mono text-[0.65rem] text-text-faint uppercase tracking-wider">
                Status
              </th>
            </tr>
          </thead>
          <tbody>
            {orders.map((order) => (
              <tr
                key={order.id}
                className="border-b border-border-dim last:border-b-0 hover:bg-bg-panel/50 transition-colors"
              >
                <td className="px-6 py-4 font-mono text-text-main text-xs">{order.id}</td>
                <td className="px-6 py-4 text-text-main">{order.customer}</td>
                <td className="px-6 py-4 text-text-muted text-xs max-md:hidden">{order.items}</td>
                <td className="px-6 py-4 text-right font-mono text-text-main text-sm">{order.amount}</td>
                <td className="px-6 py-4 text-right">
                  <span
                    className={`inline-block px-2.5 py-1 rounded-full text-[0.65rem] font-mono font-medium border ${
                      statusStyles[order.status]
                    }`}
                  >
                    {order.status}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
