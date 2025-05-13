import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import axios from 'axios';

const API_URL = 'http://localhost:8000';

const ConversationHistory = () => {
  const { agentName } = useParams();
  const [conversations, setConversations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchConversations = async () => {
      try {
        setLoading(true);
        const response = await axios.get(`${API_URL}/agents/${agentName}/conversations`);
        setConversations(response.data);
        setLoading(false);
      } catch (err) {
        console.error('Error fetching conversations:', err);
        setError(`Failed to fetch conversations: ${err.response?.data?.detail || err.message}`);
        setLoading(false);
      }
    };

    fetchConversations();
  }, [agentName]);

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleString();
  };

  const deleteConversation = async (conversationId) => {
    if (window.confirm('Are you sure you want to delete this conversation?')) {
      try {
        await axios.delete(`${API_URL}/agents/${agentName}/conversations/${conversationId}`);
        setConversations(conversations.filter(conv => conv.conversation_id !== conversationId));
      } catch (err) {
        console.error('Error deleting conversation:', err);
        setError(`Failed to delete conversation: ${err.response?.data?.detail || err.message}`);
      }
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="relative w-16 h-16">
          <div className="absolute top-0 left-0 w-full h-full border-4 border-cyber-300 border-t-transparent rounded-full animate-spin"></div>
          <div className="absolute top-2 left-2 w-12 h-12 border-4 border-neon-pink border-b-transparent rounded-full animate-spin"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto">
      <div className="bg-dark-card rounded-xl shadow-lg overflow-hidden border border-gray-800">
        <div className="bg-gradient-to-r from-cyber-600 to-cyber-700 p-4 relative overflow-hidden">
          {/* Background grid pattern */}
          <div className="absolute inset-0 opacity-10">
            <div className="absolute inset-0" style={{ 
              backgroundImage: 'linear-gradient(to right, #fff 1px, transparent 1px), linear-gradient(to bottom, #fff 1px, transparent 1px)', 
              backgroundSize: '20px 20px' 
            }}></div>
          </div>
          
          <div className="relative z-10 flex items-center">
            <div className="w-10 h-10 rounded-md bg-cyber-800 flex items-center justify-center mr-3 shadow-inner">
              <span className="text-cyber-300 font-mono font-bold">{agentName.charAt(0)}</span>
            </div>
            <div>
              <h1 className="text-2xl font-bold text-white">Conversation History</h1>
              <p className="text-cyber-200">Agent: {agentName}</p>
            </div>
          </div>
        </div>

        <div className="p-4 bg-dark-light">
          {error && (
            <div className="bg-red-900 bg-opacity-20 border border-red-800 text-red-400 p-4 mb-4 rounded-lg">
              {error}
            </div>
          )}

          {conversations.length === 0 ? (
            <div className="text-center py-10 bg-dark-lighter rounded-xl border border-gray-800 p-8">
              <svg xmlns="http://www.w3.org/2000/svg" className="h-16 w-16 mx-auto mb-4 text-gray-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
              </svg>
              <p className="text-gray-400 mb-4">No conversations found</p>
              <Link 
                to={`/chat/${agentName}`} 
                className="inline-block px-4 py-2 rounded-md bg-gradient-to-r from-cyber-500 to-cyber-600 text-white shadow-md hover:shadow-neon transition-all duration-300"
              >
                Start a new conversation
              </Link>
            </div>
          ) : (
            <div className="space-y-4">
              {conversations.map((conversation) => (
                <div 
                  key={conversation.conversation_id} 
                  className="border border-gray-800 rounded-xl hover:shadow-neon transition-all duration-300 bg-dark-card overflow-hidden"
                >
                  <div className="p-4 flex flex-col md:flex-row justify-between md:items-center">
                    <div>
                      <h2 className="text-lg font-semibold text-white">{conversation.title}</h2>
                      <div className="flex flex-wrap gap-4 text-sm text-gray-500 mt-1">
                        <span className="flex items-center">
                          <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 mr-1 text-cyber-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                          </svg>
                          Created: {formatDate(conversation.created_at)}
                        </span>
                        <span className="flex items-center">
                          <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 mr-1 text-cyber-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                          </svg>
                          Updated: {formatDate(conversation.updated_at)}
                        </span>
                        <span className="flex items-center">
                          <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 mr-1 text-cyber-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 8h2a2 2 0 012 2v6a2 2 0 01-2 2h-2v4l-4-4H9a1.994 1.994 0 01-1.414-.586m0 0L11 14h4a2 2 0 002-2V6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2v4l.586-.586z" />
                          </svg>
                          {conversation.messages.length} messages
                        </span>
                      </div>
                    </div>
                    <div className="flex gap-2 mt-4 md:mt-0">
                      <Link 
                        to={`/chat/${agentName}?conversation=${conversation.conversation_id}`}
                        className="bg-gradient-to-r from-cyber-500 to-cyber-600 text-white px-3 py-1 rounded-md hover:shadow-neon flex items-center"
                      >
                        <span>Continue</span>
                        <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 ml-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 5l7 7-7 7M5 5l7 7-7 7" />
                        </svg>
                      </Link>
                      <button
                        onClick={() => deleteConversation(conversation.conversation_id)}
                        className="bg-red-900 bg-opacity-30 border border-red-800 text-red-400 px-3 py-1 rounded-md hover:bg-opacity-50 transition-colors duration-200"
                      >
                        Delete
                      </button>
                    </div>
                  </div>
                  
                  {conversation.messages.length > 0 && (
                    <div className="border-t border-gray-800 p-4 text-gray-400 bg-dark-lighter">
                      <div className="flex items-center">
                        <span className="font-medium text-cyber-300 mr-2">Last message:</span>
                        <p className="truncate">
                          {conversation.messages[conversation.messages.length - 1].content.substring(0, 100)}
                          {conversation.messages[conversation.messages.length - 1].content.length > 100 ? '...' : ''}
                        </p>
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
      
      <div className="mt-4 flex justify-end">
        <Link to="/" className="text-cyber-300 hover:text-cyber-200 flex items-center group">
          <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
          </svg>
          <span>Back to Home</span>
        </Link>
      </div>
    </div>
  );
};

export default ConversationHistory; 