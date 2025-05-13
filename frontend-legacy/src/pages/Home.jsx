import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import axios from 'axios';

const API_URL = 'http://localhost:8000';

// Button component with Ben 10 design
const OmnitrixButton = ({ to, children, primary = false }) => {
  const baseClasses = "px-4 py-2 rounded-md font-medium inline-flex items-center justify-center transition-all duration-300 transform hover:-translate-y-0.5";
  const primaryClasses = "bg-gradient-to-r from-omnitrix-dark to-omnitrix text-white shadow-omnitrix hover:shadow-omnitrix-pulse";
  const secondaryClasses = "bg-gradient-to-r from-ben10-alien to-ben10-blue text-white shadow-md hover:shadow-neon-pink";
  
  return (
    <Link to={to} className={`${baseClasses} ${primary ? primaryClasses : secondaryClasses}`}>
      {children}
    </Link>
  );
};

// Agent card component with Ben 10 design
const AgentCard = ({ agent, onDelete }) => {
  const [slackStatus, setSlackStatus] = useState(null);
  const [isLoadingStatus, setIsLoadingStatus] = useState(false);
  const [actionInProgress, setActionInProgress] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  
  // Fetch Slack status when component mounts
  useEffect(() => {
    const fetchSlackStatus = async () => {
      setIsLoadingStatus(true);
      try {
        const response = await axios.get(`${API_URL}/agents/${agent.name}/slack/status`);
        setSlackStatus(response.data);
      } catch (error) {
        console.error('Error fetching Slack status:', error);
        // Don't show error UI, just assume it's not deployed
      } finally {
        setIsLoadingStatus(false);
      }
    };
    
    fetchSlackStatus();
  }, [agent.name]);
  
  // Toggle Slack bot status (start/stop)
  const toggleSlackBot = async (action) => {
    if (actionInProgress) return;
    
    setActionInProgress(true);
    try {
      const response = await axios.post(`${API_URL}/agents/${agent.name}/slack/toggle`, {
        action: action
      });
      
      // Update status
      setSlackStatus({
        deployed: true,
        status: response.data.status
      });
    } catch (error) {
      console.error(`Error ${action}ing Slack bot:`, error);
      // Could show an error toast here
    } finally {
      setActionInProgress(false);
    }
  };

  // Handle delete button click
  const handleDeleteClick = () => {
    setShowDeleteConfirm(true);
  };

  // Handle confirmation dialog close
  const handleDeleteCancel = () => {
    setShowDeleteConfirm(false);
  };

  // Handle actual deletion
  const handleDeleteConfirm = async () => {
    setActionInProgress(true);
    try {
      await axios.delete(`${API_URL}/delete_agent/${agent.name}`);
      onDelete(agent.name);
      setShowDeleteConfirm(false);
    } catch (error) {
      console.error(`Error deleting agent:`, error);
      alert(`Failed to delete agent: ${error.response?.data?.detail || error.message}`);
      setShowDeleteConfirm(false);
    } finally {
      setActionInProgress(false);
    }
  };

  return (
    <div className="bg-ben10-black rounded-xl overflow-hidden border border-omnitrix-dark shadow-lg hover:shadow-omnitrix transition-all duration-300 transform hover:-translate-y-1 flex flex-col h-full">
      <div className="bg-gradient-to-r from-omnitrix-dark to-omnitrix p-4">
        <div className="flex items-center justify-between">
          <Link to={`/agent/profile/${agent.name}`} className="flex items-center group cursor-pointer hover:opacity-90 transition-opacity">
            <div className="w-10 h-10 rounded-full bg-black flex items-center justify-center mr-3 shadow-inner border-2 border-white group-hover:border-omnitrix-light transition-colors">
              <span className="text-omnitrix font-mono font-bold">{agent.name.charAt(0)}</span>
            </div>
            <div>
              <h3 className="text-xl font-bold text-white group-hover:underline">{agent.name}</h3>
              <p className="text-sm text-omnitrix-glow">{agent.role}</p>
            </div>
          </Link>
          
          {/* Slack controls */}
          {slackStatus?.deployed && (
            <div className="flex items-center space-x-1">
              {slackStatus.status === 'running' ? (
                <button 
                  onClick={() => toggleSlackBot('stop')} 
                  className="bg-black bg-opacity-30 hover:bg-opacity-50 px-2 py-1 rounded text-xs text-yellow-400 border border-yellow-600 flex items-center transition-all duration-200"
                  disabled={actionInProgress}
                  title="Pause Slack bot"
                >
                  <svg className="w-3 h-3 mr-1" fill="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                    <rect x="6" y="4" width="4" height="16" rx="1" />
                    <rect x="14" y="4" width="4" height="16" rx="1" />
                  </svg>
                  {actionInProgress ? '...' : 'Pause'}
                </button>
              ) : (
                <button 
                  onClick={() => toggleSlackBot('start')} 
                  className="bg-black bg-opacity-30 hover:bg-opacity-50 px-2 py-1 rounded text-xs text-green-400 border border-green-600 flex items-center transition-all duration-200"
                  disabled={actionInProgress}
                  title="Start Slack bot"
                >
                  <svg className="w-3 h-3 mr-1" fill="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                    <path d="M8 5v14l11-7z" />
                  </svg>
                  {actionInProgress ? '...' : 'Play'}
                </button>
              )}
              <div 
                className="w-2 h-2 rounded-full ml-1"
                style={{ backgroundColor: slackStatus.status === 'running' ? '#4ade80' : '#fbbf24' }}
                title={slackStatus.status === 'running' ? 'Slack bot is running' : 'Slack bot is paused'}
              ></div>
            </div>
          )}
        </div>
      </div>
      
      <div className="p-4 flex-grow">
        <p className="text-gray-400 mb-4 text-sm line-clamp-3">
          {agent.personality.substring(0, 120)}
          {agent.personality.length > 120 ? '...' : ''}
        </p>
        
        {agent.tools && agent.tools.length > 0 && (
          <div className="mb-4">
            <p className="text-xs text-gray-500 mb-1">Tools:</p>
            <div className="flex flex-wrap gap-1">
              {agent.tools.map((tool) => (
                <span
                  key={tool}
                  className="bg-black text-omnitrix text-xs px-2 py-0.5 rounded-full border border-omnitrix"
                >
                  {tool}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>
      
      <div className="p-4 pt-0 mt-auto">
        <div className="flex justify-between items-center">
          <div className="flex items-center space-x-4">
            <Link
              to={`/chat/${agent.name}`}
              className="text-omnitrix hover:text-omnitrix-light flex items-center group"
            >
              <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-1" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M18 10c0 3.866-3.582 7-8 7a8.841 8.841 0 01-4.083-.98L2 17l1.338-3.123C2.493 12.767 2 11.434 2 10c0-3.866 3.582-7 8-7s8 3.134 8 7zM7 9H5v2h2V9zm8 0h-2v2h2V9zM9 9h2v2H9V9z" clipRule="evenodd" />
              </svg>
              <span>Chat</span>
            </Link>
            <Link
              to={`/agents/${agent.name}/history`}
              className="text-gray-500 hover:text-gray-300 flex items-center"
            >
              <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-1" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.828 2.829a1 1 0 101.415-1.415L11 9.586V6z" clipRule="evenodd" />
              </svg>
              <span>History</span>
            </Link>
          </div>
          <button
            onClick={handleDeleteClick}
            className="text-red-500 hover:text-red-400 transition-colors"
            title="Delete agent"
          >
            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
            </svg>
          </button>
        </div>
      </div>

      {/* Delete confirmation dialog */}
      {showDeleteConfirm && (
        <div className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50">
          <div className="bg-ben10-black rounded-lg border border-red-800 p-6 max-w-md w-full mx-4">
            <h3 className="text-xl font-bold text-white mb-2">Delete Agent</h3>
            <p className="text-gray-300 mb-6">
              Are you sure you want to delete <span className="text-omnitrix font-semibold">{agent.name}</span>? 
              This action cannot be undone.
            </p>
            <div className="flex justify-end space-x-3">
              <button
                onClick={handleDeleteCancel}
                className="px-4 py-2 bg-gray-800 hover:bg-gray-700 text-white rounded"
                disabled={actionInProgress}
              >
                Cancel
              </button>
              <button
                onClick={handleDeleteConfirm}
                className="px-4 py-2 bg-red-700 hover:bg-red-600 text-white rounded flex items-center"
                disabled={actionInProgress}
              >
                {actionInProgress ? (
                  <>
                    <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    Deleting...
                  </>
                ) : (
                  <>Delete</>
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

// Multi-agent system card component with Ben 10 design
const MultiAgentSystemCard = ({ system }) => {
  return (
    <div className="bg-ben10-black rounded-xl overflow-hidden border border-ben10-alien shadow-lg hover:shadow-ben10-alien transition-all duration-300 transform hover:-translate-y-1 flex flex-col h-full">
      <div className="bg-gradient-to-r from-ben10-alien to-ben10-blue p-4">
        <div className="flex items-center">
          <Link to={`/multi-agent/${system.id}`} className="flex items-center group cursor-pointer hover:opacity-90 transition-opacity">
            <div className="w-10 h-10 rounded-full bg-black flex items-center justify-center mr-3 shadow-inner border-2 border-white group-hover:border-ben10-alien transition-colors">
              <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 text-ben10-alien" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
            </div>
            <div>
              <h3 className="text-xl font-bold text-white group-hover:underline">{system.name}</h3>
              <p className="text-sm text-indigo-200">{system.agents.length} agents</p>
            </div>
          </Link>
        </div>
      </div>
      
      <div className="p-4 flex-grow">
        <p className="text-gray-400 mb-4 text-sm line-clamp-3">
          {system.description.substring(0, 120)}
          {system.description.length > 120 ? '...' : ''}
        </p>
        
        <div className="mb-4">
          <p className="text-xs text-gray-500 mb-1">Agents:</p>
          <div className="flex flex-wrap gap-1">
            {system.agents.map((agentName) => (
              <span
                key={agentName}
                className={`text-xs px-2 py-0.5 rounded-full ${
                  agentName === system.triage_agent
                    ? 'bg-ben10-alien text-white border border-indigo-700'
                    : 'bg-black text-gray-300 border border-gray-700'
                }`}
              >
                {agentName} {agentName === system.triage_agent && '(Triage)'}
              </span>
            ))}
          </div>
        </div>
      </div>
      
      <div className="p-4 pt-0 mt-auto">
        <Link
          to={`/multi-agent/${system.id}`}
          className="text-ben10-alien hover:text-indigo-300 flex items-center group"
        >
          <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-1" viewBox="0 0 20 20" fill="currentColor">
            <path fillRule="evenodd" d="M18 10c0 3.866-3.582 7-8 7a8.841 8.841 0 01-4.083-.98L2 17l1.338-3.123C2.493 12.767 2 11.434 2 10c0-3.866 3.582-7 8-7s8 3.134 8 7zM7 9H5v2h2V9zm8 0h-2v2h2V9zM9 9h2v2H9V9z" clipRule="evenodd" />
          </svg>
          <span>Open Chat</span>
        </Link>
      </div>
    </div>
  );
};

const Home = () => {
  const [agents, setAgents] = useState({});
  const [multiAgentSystems, setMultiAgentSystems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  useEffect(() => {
    const fetchData = async () => {
      try {
        // Fetch agents
        const agentsResponse = await axios.get(`${API_URL}/list_agents/`);
        setAgents(agentsResponse.data);
        
        // Fetch multi-agent systems
        const systemsResponse = await axios.get(`${API_URL}/multi_agent_systems/`);
        setMultiAgentSystems(systemsResponse.data);
        
        setLoading(false);
      } catch (err) {
        console.error('Error fetching data:', err);
        setError('Failed to fetch data. Please try again later.');
        setLoading(false);
      }
    };
    
    fetchData();
  }, []);
  
  // Handle agent deletion
  const handleAgentDelete = (agentName) => {
    // Create a new object without the deleted agent
    const updatedAgents = { ...agents };
    delete updatedAgents[agentName];
    setAgents(updatedAgents);
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
  
  if (error) {
    return (
      <div className="text-center p-8 text-red-500 bg-dark-lighter rounded-lg border border-red-800">
        <svg xmlns="http://www.w3.org/2000/svg" className="h-12 w-12 mx-auto mb-4 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
        </svg>
        <p>{error}</p>
      </div>
    );
  }
  
  const agentList = Object.values(agents);
  
  return (
    <div>
      <div className="mb-12">
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 mb-8">
          <div>
            <h1 className="text-3xl font-bold bg-gradient-to-r from-omnitrix to-omnitrix-light bg-clip-text text-transparent">
              Omnitrix Framework
            </h1>
            <p className="text-gray-400 mt-2">
              Create, manage, and interact with intelligent agents
            </p>
          </div>
          <div className="flex gap-3">
            <OmnitrixButton to="/create-agent" primary>
              <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
              </svg>
              New Agent
            </OmnitrixButton>
            <OmnitrixButton to="/multi-agent/create">
              <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
              </svg>
              Ultimate Agent
            </OmnitrixButton>
          </div>
        </div>
      </div>
      
      {/* Individual Agents Section */}
      <section className="mb-12">
        <div className="flex items-center mb-6">
          <div className="w-1 h-6 bg-omnitrix mr-3 rounded-full"></div>
          <h2 className="text-2xl font-semibold text-white">Your Agents</h2>
        </div>
        
        {agentList.length === 0 ? (
          <div className="bg-ben10-black rounded-xl p-8 text-center border border-omnitrix-dark">
            <div className="w-20 h-20 mx-auto mb-4 rounded-full bg-omnitrix flex items-center justify-center shadow-omnitrix border-4 border-white relative">
              <div className="absolute inset-2 rounded-full bg-black opacity-70"></div>
              <span className="relative z-10 font-mono text-white text-xl">10</span>
            </div>
            <p className="text-gray-400 mb-4">You don't have any agents yet.</p>
            <div className="inline-block">
              <OmnitrixButton to="/create-agent" primary>
                <span>Create Your First Agent</span>
              </OmnitrixButton>
            </div>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {agentList.map((agent) => (
              <div className="h-full" key={agent.name}>
                <AgentCard agent={agent} onDelete={(name) => handleAgentDelete(name)} />
              </div>
            ))}
          </div>
        )}
      </section>
      
      {/* Multi-Agent Systems Section */}
      <section>
        <div className="flex items-center mb-6">
          <div className="w-1 h-6 bg-ben10-alien mr-3 rounded-full"></div>
          <h2 className="text-2xl font-semibold text-white">Ultimate Agents</h2>
        </div>
        
        {multiAgentSystems.length === 0 ? (
          <div className="bg-ben10-black rounded-xl p-8 text-center border border-ben10-alien">
            <div className="w-20 h-20 mx-auto mb-4 rounded-full bg-ben10-alien flex items-center justify-center shadow-md border-4 border-white relative">
              <div className="absolute inset-2 rounded-full bg-black opacity-70"></div>
              <svg xmlns="http://www.w3.org/2000/svg" className="relative z-10 h-10 w-10 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
            </div>
            <p className="text-gray-400 mb-4">You don't have any ultimate agents yet.</p>
            {agentList.length < 2 ? (
              <p className="text-sm text-gray-500">
                Create at least two agents to build an ultimate agent.
              </p>
            ) : (
              <div className="inline-block">
                <OmnitrixButton to="/multi-agent/create">
                  <span>Create Your First Ultimate Agent</span>
                </OmnitrixButton>
              </div>
            )}
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {multiAgentSystems.map((system) => (
              <div className="h-full" key={system.id}>
                <MultiAgentSystemCard system={system} />
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  );
};

export default Home; 