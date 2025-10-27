import React, { useEffect, useState } from 'react';
import { getAgentStatus } from '../services/api';

export default function MetricsPane() {
  const [metrics, setMetrics] = useState(null);

  async function refresh() {
    try {
      const r = await getAgentStatus();
      setMetrics(r.metrics || null);
    } catch (e) {
      // ignore
    }
  }

  useEffect(() => {
    refresh();
    const id = setInterval(refresh, 6000);
    return () => clearInterval(id);
  }, []);

  const k = metrics || {};

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', padding: '10px' }}>
      <h3>Metrics</h3>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 12, marginBottom: 12 }}>
        <Tile label="Live agents" value={k.live_agents ?? 0} />
        <Tile label="Average fitness" value={Number(k.average_fitness || 0).toFixed(2)} />
        <Tile label="Generational depth" value={k.max_generation ?? 0} />
      </div>
      <div style={{ flex: 1, border: '1px solid #ccc', borderRadius: 4, padding: 12 }}>
        <h4>Generation distribution</h4>
        <ul style={{ marginTop: 6 }}>
          {Object.entries(k.generation_distribution || {}).map(([gen, count]) => (
            <li key={gen}>gen {gen}: {count}</li>
          ))}
        </ul>
      </div>
    </div>
  );
}

function Tile({ label, value }) {
  return (
    <div style={{ border: '1px solid #ddd', borderRadius: 6, padding: 12, background: '#fafafa' }}>
      <div style={{ color: '#555', fontSize: 12 }}>{label}</div>
      <div style={{ fontSize: 22, fontWeight: 600 }}>{value}</div>
    </div>
  );
}
