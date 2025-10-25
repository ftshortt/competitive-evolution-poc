import React, { useState, useEffect } from 'react';
import { startExperiment, stopExperiment, getStatus } from '../services/api';

const ControlPane = () => {
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    // Poll status every 5 seconds
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

    pollStatus(); // Initial fetch
    const interval = setInterval(pollStatus, 5000); // Poll every 5 seconds

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

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', padding: '10px' }}>
      <h3>Experiment Control</h3>
      
      <div style={{ marginBottom: '20px' }}>
        <button
          onClick={handleStart}
          disabled={loading || status?.running}
          style={{
            padding: '10px 20px',
            marginRight: '10px',
            backgroundColor: '#4caf50',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: loading || status?.running ? 'not-allowed' : 'pointer',
            fontSize: '14px'
          }}
        >
          Start Experiment
        </button>
        <button
          onClick={handleStop}
          disabled={loading || !status?.running}
          style={{
            padding: '10px 20px',
            backgroundColor: '#f44336',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: loading || !status?.running ? 'not-allowed' : 'pointer',
            fontSize: '14px'
          }}
        >
          Stop Experiment
        </button>
      </div>

      {error && (
        <div style={{
          padding: '10px',
          marginBottom: '10px',
          backgroundColor: '#ffebee',
          color: '#c62828',
          borderRadius: '4px',
          border: '1px solid #ef5350'
        }}>
          {error}
        </div>
      )}

      <div style={{
        flex: 1,
        padding: '15px',
        border: '1px solid #ccc',
        borderRadius: '4px',
        backgroundColor: '#f9f9f9'
      }}>
        <h4 style={{ marginTop: 0 }}>Status</h4>
        {status ? (
          <div>
            <div style={{ marginBottom: '10px' }}>
              <strong>Running:</strong> {status.running ? 'Yes' : 'No'}
            </div>
            <div style={{ marginBottom: '10px' }}>
              <strong>Generation:</strong> {status.generation ?? 'N/A'}
            </div>
            <div style={{ marginBottom: '10px' }}>
              <strong>Best Fitness:</strong> {status.fitness ?? 'N/A'}
            </div>
            <div style={{ marginBottom: '10px' }}>
              <strong>Pool Count:</strong> {status.poolCount ?? 'N/A'}
            </div>
          </div>
        ) : (
          <div style={{ fontStyle: 'italic', color: '#666' }}>Loading status...</div>
        )}
      </div>
    </div>
  );
};

export default ControlPane;
