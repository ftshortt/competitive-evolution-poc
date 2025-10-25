import React from 'react';

const MetricsPane = () => {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', padding: '10px' }}>
      <h3>Metrics Dashboard</h3>
      <div style={{ flex: 1, border: '1px solid #ccc', borderRadius: '4px', overflow: 'hidden' }}>
        <iframe
          src="http://localhost:3000"
          title="Grafana Metrics Dashboard"
          style={{
            width: '100%',
            height: '100%',
            border: 'none'
          }}
          allowFullScreen
        />
      </div>
    </div>
  );
};

export default MetricsPane;
