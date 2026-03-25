export default function StatsBar({ stats, nodeCount, edgeCount }) {
  const fmt = (n) => n ? Number(n).toLocaleString('en-IN', { maximumFractionDigits: 0 }) : '—'
 // const fmtAmt = (n) => n ? `${stats.currency || ''} ${Number(n).toLocaleString('en-IN', { maximumFractionDigits: 0 })}` : '—'

  const items = [
    { label: 'Sales Orders', value: fmt(stats.sales_order_headers), icon: '📋' },
    { label: 'Billing Docs', value: fmt(stats.billing_document_headers), icon: '📄' },
    { label: 'Deliveries', value: fmt(stats.outbound_delivery_headers), icon: '🚚' },
    { label: 'Payments', value: fmt(stats.payments), icon: '💳' },
    { label: 'Products', value: fmt(stats.products), icon: '📦' },
    { label: 'Customers', value: fmt(stats.business_partners), icon: '👤' },
    { label: 'Graph Nodes', value: fmt(nodeCount), icon: '●' },
    { label: 'Graph Edges', value: fmt(edgeCount), icon: '→' },
  ]

  return (
    <div className="stats-bar">
      {items.map((item, i) => (
        <div key={i} className="stat-item">
          <span className="stat-icon">{item.icon}</span>
          <div>
            <div className="stat-value">{item.value}</div>
            <div className="stat-label">{item.label}</div>
          </div>
        </div>
      ))}
    </div>
  )
}
