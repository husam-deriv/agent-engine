import React, { useState, useEffect } from 'react';
import AgentCard from '../components/AgentCard';
import ChatInterface from '../components/ChatInterface';

const Dashboard = () => {
  const [agents, setAgents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [searchTerm, setSearchTerm] = useState('');
  const [activeChatAgent, setActiveChatAgent] = useState(null);

  useEffect(() => {
    fetchAgents();
  }, []);

  const fetchAgents = async () => {
    setLoading(true);
    try {
      const response = await fetch('http://localhost:8000/list_agents/');
      if (!response.ok) {
        throw new Error('Failed to fetch agents');
      }
      const data = await response.json();
      // Convert object to array
      const agentsArray = Object.values(data);
      setAgents(agentsArray);
    } catch (error) {
      console.error('Error fetching agents:', error);
      setError('Failed to load agents. Please try again later.');
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteAgent = async (agentName) => {
    if (window.confirm(`Are you sure you want to delete ${agentName}?`)) {
      try {
        const response = await fetch(`http://localhost:8000/delete_agent/${agentName}`, {
          method: 'DELETE',
        });
        
        if (!response.ok) {
          throw new Error('Failed to delete agent');
        }
        
        // Remove agent from state
        setAgents(agents.filter(agent => agent.name !== agentName));
      } catch (error) {
        console.error('Error deleting agent:', error);
        alert('Failed to delete agent. Please try again.');
      }
    }
  };

  const handleChatWithAgent = (agentName) => {
    setActiveChatAgent(agentName);
  };

  const closeChat = () => {
    setActiveChatAgent(null);
  };

  const filteredAgents = agents.filter(agent => 
    agent.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    agent.role.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="container mx-auto p-4">
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-800 mb-2">AI Agents Dashboard</h1>
        <p className="text-gray-600">Manage and interact with your AI agents</p>
      </div>
      
      <div className="mb-6">
        <input
          type="text"
          placeholder="Search agents by name or role..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="w-full p-3 border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
        />
      </div>
      
      {loading ? (
        <div className="flex justify-center items-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary"></div>
        </div>
      ) : error ? (
        <div className="bg-red-100 text-red-700 p-4 rounded-lg">
          {error}
        </div>
      ) : filteredAgents.length === 0 ? (
        <div className="text-center py-10">
          <p className="text-gray-500 text-xl">
            {searchTerm ? 'No agents match your search' : 'No agents found. Create your first agent!'}
          </p>
          <a 
            href="/create" 
            className="mt-4 inline-block bg-primary text-primary-foreground px-6 py-3 rounded-lg hover:bg-primary/90 transition"
          >
            Create Agent
          </a>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-6">
          {filteredAgents.map(agent => (
            <AgentCard 
              key={agent.name}
              agent={agent}
              onDelete={handleDeleteAgent}
              onChat={handleChatWithAgent}
            />
          ))}
        </div>
      )}
      
      {activeChatAgent && (
        <ChatInterface 
          agentName={activeChatAgent} 
          onClose={closeChat} 
        />
      )}
    </div>
  );
};

export default Dashboard; 