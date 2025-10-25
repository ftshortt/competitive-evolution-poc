import React from 'react';

const GraphPane = () => {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', padding: '10px' }}>
      <h3>Graph Visualization</h3>
      <div style={{ flex: 1, border: '1px solid #ccc', borderRadius: '4px', overflow: 'hidden' }}>
        <iframe
          src="http://localhost:7474"
          title="Neo4j Graph Browser"
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

export default GraphPane;
