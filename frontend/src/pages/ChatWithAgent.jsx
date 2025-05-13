import React, { useState, useEffect, useRef } from 'react';
import { useParams, useSearchParams, Link, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { API_URL } from '../config';

const ChatWithAgent = () => {
  const { agentName } = useParams();
  const [searchParams] = useSearchParams();
  const conversationId = searchParams.get('conversation');
  const navigate = useNavigate();
  
  const [agent, setAgent] = useState(null);
  const [messages, setMessages] = useState([]);
  const [newMessage, setNewMessage] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [isThinking, setIsThinking] = useState(false);
  const [currentConversationId, setCurrentConversationId] = useState(conversationId);
  const [error, setError] = useState('');
  
  // Add Slack deployment state
  const [showSlackModal, setShowSlackModal] = useState(false);
  const [slackBotToken, setSlackBotToken] = useState('');
  const [slackAppToken, setSlackAppToken] = useState('');
  const [deployingToSlack, setDeployingToSlack] = useState(false);
  const [slackDeploymentStatus, setSlackDeploymentStatus] = useState(null);
  
  const messagesEndRef = useRef(null);
  const chatInputRef = useRef(null);
  
  // Fetch agent details
  useEffect(() => {
    const fetchAgent = async () => {
      try {
        const response = await axios.get(`${API_URL}/agent/${agentName}`);
        setAgent(response.data);
        setIsLoading(false);
        
        // Also fetch Slack status
        fetchSlackStatus();
      } catch (error) {
        console.error('Error fetching agent:', error);
        setError(`Failed to fetch agent: ${error.response?.data?.detail || error.message}`);
        setIsLoading(false);
      }
    };
    
    fetchAgent();
  }, [agentName]);
  
  // Fetch Slack deployment status for this agent
  const fetchSlackStatus = async () => {
    try {
      const response = await axios.get(`${API_URL}/agents/${agentName}/slack/status`);
      setSlackDeploymentStatus(response.data);
    } catch (error) {
      console.error('Error fetching Slack status:', error);
      // Don't set error state here as it's not critical
    }
  };
  
  // Deploy agent to Slack
  const deployToSlack = async () => {
    if (!slackBotToken || !slackAppToken) {
      setError('Both Slack Bot Token and App Token are required');
      return;
    }
    
    setDeployingToSlack(true);
    setError('');
    
    try {
      const response = await axios.post(`${API_URL}/agents/${agentName}/deploy_to_slack`, {
        bot_token: slackBotToken,
        app_token: slackAppToken
      });
      
      // Success
      setSlackDeploymentStatus({
        deployed: true,
        status: response.data.status
      });
      setShowSlackModal(false);
      
      // Add a system message about successful deployment
      setMessages([
        ...messages,
        { 
          role: 'system', 
          content: `Agent has been successfully deployed to Slack! It's now ready to receive messages.` 
        }
      ]);
    } catch (error) {
      console.error('Error deploying to Slack:', error);
      setError(`Failed to deploy to Slack: ${error.response?.data?.detail || error.message}`);
    } finally {
      setDeployingToSlack(false);
    }
  };
  
  // Toggle Slack bot status (start/stop)
  const toggleSlackBot = async (action) => {
    try {
      const response = await axios.post(`${API_URL}/agents/${agentName}/slack/toggle`, {
        action: action
      });
      
      // Update status
      setSlackDeploymentStatus({
        deployed: true,
        status: response.data.status
      });
      
      // Add a system message
      setMessages([
        ...messages,
        { 
          role: 'system', 
          content: `Agent has been ${action === 'start' ? 'started' : 'stopped'} on Slack.` 
        }
      ]);
    } catch (error) {
      console.error(`Error ${action}ing Slack bot:`, error);
      setError(`Failed to ${action} Slack bot: ${error.response?.data?.detail || error.message}`);
    }
  };
  
  // Undeploy from Slack
  const undeployFromSlack = async () => {
    if (!window.confirm('Are you sure you want to undeploy this agent from Slack?')) {
      return;
    }
    
    try {
      await axios.delete(`${API_URL}/agents/${agentName}/slack`);
      
      // Update status
      setSlackDeploymentStatus({
        deployed: false,
        status: 'not_deployed'
      });
      
      // Add a system message
      setMessages([
        ...messages,
        { 
          role: 'system', 
          content: 'Agent has been undeployed from Slack.' 
        }
      ]);
    } catch (error) {
      console.error('Error undeploying from Slack:', error);
      setError(`Failed to undeploy from Slack: ${error.response?.data?.detail || error.message}`);
    }
  };
  
  // Fetch conversation history if a conversation ID is provided
  useEffect(() => {
    const fetchConversation = async () => {
      if (currentConversationId) {
        try {
          const response = await axios.get(`${API_URL}/agents/${agentName}/conversations/${currentConversationId}`);
          setMessages(response.data.messages.map(msg => ({
            role: msg.role,
            content: msg.content
          })));
        } catch (error) {
          console.error('Error fetching conversation:', error);
          // Create a new conversation if the specified one doesn't exist
          const newConversation = await createNewConversation();
          setCurrentConversationId(newConversation.conversation_id);
        }
      } else {
        // Create a new conversation
        const newConversation = await createNewConversation();
        setCurrentConversationId(newConversation.conversation_id);
      }
    };
    
    if (!isLoading) {
      fetchConversation();
    }
  }, [agentName, isLoading, currentConversationId]);
  
  // Scroll to bottom on new messages
  useEffect(() => {
    if (messagesEndRef.current) {
      // Use a more stable scrolling approach
      const scrollContainer = messagesEndRef.current.parentElement;
      const isScrolledToBottom = scrollContainer.scrollHeight - scrollContainer.clientHeight <= scrollContainer.scrollTop + 100;
      
      // Only auto-scroll if user was already at the bottom
      if (isScrolledToBottom) {
        messagesEndRef.current.scrollIntoView({ behavior: 'smooth', block: 'end' });
      }
    }
  }, [messages]);
  
  // Create a new conversation
  const createNewConversation = async () => {
    try {
      const response = await axios.post(`${API_URL}/agents/${agentName}/conversations`, {
        title: `Chat with ${agentName}`
      });
      return response.data;
    } catch (error) {
      console.error('Error creating conversation:', error);
      setError(`Failed to create conversation: ${error.response?.data?.detail || error.message}`);
      return null;
    }
  };
  
  // Send a message to the agent
  const sendMessage = async (e) => {
    e.preventDefault();
    
    if (!newMessage.trim()) return;
    
    // Add user message to the chat immediately
    setMessages([...messages, { role: 'user', content: newMessage }]);
    const messageToSend = newMessage;
    setNewMessage('');
    setIsThinking(true);
    setError('');
    
    try {
      // Send the message to the backend without conversation ID
      const response = await axios.post(`${API_URL}/interact/${agentName}`, {
        message: messageToSend
      });
      
      // Add the agent's response to the chat
      setMessages(prevMessages => [
        ...prevMessages,
        { role: 'assistant', content: response.data.response }
      ]);
    } catch (error) {
      console.error('Error sending message:', error);
      const errorMsg = error.response?.data?.detail || error.message;
      setError(`Error: ${errorMsg}`);
      
      // Add an error message to the chat
      setMessages(prevMessages => [
        ...prevMessages,
        { role: 'system', content: `Error: ${errorMsg}` }
      ]);
    } finally {
      setIsThinking(false);
      chatInputRef.current?.focus();
    }
  };
  
  if (isLoading) {
    return <div className="flex justify-center items-center h-64">Loading...</div>;
  }
  
  if (!agent) {
    return (
      <div className="text-center p-8">
        <h2 className="text-xl font-bold text-red-500">Agent not found</h2>
        <p className="mt-4">
          <Link to="/" className="text-blue-500 hover:underline">
            Return to home
          </Link>
        </p>
      </div>
    );
  }
  
  return (
    <div className="max-w-4xl mx-auto bg-dark-card rounded-xl shadow-lg overflow-hidden border border-gray-800">
      {/* Agent info header */}
      <div className="bg-gradient-to-r from-cyber-600 to-cyber-700 p-4 relative overflow-hidden">
        {/* Background grid pattern */}
        <div className="absolute inset-0 opacity-10">
          <div className="absolute inset-0" style={{ 
            backgroundImage: 'linear-gradient(to right, #fff 1px, transparent 1px), linear-gradient(to bottom, #fff 1px, transparent 1px)', 
            backgroundSize: '20px 20px' 
          }}></div>
        </div>
        
        <div className="relative z-10 flex justify-between items-center">
          <div>
            <h1 className="text-2xl font-bold text-white flex items-center">
              <div className="w-10 h-10 rounded-md bg-cyber-800 flex items-center justify-center mr-3 shadow-inner">
                <span className="text-cyber-300 font-mono font-bold">{agent?.name?.charAt(0) || 'A'}</span>
              </div>
              {agent?.name}
            </h1>
            <p className="text-cyber-200 mt-1">{agent?.role}</p>
          </div>
          <div className="flex space-x-2">
            <Link
              to={`/agents/${agentName}/history`}
              className="bg-dark bg-opacity-30 hover:bg-opacity-40 backdrop-blur-sm px-3 py-1 rounded-md text-sm text-white border border-gray-700 transition-all duration-200"
            >
              View History
            </Link>
            <button 
              onClick={async () => {
                const newConversation = await createNewConversation();
                if (newConversation) {
                  setCurrentConversationId(newConversation.conversation_id);
                  setMessages([]);
                }
              }}
              className="bg-dark bg-opacity-30 hover:bg-opacity-40 backdrop-blur-sm px-3 py-1 rounded-md text-sm text-white border border-gray-700 transition-all duration-200"
            >
              New Chat
            </button>
            
            {/* Deploy to Slack button */}
            <button 
              onClick={() => setShowSlackModal(true)} 
              className="bg-dark bg-opacity-30 hover:bg-opacity-40 backdrop-blur-sm px-3 py-1 rounded-md text-sm text-white border border-green-700 transition-all duration-200 flex items-center"
            >
              <svg className="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <path d="M6 17C6 18.6569 4.65685 20 3 20C1.34315 20 0 18.6569 0 17C0 15.3431 1.34315 14 3 14C3.35064 14 3.68722 14.0602 4 14.1707V7C4 6.44772 4.44772 6 5 6H8V3C8 1.34315 9.34315 0 11 0C12.6569 0 14 1.34315 14 3C14 4.65685 12.6569 6 11 6H8V9H15V6.82929C14.6872 6.93985 14.3506 7 14 7C12.3431 7 11 5.65685 11 4C11 2.34315 12.3431 1 14 1C15.6569 1 17 2.34315 17 4C17 4.35064 16.9398 4.68722 16.8293 5H20C20.5523 5 21 5.44772 21 6V9.82929C21.3128 9.93985 21.6494 10 22 10C23.6569 10 25 11.3431 25 13C25 14.6569 23.6569 16 22 16C20.3431 16 19 14.6569 19 13C19 12.6494 19.0602 12.3128 19.1707 12H16V19C16 19.5523 15.5523 20 15 20H12V16.8293C11.6872 16.9398 11.3506 17 11 17C9.34315 17 8 15.6569 8 14C8 12.3431 9.34315 11 11 11C12.6569 11 14 12.3431 14 14C14 14.3506 13.9398 14.6872 13.8293 15H12V17H15V12H19.1707C19.0602 12.3128 19 12.6494 19 13C19 14.6569 20.3431 16 22 16C23.6569 16 25 14.6569 25 13C25 11.3431 23.6569 10 22 10C21.6494 10 21.3128 10.0602 21 10.1707V6H16.8293C16.9398 5.68722 17 5.35064 17 5C17 3.34315 15.6569 2 14 2C12.3431 2 11 3.34315 11 5C11 6.65685 12.3431 8 14 8C14.3506 8 14.6872 7.93985 15 7.82929V10H8V14.1707C8.31278 14.0602 8.64936 14 9 14C10.6569 14 12 15.3431 12 17C12 18.6569 10.6569 20 9 20C7.34315 20 6 18.6569 6 17ZM8 17C8 15.3431 6.65685 14 5 14C3.34315 14 2 15.3431 2 17C2 18.6569 3.34315 20 5 20C6.65685 20 8 18.6569 8 17Z" />
              </svg>
              Slack
            </button>
          </div>
        </div>
        
        {/* Slack bot controls - only shown if deployed */}
        {slackDeploymentStatus?.deployed && (
          <div className="mt-2 relative z-10 flex items-center justify-end space-x-2">
            <div className="text-xs text-cyber-200 mr-2">
              Slack Status: <span className={slackDeploymentStatus.status === 'running' ? 'text-green-400' : 'text-yellow-400'}>
                {slackDeploymentStatus.status === 'running' ? 'Running' : 'Stopped'}
              </span>
            </div>
            {slackDeploymentStatus.status === 'running' ? (
              <button 
                onClick={() => toggleSlackBot('stop')} 
                className="bg-dark bg-opacity-30 hover:bg-opacity-40 backdrop-blur-sm px-2 py-0.5 rounded-md text-xs text-white border border-yellow-700 transition-all duration-200 flex items-center"
                title="Pause Slack bot"
              >
                <svg className="w-3 h-3 mr-1" fill="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                  <rect x="6" y="4" width="4" height="16" rx="1" />
                  <rect x="14" y="4" width="4" height="16" rx="1" />
                </svg>
                Pause
              </button>
            ) : (
              <button 
                onClick={() => toggleSlackBot('start')} 
                className="bg-dark bg-opacity-30 hover:bg-opacity-40 backdrop-blur-sm px-2 py-0.5 rounded-md text-xs text-white border border-green-700 transition-all duration-200 flex items-center"
                title="Start Slack bot"
              >
                <svg className="w-3 h-3 mr-1" fill="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                  <path d="M8 5v14l11-7z" />
                </svg>
                Start
              </button>
            )}
            <button 
              onClick={undeployFromSlack} 
              className="bg-dark bg-opacity-30 hover:bg-opacity-40 backdrop-blur-sm px-2 py-0.5 rounded-md text-xs text-white border border-red-700 transition-all duration-200"
              title="Undeploy from Slack"
            >
              Undeploy
            </button>
          </div>
        )}
        
        {/* Display tools */}
        {agent?.tools && agent.tools.length > 0 && (
          <div className="mt-3 relative z-10">
            <p className="text-xs text-cyber-200 mb-1">Tools:</p>
            <div className="flex flex-wrap gap-1">
              {agent.tools.map((tool) => (
                <span
                  key={tool}
                  className="bg-dark bg-opacity-30 backdrop-blur-sm px-2 py-0.5 rounded-full text-xs text-cyber-300 border border-cyber-700"
                >
                  {tool}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>
      
      {/* Slack deployment modal */}
      {showSlackModal && (
        <div className="fixed inset-0 bg-black bg-opacity-80 flex items-center justify-center z-50">
          <div className="bg-dark-card rounded-lg border border-cyber-700 shadow-lg p-6 w-full max-w-md">
            <h2 className="text-xl font-bold text-white mb-4 flex items-center">
              <svg className="w-6 h-6 mr-2 text-cyber-400" fill="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <path d="M6 17C6 18.6569 4.65685 20 3 20C1.34315 20 0 18.6569 0 17C0 15.3431 1.34315 14 3 14C3.35064 14 3.68722 14.0602 4 14.1707V7C4 6.44772 4.44772 6 5 6H8V3C8 1.34315 9.34315 0 11 0C12.6569 0 14 1.34315 14 3C14 4.65685 12.6569 6 11 6H8V9H15V6.82929C14.6872 6.93985 14.3506 7 14 7C12.3431 7 11 5.65685 11 4C11 2.34315 12.3431 1 14 1C15.6569 1 17 2.34315 17 4C17 4.35064 16.9398 4.68722 16.8293 5H20C20.5523 5 21 5.44772 21 6V9.82929C21.3128 9.93985 21.6494 10 22 10C23.6569 10 25 11.3431 25 13C25 14.6569 23.6569 16 22 16C20.3431 16 19 14.6569 19 13C19 12.6494 19.0602 12.3128 19.1707 12H16V19C16 19.5523 15.5523 20 15 20H12V16.8293C11.6872 16.9398 11.3506 17 11 17C9.34315 17 8 15.6569 8 14C8 12.3431 9.34315 11 11 11C12.6569 11 14 12.3431 14 14C14 14.3506 13.9398 14.6872 13.8293 15H12V17H15V12H19.1707C19.0602 12.3128 19 12.6494 19 13C19 14.6569 20.3431 16 22 16C23.6569 16 25 14.6569 25 13C25 11.3431 23.6569 10 22 10C21.6494 10 21.3128 10.0602 21 10.1707V6H16.8293C16.9398 5.68722 17 5.35064 17 5C17 3.34315 15.6569 2 14 2C12.3431 2 11 3.34315 11 5C11 6.65685 12.3431 8 14 8C14.3506 8 14.6872 7.93985 15 7.82929V10H8V14.1707C8.31278 14.0602 8.64936 14 9 14C10.6569 14 12 15.3431 12 17C12 18.6569 10.6569 20 9 20C7.34315 20 6 18.6569 6 17ZM8 17C8 15.3431 6.65685 14 5 14C3.34315 14 2 15.3431 2 17C2 18.6569 3.34315 20 5 20C6.65685 20 8 18.6569 8 17Z" />
              </svg>
              Deploy {agent?.name} to Slack
            </h2>
            <p className="mb-4 text-gray-400">
              Enter your Slack Bot User OAuth Token and App Level Token to deploy this agent as a Slack bot.
              <a 
                href="https://api.slack.com/start/building/bolt-js" 
                target="_blank" 
                rel="noopener noreferrer"
                className="ml-1 text-cyber-400 hover:underline"
              >
                Learn how to create a Slack app
              </a>
            </p>
            
            <div className="mb-4">
              <label className="block text-gray-300 mb-2 text-sm" htmlFor="botToken">
                Bot User OAuth Token <span className="text-cyber-500">*</span>
              </label>
              <input
                id="botToken"
                type="text"
                className="w-full bg-dark-lighter border border-gray-700 rounded p-2 text-white"
                placeholder="xoxb-..."
                value={slackBotToken}
                onChange={(e) => setSlackBotToken(e.target.value)}
              />
            </div>
            
            <div className="mb-4">
              <label className="block text-gray-300 mb-2 text-sm" htmlFor="appToken">
                App Level Token <span className="text-cyber-500">*</span>
              </label>
              <input
                id="appToken"
                type="text"
                className="w-full bg-dark-lighter border border-gray-700 rounded p-2 text-white"
                placeholder="xapp-..."
                value={slackAppToken}
                onChange={(e) => setSlackAppToken(e.target.value)}
              />
            </div>
            
            {error && (
              <div className="mb-4 p-2 bg-red-900 bg-opacity-30 border border-red-800 text-red-300 rounded text-sm">
                {error}
              </div>
            )}
            
            <div className="flex justify-end space-x-2">
              <button 
                onClick={() => {
                  setShowSlackModal(false);
                  setError('');
                }}
                className="px-4 py-2 bg-dark-lighter border border-gray-700 rounded hover:bg-dark text-gray-300"
                disabled={deployingToSlack}
              >
                Cancel
              </button>
              <button 
                onClick={deployToSlack}
                className="px-4 py-2 bg-gradient-to-r from-cyber-500 to-cyber-600 text-white rounded hover:from-cyber-400 hover:to-cyber-500"
                disabled={deployingToSlack}
              >
                {deployingToSlack ? 
                  <span className="flex items-center">
                    <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    Deploying...
                  </span> 
                  : 'Deploy'
                }
              </button>
            </div>
          </div>
        </div>
      )}
      
      {/* Chat messages */}
      <div className="h-[500px] overflow-y-auto p-4 bg-dark-light" id="chat-messages-container">
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-gray-400">
            <div className="w-16 h-16 mb-4 rounded-full bg-dark-lighter flex items-center justify-center">
              <svg xmlns="http://www.w3.org/2000/svg" className="h-8 w-8 text-cyber-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
              </svg>
            </div>
            <p className="text-xl font-light">Start a conversation with {agent?.name}</p>
            <p className="text-sm mt-2 text-gray-500">This agent can help with {agent?.role} tasks</p>
          </div>
        ) : (
          <div className="space-y-4 min-h-full">
            {messages.map((message, index) => (
              <div
                key={index}
                className={`message-container flex ${
                  message.role === 'user' ? 'justify-end' : 'justify-start'
                }`}
              >
                <div
                  className={`max-w-[80%] p-3 rounded-lg ${
                    message.role === 'user'
                      ? 'bg-gradient-to-br from-cyber-600 to-cyber-700 text-white rounded-br-none shadow-md'
                      : message.role === 'error'
                      ? 'bg-red-900 bg-opacity-30 border border-red-800 text-red-300 rounded-bl-none'
                      : 'bg-dark-lighter border border-gray-800 text-gray-300 rounded-bl-none'
                  }`}
                >
                  <div className="text-sm whitespace-pre-wrap">{message.content}</div>
                </div>
              </div>
            ))}
            
            {/* Thinking indicator */}
            {isThinking && (
              <div className="flex justify-start">
                <div className="max-w-[80%] bg-dark-lighter p-3 rounded-lg rounded-bl-none border border-gray-800">
                  <div className="flex space-x-2">
                    <div className="h-2 w-2 bg-cyber-400 rounded-full animate-pulse"></div>
                    <div className="h-2 w-2 bg-cyber-400 rounded-full animate-pulse delay-75"></div>
                    <div className="h-2 w-2 bg-cyber-400 rounded-full animate-pulse delay-150"></div>
                  </div>
                </div>
              </div>
            )}
            
            {/* This invisible div helps with scrolling to the bottom */}
            <div ref={messagesEndRef} className="h-1" />
          </div>
        )}
      </div>
      
      {/* Error message */}
      {error && (
        <div className="bg-red-900 bg-opacity-20 border-t border-red-800 p-3">
          <p className="text-red-400 text-sm">{error}</p>
        </div>
      )}
      
      {/* Message input */}
      <div className="border-t border-gray-800 p-4 bg-dark-card">
        <form onSubmit={sendMessage} className="flex space-x-2">
          <input
            ref={chatInputRef}
            type="text"
            className="flex-1 bg-dark-lighter border border-gray-800 rounded-lg px-4 py-2 text-gray-200 focus:outline-none focus:ring-2 focus:ring-cyber-500 focus:border-transparent"
            placeholder={`Message ${agent?.name || 'agent'}...`}
            value={newMessage}
            onChange={(e) => setNewMessage(e.target.value)}
            disabled={isThinking}
          />
          <button
            type="submit"
            className={`px-4 py-2 rounded-lg flex items-center ${
              isThinking || !newMessage.trim()
                ? 'bg-gray-700 cursor-not-allowed text-gray-400'
                : 'bg-gradient-to-r from-cyber-500 to-cyber-600 hover:from-cyber-400 hover:to-cyber-500 text-white shadow-md hover:shadow-neon'
            } transition-all duration-200`}
            disabled={isThinking || !newMessage.trim()}
          >
            <span>Send</span>
            <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 ml-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 5l7 7-7 7M5 5l7 7-7 7" />
            </svg>
          </button>
        </form>
      </div>
    </div>
  );
};

export default ChatWithAgent; 