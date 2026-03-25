
import { useState, useEffect, useCallback } from 'react'
import GraphVisualization from './components/GraphVisualization'
import ChatPanel from './components/ChatPanel'
import StatsBar from './components/StatsBar'
import NodeModal from './components/NodeModal'
import './App.css'

const API_BASE = 'https://o2c-backend-tjki.onrender.com/api'

export default function App() {
  const [graphData, setGraphData] = useState({ nodes: [], edges: [] })
  const [stats, setStats] = useState({})
  const [loading, setLoading] = useState(true)
  const [selectedNode, setSelectedNode] = useState(null)
  const [highlightedNodes, setHighlightedNodes] = useState([])
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    Promise.all([
      fetch(`${API_BASE}/graph`).then(r => r.json()),
      fetch(`${API_BASE}/stats`).then(r => r.json())
    ]).then(([graph, statsData]) => {
      setGraphData(graph)
      setStats(statsData)
      setLoading(false)
    }).catch(() => {
      setError('Failed to connect to backend. Make sure the server is running on port 5000.')
      setLoading(false)
    })
  }, [])

  const handleNodeClick = useCallback(async (nodeId) => {
    try {
      const res = await fetch(`${API_BASE}/graph/node/${nodeId}`)
      const data = await res.json()
      setSelectedNode(data)
    } 
    catch {
      // node fetch failed silently
    }
  }, [])

  return (
    <div className="app">
      <header className="app-header">
        <div className="header-left">
          <button className="menu-btn" onClick={() => setSidebarOpen(!sidebarOpen)}>
            <span/><span/><span/>
          </button>
          <div className="breadcrumb">
            <span className="bc-parent">Analytics</span>
            <span className="bc-sep">/</span>
            <span className="bc-current">Order to Cash</span>
          </div>
        </div>
        <div className="logo-badge">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
            <circle cx="12" cy="12" r="3" fill="white"/>
            <circle cx="4" cy="5" r="2" fill="white" opacity=".7"/>
            <circle cx="20" cy="5" r="2" fill="white" opacity=".7"/>
            <circle cx="4" cy="19" r="2" fill="white" opacity=".7"/>
            <circle cx="20" cy="19" r="2" fill="white" opacity=".7"/>
            <line x1="12" y1="9" x2="6" y2="7" stroke="white" strokeWidth="1.5" opacity=".4"/>
            <line x1="12" y1="9" x2="18" y2="7" stroke="white" strokeWidth="1.5" opacity=".4"/>
            <line x1="12" y1="15" x2="6" y2="17" stroke="white" strokeWidth="1.5" opacity=".4"/>
            <line x1="12" y1="15" x2="18" y2="17" stroke="white" strokeWidth="1.5" opacity=".4"/>
          </svg>
          <span>O2C Graph</span>
        </div>
        <div className="header-right">
          <span className="live-dot"/>
          <span className="live-text">Live</span>
        </div>
      </header>

      {!loading && !error && (
        <StatsBar stats={stats} nodeCount={graphData.nodes.length} edgeCount={graphData.edges.length} />
      )}

      <div className="app-body">
        {loading ? (
          <div className="loading-screen">
            <div className="spinner"/>
            <p>Building knowledge graph…</p>
          </div>
        ) : error ? (
          <div className="error-screen">
            <div>⚠️</div>
            <h2>Connection Error</h2>
            <p>{error}</p>
            <code>cd backend && python app.py</code>
          </div>
        ) : (
          <>
            <div className="graph-wrapper">
              <GraphVisualization
                data={graphData}
                onNodeClick={handleNodeClick}
                highlightedNodes={highlightedNodes}
              />
            </div>
            {sidebarOpen && (
              <ChatPanel
                apiBase={API_BASE}
                onHighlight={setHighlightedNodes}
                onClose={() => setSidebarOpen(false)}
              />
            )}
          </>
        )}
      </div>

      {selectedNode && (
        <NodeModal data={selectedNode} onClose={() => setSelectedNode(null)} />
      )}
    </div>
  )
}
