import React from 'react'
import './App.css'

function ChatPane() {
  return (
    <div className="pane chat-pane">
      <h2>Chat</h2>
      <p>Chat interface will go here</p>
    </div>
  )
}

function MetricsPane() {
  return (
    <div className="pane metrics-pane">
      <h2>Metrics</h2>
      <p>Metrics display will go here</p>
    </div>
  )
}

function GraphPane() {
  return (
    <div className="pane graph-pane">
      <h2>Evolution Graph</h2>
      <p>Graph visualization will go here</p>
    </div>
  )
}

function ControlPane() {
  return (
    <div className="pane control-pane">
      <h2>Controls</h2>
      <p>Control panel will go here</p>
    </div>
  )
}

function App() {
  return (
    <div className="app-container">
      <h1>Competitive Evolution - Caretaker Interface</h1>
      <div className="pane-grid">
        <ChatPane />
        <MetricsPane />
        <GraphPane />
        <ControlPane />
      </div>
    </div>
  )
}

export default App
