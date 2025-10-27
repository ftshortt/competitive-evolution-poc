import React, { useState, useEffect } from 'react';
import { startExperiment, stopExperiment, getStatus } from '../services/api';

const ControlPane = () => {
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [mode, setMode] = useState('dev'); // dev | user

  useEffect(() => {
    const pollStatus = async () => {
      try {
        const statusData = await getStatus();
        setStatus(statusData);
        setError(null);
      } catch (err) {
        console.error('Error fetching status:', err);
        setError('Failed to fetch status');
      }
    };
    pollStatus();
    const interval = setInterval(pollStatus, 5000);
    return () => clearInterval(interval);
  }, []);

  const handleStart = async () => {
    setLoading(true);
    try {
      await startExperiment();
      setError(null);
    } catch (err) {
      console.error('Error starting experiment:', err);
      setError('Failed to start experiment');
    } finally {
      setLoading(false);
    }
  };

  const handleStop = async () => {
    setLoading(true);
    try {
      await stopExperiment();
      setError(null);
    } catch (err) {
      console.error('Error stopping experiment:', err);
      setError('Failed to stop experiment');
    } finally {
      setLoading(false);
    }
  };

  // AS-FDVM lifecycle ops (dummy hits backend)
  async function spawn(category) {
    try {
      await fetch('/spawn', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ category }) });
    } catch {}
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', padding: '10px' }}>
      <h3>Experiment Control</h3>

      <div style={{ display: 'flex', gap: 8, alignItems: 'center', marginBottom: 8 }}>
        <label style={{ marginLeft: 'auto', display: 'flex', gap: 6, alignItems: 'center' }}>
          Mode:
          <select value={mode} onChange={e => setMode(e.target.value)}>
            <option value="dev">Dev</option>
            <option value="user">User</option>
          </select>
        </label>
      </div>

      <div style={{ marginBottom: '20px' }}>
        <button onClick={handleStart} disabled={loading || status?.running} style={{
          padding: '10px 20px', marginRight: '10px', backgroundColor: '#4caf50', color: 'white', border: 'none', borderRadius: '4px', cursor: (loading || status?.running) ? 'not-allowed' : 'pointer', fontSize: '14px'
        }}>Start Experiment</button>
        <button onClick={handleStop} disabled={loading || !status?.running} style={{
          padding: '10px 20px', backgroundColor: '#f44336', color: 'white', border: 'none', borderRadius: '4px', cursor: (loading || !status?.running) ? 'not-allowed' : 'pointer', fontSize: '14px'
        }}>Stop Experiment</button>
      </div>

      {error && (
        <div style={{ padding: '10px', marginBottom: '10px', backgroundColor: '#ffebee', color: '#c62828', borderRadius: '4px', border: '1px solid #ef5350' }}>
          {error}
        </div>
      )}

      <div style={{ flex: 1, padding: '15px', border: '1px solid #ccc', borderRadius: '4px', backgroundColor: '#f9f9f9' }}>
        <h4 style={{ marginTop: 0 }}>Status</h4>
        {status ? (
          <div>
            <div style={{ marginBottom: 8 }}>Running: {status.running ? 'Yes' : 'No'}</div>
            <div style={{ marginBottom: 8 }}>Generation: {status.generation ?? 'N/A'}</div>
            <div style={{ marginBottom: 8 }}>Best Fitness: {status.fitness ?? 'N/A'}</div>
            <div style={{ marginBottom: 8 }}>Pool Count: {status.poolCount ?? 'N/A'}</div>
          </div>
        ) : (
          <div style={{ color: '#64748b', fontStyle: 'italic' }}>Loading status...</div>
        )}
      </div>

      <div style={{ marginTop: 12, padding: 12, border: '1px dashed #cbd5e1', borderRadius: 6 }}>
        <h4 style={{ marginTop: 0 }}>AS-FDVM Lifecycle</h4>
        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
          {['exploration','exploitation','innovation','stabilization','adaptation'].map(cat => (
            <button key={cat} onClick={() => spawn(cat)} style={{ padding: '6px 10px', borderRadius: 999, border: '1px solid #e5e7eb', background: 'white' }}>Spawn {cat}</button>
          ))}
        </div>
      </div>
    </div>
  );
};

export default ControlPane;
