import React, { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import axios from 'axios';
import { API_URL } from '../config';

const ProjectChat = () => {
  const { projectId } = useParams();
  const navigate = useNavigate();
  
  const [project, setProject] = useState(null);
  const [messages, setMessages] = useState([]);
  const [newMessage, setNewMessage] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [isThinking, setIsThinking] = useState(false);
  const [error, setError] = useState('');
  
  const messagesEndRef = useRef(null);
  const chatInputRef = useRef(null);
  
  // Fetch project details
  useEffect(() => {
    const fetchProject = async () => {
      try {
        const response = await axios.get(`${API_URL}/projects/${projectId}`);
        setProject(response.data);
        setIsLoading(false);
      } catch (error) {
        console.error('Error fetching project:', error);
        setError(`Failed to fetch project: ${error.response?.data?.detail || error.message}`);
        setIsLoading(false);
      }
    };
    
    fetchProject();
  }, [projectId]);
  
  // Scroll to bottom on new messages
  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages]);
  
  // Send a message to the project
  const sendMessage = async (e) => {
    e.preventDefault();
    
    if (!newMessage.trim()) return;
    
    // Add user message to the UI immediately
    const userMessage = { role: 'user', content: newMessage };
    const messageToSend = newMessage;
    setMessages(prevMessages => [...prevMessages, userMessage]);
    setNewMessage('');
    setIsThinking(true);
    setError('');
    
    try {
      // Send the message to the API without conversation ID
      const response = await axios.post(`${API_URL}/projects/${projectId}/interact`, {
        message: messageToSend
      });
      
      // Add response to messages
      if (response.data.response) {
        const assistantMessage = { role: 'assistant', content: response.data.response };
        setMessages(prevMessages => [...prevMessages, assistantMessage]);
      } else if (response.data.error) {
        const errorMsg = `Error: ${response.data.error}`;
        setError(errorMsg);
        
        // Add error message to chat
        const errorMessage = { 
          role: 'system', 
          content: errorMsg 
        };
        setMessages(prevMessages => [...prevMessages, errorMessage]);
      } else {
        // Handle case where response is empty
        const errorMessage = { 
          role: 'system', 
          content: 'The AI did not provide a response. Please try again.' 
        };
        setMessages(prevMessages => [...prevMessages, errorMessage]);
      }
    } catch (error) {
      console.error('Error sending message:', error);
      const errorMsg = error.response?.data?.detail || error.message;
      setError(`Failed to send message: ${errorMsg}`);
      
      // Add error message to the chat
      const errorMessage = { 
        role: 'system', 
        content: `Error: ${errorMsg}` 
      };
      setMessages(prevMessages => [...prevMessages, errorMessage]);
    } finally {
      setIsThinking(false);
    }
  };
  
  // Start a new chat by clearing messages
  const startNewChat = () => {
    setMessages([]);
  };
  
  if (isLoading) {
    return (
      <div className="flex justify-center items-center h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary"></div>
      </div>
    );
  }
  
  if (error && !project) {
    return (
      <div className="container mx-auto p-4">
        <div className="bg-red-100 border border-red-300 text-red-700 px-4 py-3 rounded">
          {error}
        </div>
        <div className="mt-4">
          <Link to="/roadmap" className="text-primary hover:underline">
            &larr; Back to Projects
          </Link>
        </div>
      </div>
    );
  }
  
  return (
    <div className="container mx-auto p-4 h-screen flex flex-col">
      {/* Header */}
      <div className="bg-white border-b pb-4 mb-4 flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">{project?.title}</h1>
          <p className="text-sm text-gray-600">{project?.description?.substring(0, 100)}...</p>
        </div>
        <div className="flex space-x-2">
          <button
            onClick={startNewChat}
            className="px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 transition-colors"
          >
            New Conversation
          </button>
          <Link to={`/projects/${projectId}`} className="px-4 py-2 bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200">
            Back to Project
          </Link>
        </div>
      </div>
      
      {/* Chat Interface */}
      <div className="flex flex-1 gap-4 overflow-hidden">
        {/* Main chat area */}
        <div className="flex-1 flex flex-col bg-white border rounded-lg overflow-hidden">
          {/* Messages */}
          <div className="flex-1 p-4 overflow-y-auto">
            {messages.length === 0 ? (
              <div className="h-full flex flex-col justify-center items-center text-gray-400">
                <svg xmlns="http://www.w3.org/2000/svg" className="h-12 w-12 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
                </svg>
                <p className="text-center">Ask a question to start a conversation with this project</p>
                {project?.agents?.length > 1 && (
                  <p className="text-center mt-2 text-sm">
                    This project uses {project.agents.length} agents in sequence for processing
                  </p>
                )}
              </div>
            ) : (
              <div className="space-y-4">
                {messages.map((message, index) => (
                  <div
                    key={index}
                    className={`flex ${
                      message.role === 'user' ? 'justify-end' : 'justify-start'
                    }`}
                  >
                    <div
                      className={`max-w-3/4 rounded-lg p-3 ${
                        message.role === 'user'
                          ? 'bg-blue-500 text-white'
                          : message.role === 'system'
                          ? 'bg-red-100 text-red-800'
                          : 'bg-gray-100 text-gray-800'
                      }`}
                    >
                      <p className="whitespace-pre-wrap">{message.content}</p>
                    </div>
                  </div>
                ))}
                <div ref={messagesEndRef} />
              </div>
            )}
          </div>
          
          {/* Input */}
          <div className="border-t p-4">
            <form onSubmit={sendMessage} className="flex gap-2">
              <input
                type="text"
                value={newMessage}
                onChange={(e) => setNewMessage(e.target.value)}
                placeholder="Type your message..."
                className="flex-1 p-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                ref={chatInputRef}
                disabled={isThinking}
              />
              <button
                type="submit"
                disabled={isThinking || !newMessage.trim()}
                className={`px-4 py-2 rounded-lg ${
                  isThinking || !newMessage.trim()
                    ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                    : 'bg-blue-500 text-white hover:bg-blue-600'
                }`}
              >
                {isThinking ? (
                  <div className="flex items-center">
                    <div className="animate-spin rounded-full h-4 w-4 border-t-2 border-b-2 border-white mr-2"></div>
                    {project?.agents?.length > 1 ? 'Processing...' : 'Thinking...'}
                  </div>
                ) : (
                  'Send'
                )}
              </button>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ProjectChat; 