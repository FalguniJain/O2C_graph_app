const TYPE_COLORS = {
  SalesOrder: '#3b82f6', SalesOrderItem: '#06b6d4',
  BillingDocument: '#8b5cf6', Delivery: '#10b981',
  Payment: '#f59e0b', JournalEntry: '#ef4444',
  Customer: '#ec4899', Product: '#84cc16',
}

export default function NodeModal({ data, onClose }) {
  if (!data || !data.node) return null
  const { node, edges, connected_nodes } = data
  const color = TYPE_COLORS[node.type] || '#64748b'

  const grouped = {}
  for (const e of edges) {
    if (!grouped[e.relation]) grouped[e.relation] = []
    const otherId = e.source === node.id ? e.target : e.source
    const other = connected_nodes.find(n => n.id === otherId)
    if (other) grouped[e.relation].push(other)
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal" onClick={e => e.stopPropagation()}>
        <div className="modal-header" style={{ borderColor: color }}>
          <div className="modal-type-badge" style={{ background: color }}>
            {node.type}
          </div>
          <h2 className="modal-title">{node.label}</h2>
          <button className="modal-close" onClick={onClose}>×</button>
        </div>

        <div className="modal-body">
          <div className="modal-section">
            <h3>Properties</h3>
            <div className="props-grid">
              {Object.entries(node.properties || {}).map(([k, v]) => (
                <div key={k} className="prop-row">
                  <span className="prop-key">{k}</span>
                  <span className="prop-val">{String(v ?? '—')}</span>
                </div>
              ))}
            </div>
          </div>

          {Object.keys(grouped).length > 0 && (
            <div className="modal-section">
              <h3>Connections ({edges.length})</h3>
              {Object.entries(grouped).map(([rel, nodes]) => (
                <div key={rel} className="conn-group">
                  <div className="conn-relation">{rel}</div>
                  {nodes.slice(0, 5).map(n => (
                    <div key={n.id} className="conn-node">
                      <span className="conn-dot" style={{ background: TYPE_COLORS[n.type] || '#64748b' }} />
                      <span className="conn-label">{n.label}</span>
                      <span className="conn-type">{n.type}</span>
                    </div>
                  ))}
                  {nodes.length > 5 && (
                    <div className="conn-more">+{nodes.length - 5} more</div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
