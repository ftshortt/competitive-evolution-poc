import React, { useEffect, useMemo, useState } from 'react';
import { getAgentStatus, getAgentFamily } from '../services/api';

// Simple tree layout without external libs; color-code by generation/fitness
export default function GraphPane() {
  const [agents, setAgents] = useState([]);
  const [selectedId, setSelectedId] = useState(null);
  const [tree, setTree] = useState(null);

  useEffect(() => {
    refresh();
    const id = setInterval(refresh, 7000);
    return () => clearInterval(id);
  }, []);

  useEffect(() => {
    const parent = agents.find(a => a.generation === 0);
    if (!selectedId && parent) setSelectedId(parent.id);
  }, [agents, selectedId]);

  useEffect(() => {
    if (!selectedId) { setTree(null); return; }
    getAgentFamily(selectedId).then(r => setTree(r.tree)).catch(() => setTree(null));
  }, [selectedId]);

  async function refresh() {
    try {
      const r = await getAgentStatus();
      setAgents(r.live_agents || []);
    } catch (e) {
      // ignore
    }
  }

  const nodes = tree?.nodes || [];
  const edges = tree?.edges || [];

  // Map generations to lanes (y position), spread siblings on x
  const gens = useMemo(() => {
    const g = {};
    for (const n of nodes) {
      g[n.generation] = g[n.generation] || [];
      g[n.generation].push(n);
    }
    return g;
  }, [nodes]);

  const laneHeight = 120;
  const width = 900;

  function colorFor(n) {
    // Hue by generation, lightness by fitness
    const hue = (n.generation * 60) % 360;
    const fitness = typeof n.fitness === 'number' ? n.fitness : 0;
    const light = 70 - Math.min(40, Math.round(fitness * 40));
    return `hsl(${hue} 70% ${light}%)`;
  }

  // Compute positions per generation
  const positioned = useMemo(() => {
    const pos = {};
    Object.entries(gens).forEach(([genStr, arr]) => {
      const gen = Number(genStr);
      const y = 40 + gen * laneHeight;
      const step = Math.max(120, Math.floor(width / Math.max(1, arr.length)));
      arr.forEach((n, i) => {
        pos[n.id] = { x: 60 + i * step, y, data: n };
      });
    });
    return pos;
  }, [gens]);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', padding: 10 }}>
      <h3>Family Graph</h3>
      <div style={{ display: 'flex', gap: 8, alignItems: 'center', marginBottom: 8 }}>
        <label>Focus agent:</label>
        <select value={selectedId || ''} onChange={e => setSelectedId(e.target.value)}>
          <option value="">None</option>
          {agents.map(a => (
            <option key={a.id} value={a.id}>{a.name || a.id.slice(0,8)} · gen {a.generation}</option>
          ))}
        </select>
        <span style={{ color: '#777' }}>{nodes.length} nodes · {edges.length} edges</span>
      </div>

      <div style={{ flex: 1, border: '1px solid #ccc', borderRadius: 4, position: 'relative', overflow: 'auto' }}>
        <svg width={width} height={Math.max(200, (Object.keys(gens).length + 1) * laneHeight)}>
          {/* Lanes */}
          {Object.keys(gens).map(g => (
            <g key={g}>
              <line x1={0} y1={40 + Number(g) * laneHeight} x2={width} y2={40 + Number(g) * laneHeight} stroke="#eee" />
              <text x={10} y={30 + Number(g) * laneHeight} fill="#777" fontSize={12}>gen {g}</text>
            </g>
          ))}
          {/* Edges */}
          {edges.map((e, i) => {
            const s = positioned[e.source];
            const t = positioned[e.target];
            if (!s || !t) return null;
            return <line key={i} x1={s.x} y1={s.y} x2={t.x} y2={t.y} stroke="#bbb" markerEnd="url(#arrow)" />
          })}
          <defs>
            <marker id="arrow" markerWidth="10" markerHeight="10" refX="10" refY="3" orient="auto" markerUnits="strokeWidth">
              <path d="M0,0 L0,6 L9,3 z" fill="#bbb" />
            </marker>
          </defs>
          {/* Nodes */}
          {Object.values(positioned).map(p => (
            <g key={p.data.id}>
              <circle cx={p.x} cy={p.y} r={18} fill={colorFor(p.data)} stroke="#555" />
              <title>
                {`name: ${p.data.name}\nfitness: ${p.data.fitness?.toFixed?.(2) || 0}\ntraits: ${JSON.stringify(p.data.traits)}\nbirth: ${new Date(p.data.birth_time*1000).toLocaleString()}${p.data.death_time ? `\ndied: ${new Date(p.data.death_time*1000).toLocaleString()}` : ''}`}
              </title>
              <text x={p.x} y={p.y + 34} fontSize={10} textAnchor="middle" fill="#333">{p.data.name || p.data.id.slice(0,6)}</text>
            </g>
          ))}
        </svg>
      </div>
    </div>
  );
}
