import React, { useState, useEffect, useRef } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import axios from 'axios';

const API_URL = 'http://localhost:8000';

// Agent message bubble component
const AgentMessage = ({ message, agentName, role }) => {
  const isTriageAgent = role === 'triage';
  
  return (
    <div className="message-container mb-4">
      <div className={`flex items-center gap-2 mb-1 ${isTriageAgent ? 'text-neon-purple' : 'text-cyber-300'}`}>
        <div className={`w-8 h-8 rounded-md flex items-center justify-center text-white
          ${isTriageAgent ? 'bg-gradient-to-br from-purple-700 to-neon-purple shadow-neon-pink' : 'bg-gradient-to-br from-cyber-600 to-cyber-700 shadow-neon'}`}>
          {agentName.substring(0, 1).toUpperCase()}
        </div>
        <span className="font-semibold">{agentName}</span>
        <span className="text-xs text-gray-500">
          {isTriageAgent ? '(Triage Agent)' : '(Response Agent)'}
        </span>
      </div>
      
      <div className={`ml-10 p-3 rounded-lg border ${isTriageAgent ? 'bg-dark-lighter border-purple-800 text-gray-300' : 'bg-dark-lighter border-cyber-800 text-gray-300'}`}>
        {message}
      </div>
    </div>
  );
};

// User message bubble component
const UserMessage = ({ message }) => {
  return (
    <div className="message-container flex justify-end mb-4">
      <div className="bg-gradient-to-br from-cyber-600 to-cyber-700 text-white p-3 rounded-lg max-w-md shadow-md">
        {message}
      </div>
    </div>
  );
};

// Thinking indicator component
const ThinkingIndicator = () => {
  return (
    <div className="message-container mb-4">
      <div className="flex items-center gap-2 mb-1">
        <div className="w-8 h-8 rounded-md bg-green-900 bg-opacity-50 flex items-center justify-center text-green-400">
          <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 animate-pulse" viewBox="0 0 20 20" fill="currentColor">
            <path fillRule="evenodd" d="M11.3 1.046A1 1 0 0112 2v5h4a1 1 0 01.82 1.573l-7 10A1 1 0 018 18v-5H4a1 1 0 01-.82-1.573l7-10a1 1 0 011.12-.38z" clipRule="evenodd" />
          </svg>
        </div>
        <span className="font-semibold">System thinking...</span>
      </div>
      <div className="ml-10 p-3 rounded-lg bg-green-900 bg-opacity-30 border border-green-800 flex items-center">
        <div className="flex space-x-2">
          <div className="w-2 h-2 rounded-full bg-green-400 animate-bounce" style={{ animationDelay: '0ms' }}></div>
          <div className="w-2 h-2 rounded-full bg-green-400 animate-bounce" style={{ animationDelay: '150ms' }}></div>
          <div className="w-2 h-2 rounded-full bg-green-400 animate-bounce" style={{ animationDelay: '300ms' }}></div>
        </div>
      </div>
    </div>
  );
};

// Error message component
const ErrorMessage = ({ message }) => {
  return (
    <div className="message-container mb-4">
      <div className="flex items-center gap-2 mb-1 text-red-400">
        <div className="w-8 h-8 rounded-md bg-red-900 flex items-center justify-center text-white">
          <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
            <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
          </svg>
        </div>
        <span className="font-semibold">System Error</span>
      </div>
      
      <div className="ml-10 p-3 rounded-lg border bg-red-900 bg-opacity-30 border-red-800 text-red-300">
        {message}
      </div>
    </div>
  );
};

