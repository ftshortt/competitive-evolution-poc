import React, { useState, useEffect } from 'react';
import Editor from '@monaco-editor/react';

const CodeEditorPane = () => {
  const [selectedFile, setSelectedFile] = useState('');
  const [codeContent, setCodeContent] = useState('');
  const [executionOutput, setExecutionOutput] = useState('');
  const [isExecuting, setIsExecuting] = useState(false);
  const [files, setFiles] = useState([]);

  // Fetch available files in src/ scripts directory
  useEffect(() => {
    const fetchFiles = async () => {
      try {
        const response = await fetch('/api/phase2/files');
        const data = await response.json();
        setFiles(data.files || []);
      } catch (error) {
        console.error('Error fetching files:', error);
      }
    };
    fetchFiles();
  }, []);

  // Load file content when selected
  const handleFileSelect = async (filename) => {
    setSelectedFile(filename);
    try {
      const response = await fetch(`/api/phase2/files/${filename}`);
      const data = await response.json();
      setCodeContent(data.content || '');
    } catch (error) {
      console.error('Error loading file:', error);
      setCodeContent('');
    }
  };

  // Execute code
  const handleExecute = async () => {
    if (!selectedFile) {
      setExecutionOutput('Please select a file to execute');
      return;
    }

    setIsExecuting(true);
    setExecutionOutput('Executing...');

    try {
      const response = await fetch('/api/phase2/execute', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          filename: selectedFile,
          code: codeContent,
        }),
      });

      const data = await response.json();
      setExecutionOutput(data.output || data.error || 'Execution completed');
    } catch (error) {
      setExecutionOutput(`Error: ${error.message}`);
    } finally {
      setIsExecuting(false);
    }
  };

  return (
    <div className="code-editor-pane">
      <div className="editor-layout">
        {/* File Browser */}
        <div className="file-browser">
          <h3>Files (src/scripts)</h3>
          <ul className="file-list">
            {files.map((file) => (
              <li
                key={file}
                className={selectedFile === file ? 'selected' : ''}
                onClick={() => handleFileSelect(file)}
              >
                {file}
              </li>
            ))}
          </ul>
        </div>

        {/* Monaco Editor */}
        <div className="editor-container">
          <div className="editor-header">
            <h3>{selectedFile || 'Select a file'}</h3>
            <button
              onClick={handleExecute}
              disabled={!selectedFile || isExecuting}
              className="run-button"
            >
              {isExecuting ? 'Running...' : 'Run'}
            </button>
          </div>
          <Editor
            height="60vh"
            defaultLanguage="javascript"
            value={codeContent}
            onChange={(value) => setCodeContent(value || '')}
            theme="vs-dark"
            options={{
              minimap: { enabled: false },
              fontSize: 14,
              lineNumbers: 'on',
              roundedSelection: false,
              scrollBeyondLastLine: false,
              readOnly: false,
              automaticLayout: true,
            }}
          />
        </div>
      </div>

      {/* Output Display Area */}
      <div className="output-display">
        <h3>Output</h3>
        <pre className="output-content">{executionOutput || 'No output yet'}</pre>
      </div>
    </div>
  );
};

export default CodeEditorPane;
