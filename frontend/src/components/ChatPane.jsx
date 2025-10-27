import React, { useEffect, useMemo, useRef, useState } from 'react';
import { spawnAgent, retireAgent, getAgentStatus, getAgentFamily, postAgentTopic, sendChatMessage } from '../services/api';

const SYSTEM_HELP = `Commands: \n- spawn child {"traits": {"domain": "x", "style": "y"}}\n- retire <agent_id>\n- show family <agent_id>`;

export default function ChatPane() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [agents, setAgents] = useState([]);
  const [activeAgentId, setActiveAgentId] = useState(null);
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
        // could surface a small badge somewhere
      }
    } catch (e) {
      console.error('Failed to refresh agents', e);
    }
  }

  function append(role, content) {
    setMessages(prev => [...prev, { role, content, ts: Date.now() }]);
  }

  async function handleSendMessage() {
    if (!input.trim()) return;
    const text = input.trim();
    setInput('');
    append('user', text);
    setLoading(true);

    // Parse optional commands
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

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', padding: '10px' }}>
      <h3>Chat</h3>
      <div style={{ display: 'flex', gap: 8, alignItems: 'center', marginBottom: 8 }}>
        <label>Active agent:</label>
        <select value={activeAgentId || ''} onChange={e => setActiveAgentId(e.target.value)}>
          <option value="">Parent default</option>
          {agents.map(a => (
            <option key={a.id} value={a.id}>{a.name || a.id.slice(0,8)} · gen {a.generation} · fit {a.fitness?.toFixed?.(2) || '0.00'}</option>
          ))}
        </select>
        <span style={{ color: '#777' }}>{agents.length} live</span>
      </div>

      <div style={{ flex: 1, overflowY: 'auto', border: '1px solid #ccc', padding: '10px', marginBottom: '10px', backgroundColor: '#f9f9f9' }}>
        {messages.map((msg, idx) => (
          <div key={idx} style={{ marginBottom: '10px', padding: '8px', backgroundColor: msg.role === 'user' ? '#e3f2fd' : '#f5f5f5', borderRadius: '4px', borderLeft: `4px solid ${msg.role === 'user' ? '#2196f3' : '#4caf50'}` }}>
            <strong>{msg.role === 'user' ? 'You' : 'Assistant'}:</strong>
            <div style={{ marginTop: '5px', whiteSpace: 'pre-wrap' }}>{msg.content}</div>
          </div>
        ))}
        {loading && <div style={{ fontStyle: 'italic', color: '#666' }}>Assistant is typing...</div>}
        <div style={{ color: '#888', fontSize: 12, marginTop: 8, whiteSpace: 'pre-wrap' }}>{SYSTEM_HELP}</div>
      </div>

      <div style={{ display: 'flex', gap: '10px' }}>
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder="Type your message or a command..."
          disabled={loading}
          style={{ flex: 1, padding: '10px', fontSize: '14px', border: '1px solid #ccc', borderRadius: '4px' }}
        />
        <button onClick={handleSendMessage} disabled={loading}>Send</button>
      </div>
    </div>
  );
}