// Message component to handle different roles
const Message = ({ role, content, metadata, timestamp }) => {
  // Format timestamp
  const formatTime = (isoString) => {
    if (!isoString) return '';
    const date = new Date(isoString);
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  if (role === 'user') {
    return (
      <div className="message-container mb-4">
        <div className="flex items-center gap-2 mb-1">
          <div className="w-8 h-8 rounded-md bg-blue-600 flex items-center justify-center text-white">
            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M10 9a3 3 0 100-6 3 3 0 000 6zm-7 9a7 7 0 1114 0H3z" clipRule="evenodd" />
            </svg>
          </div>
          <span className="font-semibold">You</span>
          <span className="text-xs text-gray-400">{formatTime(timestamp)}</span>
        </div>
        <div className="ml-10 p-3 rounded-lg bg-blue-900 bg-opacity-30 border border-blue-800">
          {content}
        </div>
      </div>
    );
  }

  // For assistant or agent messages
  const agentName = metadata?.agent_name || (role === 'assistant' ? 'Assistant' : role);
  const agentRole = metadata?.agent_role || '';
  const bgColor = role === 'triage' ? 'bg-purple-900' : 'bg-green-900';
  const borderColor = role === 'triage' ? 'border-purple-800' : 'border-green-800';
  const iconColor = role === 'triage' ? 'text-purple-400' : 'text-green-400';
  
  // Check if we should show triage reasoning
  const showTriageReasoning = role === 'assistant' && metadata?.triage?.reasoning;

  return (
    <div className="message-container mb-4">
      <div className="flex items-center gap-2 mb-1">
        <div className={`w-8 h-8 rounded-md ${bgColor} bg-opacity-50 flex items-center justify-center ${iconColor}`}>
          <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
            <path d="M13 6a3 3 0 11-6 0 3 3 0 016 0zM18 8a2 2 0 11-4 0 2 2 0 014 0zM14 15a4 4 0 00-8 0v3h8v-3zM6 8a2 2 0 11-4 0 2 2 0 014 0zM16 18v-3a5.972 5.972 0 00-.75-2.906A3.005 3.005 0 0119 15v3h-3zM4.75 12.094A5.973 5.973 0 004 15v3H1v-3a3 3 0 013.75-2.906z" />
          </svg>
        </div>
        <div>
          <span className="font-semibold">{agentName}</span>
          {agentRole && <span className="text-xs ml-2 text-gray-400">{agentRole}</span>}
        </div>
        <span className="text-xs text-gray-400">{formatTime(timestamp)}</span>
      </div>
      
      {/* Show triage reasoning if available */}
      {showTriageReasoning && (
        <div className="ml-10 mb-2 p-2 rounded-lg bg-purple-900 bg-opacity-20 border border-purple-800 text-sm text-purple-300">
          <div className="flex items-center gap-1 mb-1">
            <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
            </svg>
            <span className="font-semibold text-xs">Triage: {metadata.triage.agent_name}</span>
          </div>
          <div className="text-xs italic">{metadata.triage.reasoning}</div>
        </div>
      )}
      
      <div className={`ml-10 p-3 rounded-lg ${bgColor} bg-opacity-30 border ${borderColor}`}>
        {content}
      </div>
    </div>
  );
};

const MultiAgentChat = () => {
  const { systemId } = useParams();
  const navigate = useNavigate();
  const [system, setSystem] = useState(null);
  const [messages, setMessages] = useState([]);
  const [newMessage, setNewMessage] = useState('');
  const [thinking, setThinking] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);
  const [conversationId, setConversationId] = useState(null);
  const messagesEndRef = useRef(null);

  // Fetch system details and conversation history
  useEffect(() => {
    const fetchSystemDetails = async () => {
      try {
        // Check if ID is valid
        if (!systemId || systemId === 'undefined') {
          setError('Invalid system ID. Please select a valid multi-agent system.');
          setLoading(false);
          // Redirect to home page after 3 seconds
          setTimeout(() => {
            navigate('/');
          }, 3000);
          return;
        }
        
        // Fetch system details
        const systemResponse = await axios.get(`${API_URL}/multi_agent_systems/${systemId}`);
        setSystem(systemResponse.data);
        
        // Fetch conversation history if needed
        // This would be implemented if we want to load previous conversations
        
        setLoading(false);
      } catch (error) {
        console.error('Error fetching system details:', error);
        setError('Failed to load system details. Please try again.');
        setLoading(false);
        // Redirect to home page after 3 seconds if system not found
        if (error.response && (error.response.status === 404 || error.response.status === 400)) {
          setTimeout(() => {
            navigate('/');
          }, 3000);
        }
      }
    };

    fetchSystemDetails();
  }, [systemId, navigate]);

  // Scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSendMessage = async () => {
    if (!newMessage.trim()) return;
    
    setError(''); // Clear any previous errors
    
    // Add user message to chat
    const userMessage = {
      role: 'user',
      content: newMessage,
      timestamp: new Date().toISOString(),
    };
    
    setMessages((prevMessages) => [...prevMessages, userMessage]);
    setNewMessage(''); // Clear input
    setThinking(true);
    
    try {
      const response = await axios.post(
        `${API_URL}/multi_agent_systems/${systemId}/interact`,
        { 
          message: newMessage,
          conversation_id: conversationId
        }
      );
      
      if (response.data.error) {
        // Add error message to chat
        setMessages((prevMessages) => [
          ...prevMessages, 
          { 
            role: 'error', 
            content: response.data.error,
            timestamp: new Date().toISOString() 
          }
        ]);
        console.error('Error from multi-agent system:', response.data.error);
      } else {
        // Update conversation ID if provided
        if (response.data.conversation_id) {
          setConversationId(response.data.conversation_id);
        }
        
        // Add assistant message to chat
        setMessages((prevMessages) => [
          ...prevMessages,
          {
            role: response.data.role || 'assistant',
            content: response.data.content,
            metadata: response.data.metadata || null,
            timestamp: new Date().toISOString(),
          },
        ]);
      }
    } catch (error) {
      console.error('Error sending message:', error);
      // Add error message to chat
      setMessages((prevMessages) => [
        ...prevMessages, 
        { 
          role: 'error', 
          content: error.response?.data?.detail || 'Failed to communicate with the multi-agent system. Please try again.',
          timestamp: new Date().toISOString() 
        }
      ]);
    } finally {
      setThinking(false);
    }
  };

  return (
    <div className="flex flex-col h-screen bg-dark">
      {/* Header */}
      <div className="bg-dark-lighter border-b border-gray-800 p-4">
        <div className="container mx-auto">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <Link to="/" className="text-gray-400 hover:text-white">
                <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
                </svg>
              </Link>
              <div>
                <h1 className="text-xl font-bold text-white">
                  {loading ? 'Loading...' : system?.name || 'Multi-Agent Chat'}
                </h1>
                {system && (
                  <p className="text-sm text-gray-400">{system.description}</p>
                )}
              </div>
            </div>
            
            {system && (
              <div className="flex items-center space-x-2">
                <span className="text-sm text-gray-400">Triage Agent:</span>
                <span className="px-2 py-1 bg-purple-900 bg-opacity-30 text-purple-300 rounded text-xs border border-purple-800">
                  {system.triage_agent}
                </span>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Main content */}
      <div className="flex-1 overflow-hidden container mx-auto p-4">
        <div className="flex flex-col h-full">
          {/* Messages area */}
          <div className="flex-1 overflow-y-auto mb-4 pr-2">
            {loading ? (
              <div className="flex items-center justify-center h-full">
                <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-cyber-400"></div>
              </div>
            ) : error && messages.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-full">
                <div className="text-red-400 text-center max-w-md p-6 bg-dark-lighter rounded-lg border border-red-800">
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-12 w-12 mx-auto mb-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <p className="text-lg font-semibold mb-2">Error</p>
                  <p className="mb-4">{error}</p>
                  <Link to="/" className="inline-block px-4 py-2 bg-cyber-600 text-white rounded-md hover:bg-cyber-500 transition-colors">
                    Return to Home
                  </Link>
                </div>
              </div>
            ) : (
              <div className="space-y-2 min-h-full">
                {messages.map((message, index) => (
                  <div key={index}>
                    {message.role === 'error' ? (
                      <ErrorMessage message={message.content} />
                    ) : (
                      <Message
                        role={message.role}
                        content={message.content}
                        metadata={message.metadata}
                        timestamp={message.timestamp}
                      />
                    )}
                  </div>
                ))}
                
                {thinking && <ThinkingIndicator />}
                
                {/* Empty div for scrolling to bottom */}
                <div ref={messagesEndRef} />
              </div>
            )}
          </div>

          {/* Input area */}
          <div className="bg-dark-lighter border border-gray-800 rounded-lg p-2">
            <div className="flex items-center">
              <input
                type="text"
                value={newMessage}
                onChange={(e) => setNewMessage(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
                placeholder="Type your message..."
                className="flex-1 bg-transparent border-none outline-none text-white placeholder-gray-500"
                disabled={thinking || loading}
              />
              <button
                onClick={handleSendMessage}
                disabled={thinking || !newMessage.trim() || loading}
                className={`ml-2 px-4 py-2 rounded-md ${
                  thinking || !newMessage.trim() || loading
                    ? 'bg-gray-700 text-gray-400 cursor-not-allowed'
                    : 'bg-cyber-600 text-white hover:bg-cyber-500'
                }`}
              >
                {thinking ? (
                  <span className="flex items-center">
                    <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    Processing
                  </span>
                ) : (
                  'Send'
                )}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default MultiAgentChat; 