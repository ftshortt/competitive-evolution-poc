import React, { useState } from 'react';
import { sendChatMessage } from '../services/api';

const ChatPane = () => {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSendMessage = async () => {
    if (!input.trim()) return;

    const userMessage = { role: 'user', content: input };
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setLoading(true);

    try {
      const response = await sendChatMessage(input);
      const assistantMessage = { role: 'assistant', content: response.message };
      setMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      console.error('Error sending message:', error);
      const errorMessage = { role: 'assistant', content: 'Error: Failed to send message' };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', padding: '10px' }}>
      <h3>Chat</h3>
      <div style={{ 
        flex: 1, 
        overflowY: 'auto', 
        border: '1px solid #ccc', 
        padding: '10px', 
        marginBottom: '10px',
        backgroundColor: '#f9f9f9'
      }}>
        {messages.map((msg, idx) => (
          <div key={idx} style={{
            marginBottom: '10px',
            padding: '8px',
            backgroundColor: msg.role === 'user' ? '#e3f2fd' : '#f5f5f5',
            borderRadius: '4px',
            borderLeft: `4px solid ${msg.role === 'user' ? '#2196f3' : '#4caf50'}`
          }}>
            <strong>{msg.role === 'user' ? 'You' : 'Assistant'}:</strong>
            <div style={{ marginTop: '5px' }}>{msg.content}</div>
          </div>
        ))}
        {loading && <div style={{ fontStyle: 'italic', color: '#666' }}>Assistant is typing...</div>}
      </div>
      <div style={{ display: 'flex', gap: '10px' }}>
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder="Type your message..."
          disabled={loading}
          style={{ 
            flex: 1, 
            padding: '10px', 
            fontSize: '14px',
            border: '1px solid #ccc',
            borderRadius: '4px'
          }}
        />
        <button 
          onClick={handleSendMessage} 
          disabled={loading || !input.trim()}
          style={{
            padding: '10px 20px',
            backgroundColor: '#2196f3',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: loading ? 'not-allowed' : 'pointer',
            fontSize: '14px'
          }}
        >
          Send
        </button>
      </div>
    </div>
  );
};

export default ChatPane;
