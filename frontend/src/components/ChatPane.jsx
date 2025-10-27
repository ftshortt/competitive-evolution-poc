import React, { useEffect, useMemo, useRef, useState } from 'react';
import { spawnAgent, retireAgent, getAgentStatus, getAgentFamily, postAgentTopic, sendChatMessage } from '../services/api';

const SYSTEM_HELP = `Commands: 
- spawn child {"traits": {"domain": "x", "style": "y"}}
- retire <agent_id>
- show family <agent_id>`;

const CATEGORY_COLORS = {
  exploration: '#3b82f6',
  exploitation: '#22c55e',
  innovation: '#a855f7',
  stabilization: '#f59e0b',
  adaptation: '#ef4444',
};

export default function ChatPane() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [agents, setAgents] = useState([]);
  const [activeAgentId, setActiveAgentId] = useState(null);
  const [mode, setMode] = useState('dev'); // dev | user
  const [lastDriftHint, setLastDriftHint] = useState('');
  const pollRef = useRef(null);

  const parentAgentId = useMemo(() => agents.find(a => a.generation === 0)?.id || null, [agents]);

  useEffect(() => {
    refreshAgents();
    pollRef.current = setInterval(() => refreshAgents(false), 5000);
    return () => clearInterval(pollRef.current);
  }, []);

  useEffect(() => {
    if (!activeAgentId && parentAgentId) setActiveAgentId(parentAgentId);
  }, [parentAgentId, activeAgentId]);

  async function refreshAgents(verbose = true) {
    try {
      const resp = await getAgentStatus();
      setAgents(resp.live_agents || []);
      if (verbose && resp.metrics?.topic_categories) {
        // surface a small badge somewhere if needed
      }
    } catch (e) {
      console.error('Failed to refresh agents', e);
    }
  }

  function append(role, content, extra = {}) {
    setMessages(prev => [...prev, { role, content, ts: Date.now(), ...extra }]);
  }

  async function handleSendMessage() {
    if (!input.trim()) return;
    const text = input.trim();
    setInput('');
    append('user', text);
    setLoading(true);
    const lower = text.toLowerCase();
    try {
      if (lower.startsWith('spawn child')) {
        const jsonStart = text.indexOf('{');
        let traits = {};
        if (jsonStart >= 0) {
          const json = text.slice(jsonStart);
          try { traits = JSON.parse(json).traits || JSON.parse(json); } catch {}
        }
        const parentId = activeAgentId || parentAgentId;
        const resp = await spawnAgent({ parent_id: parentId, traits });
        append('assistant', `Spawned child ${resp.agent?.id || 'unknown'}`);
        await refreshAgents();
        return;
      }
      if (lower.startsWith('retire ')) {
        const parts = text.split(/\s+/);
        const target = parts[1];
        if (!target) { append('assistant', 'Usage: retire <agent_id>'); return; }
        await retireAgent({ agent_id: target });
        append('assistant', `Retired agent ${target}`);
        await refreshAgents();
        return;
      }
      if (lower.startsWith('show family')) {
        const parts = text.split(/\s+/);
        const target = parts[2] || activeAgentId || parentAgentId;
        if (!target) { append('assistant', 'No agent selected'); return; }
        const resp = await getAgentFamily(target);
        append('assistant', `Family nodes: ${resp.tree?.nodes?.length || 0}, edges: ${resp.tree?.edges?.length || 0}`);
        return;
      }
      // Default chat to parent/active agent context
      const agentId = activeAgentId || parentAgentId;
      const response = await sendChatMessage(text, agentId);
      append('assistant', response.message || response.response || '');

      // Light topic drift logging (extract simple hashtag/topic words)
      const tags = (text.match(/#[\w-]+/g) || []).map(t => t.slice(1));
      for (const t of tags.slice(0, 3)) {
        try { await postAgentTopic({ agent_id: agentId, topic: t }); } catch {}
      }

      // Seamless categorization call to backend
      try {
        const r = await fetch('/categorize', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ text }) });
        const cj = await r.json();
        if (cj?.category) {
          append('system', `Category: ${cj.category} (${Math.round((cj.confidence||0)*100)}%)`, { category: cj.category });
        }
      } catch {}

      // Pull status drift hints
      try {
        const sr = await fetch('/status');
        const sj = await sr.json();
        const hint = sj?.status_data?.recent_drift?.slice(-1)?.[0]?.drift?.hint;
        if (hint) { setLastDriftHint(hint); }
      } catch {}

    } catch (err) {
      console.error(err);
      append('assistant', 'Error handling message. ' + (err?.message || ''));
    } finally {
      setLoading(false);
    }
  }

  function handleKeyPress(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  }

  const categorizedBubbles = messages.filter(m => m.category);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', padding: 12 }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 8 }}>
        <strong>Chat</strong>
        <label style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: 6 }}>
          <span>Mode:</span>
          <select value={mode} onChange={e => setMode(e.target.value)}>
            <option value="dev">Dev</option>
            <option value="user">User</option>
          </select>
        </label>
      </div>

      {/* Category bubbles row */}
      <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginBottom: 8 }}>
        {['exploration','exploitation','innovation','stabilization','adaptation'].map(cat => (
          <span key={cat} title={cat}
            style={{
              background: CATEGORY_COLORS[cat], color: 'white', padding: '4px 8px', borderRadius: 999,
              opacity: categorizedBubbles.some(b => b.category === cat) ? 1 : 0.35,
            }}>
            {cat}
          </span>
        ))}
        {lastDriftHint && (
          <span style={{ marginLeft: 'auto', fontStyle: 'italic', color: '#64748b' }}>Hint: {lastDriftHint}</span>
        )}
      </div>

      <div style={{ flex: 1, border: '1px solid #e5e7eb', borderRadius: 6, padding: 10, overflowY: 'auto', marginBottom: 8, background: '#fff' }}>
        {messages.map((msg, idx) => (
          <div key={idx} style={{
            marginBottom: 10,
            border: '1px solid #e5e7eb',
            borderLeft: msg.category ? `6px solid ${CATEGORY_COLORS[msg.category]}` : '6px solid transparent',
            borderRadius: 6,
            padding: 8,
            background: msg.role === 'user' ? '#f8fafc' : '#fff',
          }}>
            {msg.role === 'user' ? 'You' : (msg.role === 'system' ? 'System' : 'Assistant')}:
            <div style={{ marginTop: 4, whiteSpace: 'pre-wrap' }}>{msg.content}</div>
          </div>
        ))}
        {loading && <div style={{ color: '#64748b', fontStyle: 'italic' }}>Assistant is typing...</div>}
        <div style={{ color: '#64748b', fontSize: 12, marginTop: 12, whiteSpace: 'pre-wrap' }}>{SYSTEM_HELP}</div>
      </div>

      <div style={{ display: 'flex', gap: 8 }}>
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder="Type your message or a command..."
          disabled={loading}
          style={{ flex: 1, padding: '10px', fontSize: '14px', border: '1px solid #ccc', borderRadius: '4px' }}
        />
        <button disabled={loading} onClick={handleSendMessage}>Send</button>
      </div>
    </div>
  );
}
