/* eslint-disable react-hooks/exhaustive-deps */
import { useEffect, useRef, useCallback } from 'react'
import * as d3 from 'd3'

const NODE_COLORS = {
  SalesOrder:       { fill: '#3b82f6', stroke: '#1d4ed8' },
  SalesOrderItem:   { fill: '#06b6d4', stroke: '#0284c7' },
  BillingDocument:  { fill: '#8b5cf6', stroke: '#6d28d9' },
  Delivery:         { fill: '#10b981', stroke: '#059669' },
  Payment:          { fill: '#f59e0b', stroke: '#d97706' },
  JournalEntry:     { fill: '#ef4444', stroke: '#dc2626' },
  Customer:         { fill: '#ec4899', stroke: '#db2777' },
  Product:          { fill: '#84cc16', stroke: '#65a30d' },
}

const NODE_RADIUS = {
  SalesOrder: 10, SalesOrderItem: 6, BillingDocument: 10,
  Delivery: 9, Payment: 8, JournalEntry: 7, Customer: 12, Product: 6,
}

export default function GraphVisualization({ data, onNodeClick, highlightedNodes = [] }) {
  const svgRef = useRef(null)
  const simRef = useRef(null)
  const highlightSet = new Set(highlightedNodes)

  const draw = useCallback(() => {
    if (!svgRef.current || !data.nodes.length) return
    const container = svgRef.current.parentElement
    const W = container.clientWidth
    const H = container.clientHeight

    d3.select(svgRef.current).selectAll('*').remove()

    const svg = d3.select(svgRef.current)
      .attr('width', W).attr('height', H)

    // Dark background
    svg.append('rect').attr('width', W).attr('height', H).attr('fill', '#0f172a')

    // Grid
    const grid = svg.append('g')
    for (let x = 0; x < W; x += 50)
      grid.append('line').attr('x1', x).attr('y1', 0).attr('x2', x).attr('y2', H)
        .attr('stroke', 'rgba(255,255,255,0.03)').attr('stroke-width', 1)
    for (let y = 0; y < H; y += 50)
      grid.append('line').attr('x1', 0).attr('y1', y).attr('x2', W).attr('y2', y)
        .attr('stroke', 'rgba(255,255,255,0.03)').attr('stroke-width', 1)

    const g = svg.append('g')

    const zoom = d3.zoom().scaleExtent([0.05, 4])
      .on('zoom', e => g.attr('transform', e.transform))
    svg.call(zoom)
    svg.call(zoom.transform, d3.zoomIdentity.translate(W / 2, H / 2).scale(0.4))

    // Limit nodes for performance
    const MAX = 350
    const priority = ['Customer','SalesOrder','BillingDocument','Delivery','Payment','JournalEntry','Product','SalesOrderItem']
    let nodes = []
    for (const t of priority) nodes.push(...data.nodes.filter(n => n.type === t))
    nodes = nodes.slice(0, MAX)
    const nodeIds = new Set(nodes.map(n => n.id))
    const links = data.edges.filter(e => nodeIds.has(e.source) && nodeIds.has(e.target))

    // Draw links
    const link = g.append('g').selectAll('line').data(links).join('line')
      .attr('stroke', 'rgba(148,163,184,0.15)').attr('stroke-width', 0.8)

    // Draw nodes
    const node = g.append('g').selectAll('g').data(nodes, d => d.id).join('g')
      .style('cursor', 'pointer')
      .call(d3.drag()
        .on('start', (e, d) => { if (!e.active) simRef.current.alphaTarget(0.3).restart(); d.fx = d.x; d.fy = d.y })
        .on('drag', (e, d) => { d.fx = e.x; d.fy = e.y })
        .on('end', (e, d) => { if (!e.active) simRef.current.alphaTarget(0); d.fx = null; d.fy = null })
      )
      .on('click', (e, d) => { e.stopPropagation(); onNodeClick(d.id) })

    node.append('circle')
      .attr('r', d => NODE_RADIUS[d.type] || 7)
      .attr('fill', d => highlightSet.has(d.id) ? '#fbbf24' : (NODE_COLORS[d.type]?.fill || '#64748b'))
      .attr('stroke', d => highlightSet.has(d.id) ? '#f59e0b' : (NODE_COLORS[d.type]?.stroke || '#475569'))
      .attr('stroke-width', d => highlightSet.has(d.id) ? 3 : 1.5)

    node.append('text')
      .text(d => (NODE_RADIUS[d.type] || 7) >= 9 ? d.label.substring(0, 12) : '')
      .attr('dy', d => (NODE_RADIUS[d.type] || 7) + 9)
      .attr('text-anchor', 'middle')
      .attr('fill', 'rgba(255,255,255,0.55)')
      .attr('font-size', '7px')
      .attr('font-family', 'Inter, sans-serif')
      .style('pointer-events', 'none')

    // Tooltip
    const tip = d3.select('body').select('.graph-tooltip')
    node.on('mouseover', (e, d) => {
      const c = NODE_COLORS[d.type]?.fill || '#64748b'
      tip.style('display','block').style('border-color', c)
        .html(`<div class="tt-type" style="color:${c}">${d.type}</div><div class="tt-label">${d.label}</div><div class="tt-hint">Click to inspect</div>`)
    })
    .on('mousemove', e => tip.style('left', (e.pageX+12)+'px').style('top', (e.pageY-10)+'px'))
    .on('mouseout', () => tip.style('display','none'))

    // Force simulation - tighter layout
    const sim = d3.forceSimulation(nodes)
      .force('link', d3.forceLink(links).id(d => d.id).distance(40).strength(0.5))
      .force('charge', d3.forceManyBody().strength(-80))
      .force('center', d3.forceCenter(0, 0).strength(0.1))
      .force('collision', d3.forceCollide().radius(d => (NODE_RADIUS[d.type] || 7) + 3))
      .force('x', d3.forceX(0).strength(0.05))
      .force('y', d3.forceY(0).strength(0.05))
      .on('tick', () => {
        link.attr('x1', d => d.source.x).attr('y1', d => d.source.y)
            .attr('x2', d => d.target.x).attr('y2', d => d.target.y)
        node.attr('transform', d => `translate(${d.x},${d.y})`)
      })
    simRef.current = sim

    d3.select('#zoom-in').on('click', () => svg.transition().call(zoom.scaleBy, 1.4))
    d3.select('#zoom-out').on('click', () => svg.transition().call(zoom.scaleBy, 0.7))
    d3.select('#zoom-reset').on('click', () =>
      svg.transition().call(zoom.transform, d3.zoomIdentity.translate(W/2, H/2).scale(0.4)))

  }, [data, highlightedNodes, onNodeClick])

  useEffect(() => {
    draw()
    const obs = new ResizeObserver(draw)
    if (svgRef.current?.parentElement) obs.observe(svgRef.current.parentElement)
    return () => obs.disconnect()
  }, [draw])

  return (
    <div className="graph-viz">
      <svg ref={svgRef} className="graph-svg" />
      <div className="graph-controls">
        <button id="zoom-in">+</button>
        <button id="zoom-reset">⊙</button>
        <button id="zoom-out">−</button>
      </div>
      <div className="graph-legend">
        {Object.entries(NODE_COLORS).map(([type, c]) => (
          <div key={type} className="legend-item">
            <span className="legend-dot" style={{ background: c.fill }} />
            <span>{type}</span>
          </div>
        ))}
      </div>
    </div>
  )
}