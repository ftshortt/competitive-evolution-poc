import React, { useState, useEffect } from 'react';
import './App.css';
import { FEATURES } from './config';
import ChatPane from './components/ChatPane';
import GraphPane from './components/GraphPane';
import MetricsPane from './components/MetricsPane';
import ControlPane from './components/ControlPane';
import CodeEditorPane from './components-phase2/CodeEditorPane';
import TaggingPane from './components-phase2/TaggingPane';
import LogsPane from './components-phase2/LogsPane';

function App() {
  const [simulationStatus, setSimulationStatus] = useState('stopped');
  const [graphData, setGraphData] = useState(null);
  const [metrics, setMetrics] = useState(null);
  const [messages, setMessages] = useState([]);
  const [selectedCode, setSelectedCode] = useState(null);
  const [tags, setTags] = useState([]);
  const [logs, setLogs] = useState([]);

  const isPhase2Enabled = FEATURES.PHASE_2_ENABLED;

  useEffect(() => {
    // Fetch initial data
    fetchGraphData();
    fetchMetrics();
    if (isPhase2Enabled) {
      fetchLogs();
    }
  }, [isPhase2Enabled]);

  const fetchGraphData = async () => {
    // Fetch graph data from backend
  };

  const fetchMetrics = async () => {
    // Fetch metrics from backend
  };

  const fetchLogs = async () => {
    // Fetch logs from backend
  };

  const handleStartSimulation = () => {
    setSimulationStatus('running');
  };

  const handleStopSimulation = () => {
    setSimulationStatus('stopped');
  };

  const handleCodeSelect = (code) => {
    setSelectedCode(code);
  };

  const handleTagUpdate = (newTags) => {
    setTags(newTags);
  };

  return (
    <div className={`app-container ${isPhase2Enabled ? 'phase2-layout' : 'phase1-layout'}`}>
      <div className="chat-pane">
        <ChatPane 
          messages={messages} 
          onSendMessage={(msg) => setMessages([...messages, msg])}
        />
      </div>
      
      <div className="metrics-pane">
        <MetricsPane metrics={metrics} />
      </div>
      
      <div className="graph-pane">
        <GraphPane 
          data={graphData} 
          onNodeSelect={handleCodeSelect}
        />
      </div>
      
      {isPhase2Enabled ? (
        <>
          <div className="code-editor-pane">
            <CodeEditorPane 
              code={selectedCode} 
              readOnly={true}
            />
          </div>
          
          <div className="control-pane">
            <ControlPane 
              status={simulationStatus}
              onStart={handleStartSimulation}
              onStop={handleStopSimulation}
            />
            <TaggingPane 
              selectedNode={selectedCode}
              tags={tags}
              onTagUpdate={handleTagUpdate}
            />
          </div>
          
          <div className="logs-pane">
            <LogsPane logs={logs} />
          </div>
        </>
      ) : (
        <div className="control-pane">
          <ControlPane 
            status={simulationStatus}
            onStart={handleStartSimulation}
            onStop={handleStopSimulation}
          />
        </div>
      )}
    </div>
  );
}

export default App;
