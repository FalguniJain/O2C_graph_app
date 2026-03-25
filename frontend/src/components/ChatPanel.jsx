import { useState, useEffect, useRef } from 'react'

const SAMPLE_QUERIES = [
  "Which products have the most billing documents?",
  "Trace billing document 91150187",
  "Find delivered but unbilled orders",
  "Total revenue by currency",
  "List cancelled billing documents",
  "Which customers have most orders?"
]

function Message({ msg }) {
  const isUser = msg.role === 'user'
  return (
    <div className={`msg ${isUser ? 'msg-user' : 'msg-ai'}`}>
      {!isUser && (
        <div className="msg-avatar">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none">
            <circle cx="12" cy="12" r="3" fill="white"/>
            <circle cx="5" cy="5" r="2" fill="white" opacity=".6"/>
            <circle cx="19" cy="5" r="2" fill="white" opacity=".6"/>
            <circle cx="5" cy="19" r="2" fill="white" opacity=".6"/>
            <circle cx="19" cy="19" r="2" fill="white" opacity=".6"/>
            <line x1="12" y1="9" x2="7" y2="7" stroke="white" strokeWidth="1.5" opacity=".4"/>
            <line x1="12" y1="9" x2="17" y2="7" stroke="white" strokeWidth="1.5" opacity=".4"/>
            <line x1="12" y1="15" x2="7" y2="17" stroke="white" strokeWidth="1.5" opacity=".4"/>
            <line x1="12" y1="15" x2="17" y2="17" stroke="white" strokeWidth="1.5" opacity=".4"/>
          </svg>
        </div>
      )}
      <div className="msg-content">
        {isUser ? (
          <p>{msg.content}</p>
        ) : (
          <>
            <p className="msg-text">{msg.content}</p>
            {msg.sql && (
              <details className="sql-block">
                <summary>View SQL Query</summary>
                <pre><code>{msg.sql}</code></pre>
              </details>
            )}
            {msg.data && Array.isArray(msg.data) && msg.data.length > 0 && (
              <div className="data-table-wrap">
                <table className="data-table">
                  <thead>
                    <tr>{Object.keys(msg.data[0]).slice(0, 5).map(k => <th key={k}>{k}</th>)}</tr>
                  </thead>
                  <tbody>
                    {msg.data.slice(0, 8).map((row, i) => (
                      <tr key={i}>
                        {Object.values(row).slice(0, 5).map((v, j) => (
                          <td key={j}>{String(v ?? '—').substring(0, 30)}</td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
                {msg.data.length > 8 && (
                  <p className="data-more">+ {msg.data.length - 8} more rows</p>
                )}
              </div>
            )}
          </>
        )}
      </div>
    </div>
  )
}

export default function ChatPanel({ apiBase, onHighlight, onClose }) {
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content: "Hi! I'm your O2C Graph Agent. I can help you analyze sales orders, deliveries, billing documents, payments, and more. Ask me anything about the Order-to-Cash data!"
    }
  ])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const bottomRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const send = async (text) => {
    const userText = (text || input).trim()
    if (!userText || loading) return
    setInput('')

    const userMsg = { role: 'user', content: userText }
    setMessages(prev => [...prev, userMsg])
    setLoading(true)

    try {
      const history = messages.slice(-6).map(m => ({ role: m.role === 'assistant' ? 'assistant' : 'user', content: m.content }))
      const res = await fetch(`${apiBase}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: userText, history })
      })
      const data = await res.json()
      const aiMsg = {
        role: 'assistant',
        content: data.answer,
        sql: data.sql,
        data: data.data
      }
      setMessages(prev => [...prev, aiMsg])
      if (data.highlighted_nodes?.length) {
        onHighlight(data.highlighted_nodes)
      }
    } catch  {
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: 'Connection error. Please ensure the backend is running.'
      }])
    }
    setLoading(false)
  }

  return (
    <div className="chat-panel">
      <div className="chat-header">
        <div className="chat-header-left">
          <div className="chat-avatar">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
              <circle cx="12" cy="12" r="3" fill="white"/>
              <circle cx="5" cy="5" r="2" fill="white" opacity=".6"/>
              <circle cx="19" cy="5" r="2" fill="white" opacity=".6"/>
              <circle cx="5" cy="19" r="2" fill="white" opacity=".6"/>
              <circle cx="19" cy="19" r="2" fill="white" opacity=".6"/>
              <line x1="12" y1="9" x2="7" y2="7" stroke="white" strokeWidth="1.5" opacity=".4"/>
              <line x1="12" y1="9" x2="17" y2="7" stroke="white" strokeWidth="1.5" opacity=".4"/>
              <line x1="12" y1="15" x2="7" y2="17" stroke="white" strokeWidth="1.5" opacity=".4"/>
              <line x1="12" y1="15" x2="17" y2="17" stroke="white" strokeWidth="1.5" opacity=".4"/>
            </svg>
          </div>
          <div>
            <div className="chat-title">Graph Agent</div>
            <div className="chat-subtitle">Order to Cash</div>
          </div>
        </div>
        <button className="chat-close" onClick={onClose}>×</button>
      </div>

      <div className="chat-messages">
        {messages.map((m, i) => <Message key={i} msg={m} />)}
        {loading && (
          <div className="msg msg-ai">
            <div className="msg-avatar">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none">
                <circle cx="12" cy="12" r="3" fill="white"/>
                <circle cx="5" cy="5" r="2" fill="white" opacity=".6"/>
                <circle cx="19" cy="5" r="2" fill="white" opacity=".6"/>
                <circle cx="5" cy="19" r="2" fill="white" opacity=".6"/>
                <circle cx="19" cy="19" r="2" fill="white" opacity=".6"/>
              </svg>
            </div>
            <div className="msg-content">
              <div className="typing-dots"><span/><span/><span/></div>
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      <div className="chat-suggestions">
        {SAMPLE_QUERIES.slice(0, 3).map((q, i) => (
          <button key={i} className="suggestion-chip" onClick={() => send(q)}>
            {q}
          </button>
        ))}
      </div>

      <div className="chat-input-area">
        <div className="chat-status">
          <span className="status-dot-green"/>
          Agent is ready
        </div>
        <div className="input-row">
          <textarea
            className="chat-input"
            placeholder="Ask about orders, billing, payments…"
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={e => {
              if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send() }
            }}
            rows={2}
          />
          <button className="send-btn" onClick={() => send()} disabled={loading || !input.trim()}>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
              <path d="M22 2L11 13" stroke="white" strokeWidth="2" strokeLinecap="round"/>
              <path d="M22 2L15 22L11 13L2 9L22 2Z" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
          </button>
        </div>
      </div>
    </div>
  )
}
