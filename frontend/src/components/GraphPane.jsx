import React, { useEffect, useMemo, useState } from 'react';

// Graph by category and generation from AS-FDVM engine plus family focus
export default function GraphPane() {
  const [graph, setGraph] = useState(null);
  const [groupMode, setGroupMode] = useState('category'); // category | generation

  useEffect(() => {
    refresh();
    const id = setInterval(refresh, 8000);
    return () => clearInterval(id);
  }, []);

  async function refresh() {
    try {
      const r = await fetch('/graph');
      const j = await r.json();
      setGraph(j.graph || j.data || j);
    } catch (e) {
      // ignore
    }
  }

  const nodes = graph?.graph?.nodes || graph?.nodes || [];
  const edges = graph?.graph?.edges || graph?.edges || [];
  const byCategory = graph?.graph?.by_category || graph?.by_category || {};
  const byGeneration = graph?.graph?.by_generation || graph?.by_generation || {};

  // Layout helpers
  const width = 1000;
  const laneHeight = 120;

  const lanes = useMemo(() => {
    if (groupMode === 'category') return byCategory;
    return byGeneration;
  }, [groupMode, byCategory, byGeneration]);

  const laneKeys = Object.keys(lanes);
  function colorFor(n) {
    // simple color by category
    const colors = {
      exploration: '#3b82f6',
      exploitation: '#22c55e',
      innovation: '#a855f7',
      stabilization: '#f59e0b',
      adaptation: '#ef4444',
    };
    return colors[n.category] || '#64748b';
  }

  // Compute positions by lane
  const positioned = useMemo(() => {
    const pos = {};
    laneKeys.forEach((laneKey, laneIdx) => {
      const arr = lanes[laneKey] || [];
      const y = 40 + laneIdx * laneHeight;
      const step = Math.max(120, Math.floor(width / Math.max(1, arr.length)));
      arr.forEach((n, i) => {
        pos[n.id] = { x: 60 + i * step, y, data: n };
      });
    });
    return pos;
  }, [lanes, laneKeys]);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', padding: 10 }}>
      <div style={{ display: 'flex', gap: 8, alignItems: 'center', marginBottom: 8 }}>
        <strong>Evolution Graph</strong>
        <label style={{ marginLeft: 'auto', display: 'flex', gap: 6, alignItems: 'center' }}>
          Group by:
          <select value={groupMode} onChange={e => setGroupMode(e.target.value)}>
            <option value="category">Category</option>
            <option value="generation">Generation</option>
          </select>
        </label>
        <span style={{ color: '#64748b' }}>{nodes.length} nodes · {edges.length} edges</span>
      </div>

      <div style={{ flex: 1, border: '1px solid #e5e7eb', borderRadius: 6, position: 'relative', overflow: 'auto' }}>
        <svg width={width} height={Math.max(300, 80 + laneKeys.length * laneHeight)}>
          {laneKeys.map((k, i) => (
            <g key={k}>
              <line x1={0} x2={width} y1={40 + i*laneHeight} y2={40 + i*laneHeight} stroke="#eee" />
              <text x={10} y={30 + i*laneHeight} fill="#777" fontSize={12}>{groupMode==='category' ? k : `gen ${k}`}</text>
            </g>
          ))}

          {/* Edges */}
          {edges.map((e, i) => {
            const s = positioned[e.source];
            const t = positioned[e.target];
            if (!s || !t) return null;
            return <line key={i} x1={s.x} y1={s.y} x2={t.x} y2={t.y} stroke="#cbd5e1" />
          })}

          {/* Nodes */}
          {Object.values(positioned).map(p => (
            <g key={p.data.id}>
              <circle cx={p.x} cy={p.y} r={16} fill={colorFor(p.data)} stroke="#334155" />
              <title>{`id: ${p.data.id}\ncat: ${p.data.category}\nfit: ${p.data.fitness?.toFixed?.(2) || 0}`}</title>
            </g>
          ))}
        </svg>
      </div>
    </div>
  );
}
