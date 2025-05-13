import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import axios from 'axios';

const API_URL = 'http://localhost:8000';

// AI Solution card component
const SolutionCard = ({ agent, onDelete }) => {
  const [isExpanded, setIsExpanded] = useState(false);
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
    <div className="bg-white rounded-lg border border-gray-200 shadow-sm hover:shadow-md transition-shadow">
      <div className="p-5">
        <div className="flex justify-between items-start mb-3">
          <div className="flex items-center">
            <div className="w-10 h-10 rounded-md bg-gargash flex items-center justify-center text-white shadow-sm mr-3">
              <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z" />
              </svg>
            </div>
            <div>
              <h3 className="text-lg font-semibold text-gray-900">{agent.name}</h3>
              <p className="text-sm text-gray-500">{agent.role}</p>
            </div>
          </div>

          <div className="flex items-center space-x-2">
            {slackStatus?.deployed && (
              <div className="flex items-center mr-2">
                <div 
                  className={`w-2 h-2 rounded-full ${slackStatus.status === 'running' ? 'bg-success' : 'bg-warning'}`}
                ></div>
                <span className="ml-1 text-xs text-gray-500">
                  {slackStatus.status === 'running' ? 'Active' : 'Paused'}
                </span>
              </div>
            )}

            <button
              onClick={() => setIsExpanded(!isExpanded)}
              className="text-gray-400 hover:text-gargash"
            >
              <svg xmlns="http://www.w3.org/2000/svg" className={`h-5 w-5 transform transition-transform ${isExpanded ? 'rotate-180' : ''}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
              </svg>
            </button>
            
            <button 
              onClick={handleDeleteClick}
              className="text-gray-400 hover:text-danger" 
              title="Delete solution"
            >
              <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
              </svg>
            </button>
          </div>
        </div>

        {/* Basic info always visible */}
        <p className="text-gray-600 mb-4 text-sm">
          {agent.personality?.substring(0, isExpanded ? undefined : 150)}
          {!isExpanded && agent.personality?.length > 150 && '...'}
        </p>

        {/* Additional details when expanded */}
        {isExpanded && (
          <div className="mt-4 border-t border-gray-100 pt-4">
            {agent.tools && agent.tools.length > 0 && (
              <div className="mb-4">
                <p className="text-sm font-medium text-gray-700 mb-2">Capabilities:</p>
                <div className="flex flex-wrap gap-1">
                  {agent.tools.map((tool) => (
                    <span
                      key={tool}
                      className="bg-gray-100 text-gray-800 text-xs px-2 py-0.5 rounded"
                    >
                      {tool}
                    </span>
                  ))}
                </div>
              </div>
            )}
            
            <div className="flex space-x-2 mt-4">
              <Link
                to={`/chat/${agent.name}`}
                className="text-white bg-gargash hover:bg-gargash-dark px-3 py-1.5 rounded text-sm flex items-center"
              >
                <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 mr-1" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M18 10c0 3.866-3.582 7-8 7a8.841 8.841 0 01-4.083-.98L2 17l1.338-3.123C2.493 12.767 2 11.434 2 10c0-3.866 3.582-7 8-7s8 3.134 8 7zM7 9H5v2h2V9zm8 0h-2v2h2V9zM9 9h2v2H9V9z" clipRule="evenodd" />
                </svg>
                Chat
              </Link>
              
              <Link
                to={`/agents/${agent.name}/history`}
                className="text-gray-700 bg-gray-100 hover:bg-gray-200 px-3 py-1.5 rounded text-sm flex items-center"
              >
                <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 mr-1" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.828 2.829a1 1 0 101.415-1.415L11 9.586V6z" clipRule="evenodd" />
                </svg>
                History
              </Link>
              
              {slackStatus?.deployed && (
                <button
                  onClick={() => toggleSlackBot(slackStatus.status === 'running' ? 'stop' : 'start')}
                  className={`${
                    slackStatus.status === 'running'
                      ? 'text-warning bg-warning-100 hover:bg-warning-200'
                      : 'text-success bg-success-100 hover:bg-success-200'
                  } px-3 py-1.5 rounded text-sm flex items-center`}
                  disabled={actionInProgress}
                >
                  {slackStatus.status === 'running' ? (
                    <>
                      <svg className="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20" xmlns="http://www.w3.org/2000/svg">
                        <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zM7 8a1 1 0 012 0v4a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v4a1 1 0 102 0V8a1 1 0 00-1-1z" clipRule="evenodd" />
                      </svg>
                      Pause
                    </>
                  ) : (
                    <>
                      <svg className="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20" xmlns="http://www.w3.org/2000/svg">
                        <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM9.555 7.168A1 1 0 008 8v4a1 1 0 001.555.832l3-2a1 1 0 000-1.664l-3-2z" clipRule="evenodd" />
                      </svg>
                      Activate
                    </>
                  )}
                </button>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Delete confirmation dialog */}
      {showDeleteConfirm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
            <h3 className="text-xl font-bold text-gray-900 mb-2">Delete AI Solution</h3>
            <p className="text-gray-600 mb-6">
              Are you sure you want to delete <span className="text-gargash font-semibold">{agent.name}</span>? 
              This action cannot be undone.
            </p>
            <div className="flex justify-end space-x-3">
              <button
                onClick={handleDeleteCancel}
                className="px-4 py-2 bg-gray-100 hover:bg-gray-200 text-gray-800 rounded"
                disabled={actionInProgress}
              >
                Cancel
              </button>
              <button
                onClick={handleDeleteConfirm}
                className="px-4 py-2 bg-danger hover:bg-danger-dark text-white rounded flex items-center"
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
                  'Delete'
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

const AISolutions = () => {
  const [agents, setAgents] = useState({});
  const [multiAgentSystems, setMultiAgentSystems] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('All');
  const [error, setError] = useState(null);

  // Generate categories based on agent roles
  const getCategories = () => {
    const roles = Object.values(agents).map(agent => agent.role);
    const uniqueRoles = ['All', ...new Set(roles)];
    return uniqueRoles;
  };

  // Filter agents based on search and category
  const filteredAgents = Object.values(agents).filter(agent => {
    const matchesSearch = 
      searchQuery === '' || 
      agent.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      agent.role?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      agent.personality?.toLowerCase().includes(searchQuery.toLowerCase());
    
    const matchesCategory = 
      selectedCategory === 'All' || 
      agent.role === selectedCategory;
    
    return matchesSearch && matchesCategory;
  });

  useEffect(() => {
    const fetchData = async () => {
      setIsLoading(true);
      try {
        // Fetch agents
        const agentsResponse = await axios.get(`${API_URL}/list_agents`);
        setAgents(agentsResponse.data);
        
        // Fetch multi-agent systems
        try {
          const multiAgentResponse = await axios.get(`${API_URL}/multi_agent_systems`);
          setMultiAgentSystems(multiAgentResponse.data);
        } catch (multiAgentErr) {
          console.error('Error fetching multi-agent systems:', multiAgentErr);
          // Set to empty array but don't show error (non-critical)
          setMultiAgentSystems([]);
        }
        
        setError(null);
      } catch (err) {
        console.error('Error fetching data:', err);
        setError('Failed to load AI solutions. Please try again later.');
      } finally {
        setIsLoading(false);
      }
    };

    fetchData();
  }, []);

  const handleAgentDelete = (agentName) => {
    setAgents(prevAgents => {
      const newAgents = { ...prevAgents };
      delete newAgents[agentName];
      return newAgents;
    });
  };

  if (isLoading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-gargash"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded relative" role="alert">
        <strong className="font-bold">Error:</strong>
        <span className="block sm:inline"> {error}</span>
      </div>
    );
  }

  return (
    <div className="container mx-auto py-6 px-4">
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-2xl font-bold text-gray-900">AI Solutions</h1>
        <Link 
          to="/create-agent" 
          className="bg-gargash hover:bg-gargash-dark text-white py-2 px-4 rounded-md flex items-center transition-colors duration-200"
        >
          <svg className="w-5 h-5 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6"></path>
          </svg>
          Create Solution
        </Link>
      </div>

      <div className="bg-white p-4 rounded-lg border border-gray-200 mb-6">
        <div className="flex flex-col md:flex-row space-y-3 md:space-y-0 md:space-x-4">
          <div className="flex-1">
            <label htmlFor="search" className="block text-sm font-medium text-gray-700 mb-1">Search</label>
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <svg className="h-5 w-5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
              </div>
              <input
                type="text"
                id="search"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-10 w-full rounded-md border border-gray-300 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-gargash focus:border-gargash"
                placeholder="Search by name, role, or description..."
              />
            </div>
          </div>

          <div>
            <label htmlFor="category" className="block text-sm font-medium text-gray-700 mb-1">Category</label>
            <select
              id="category"
              value={selectedCategory}
              onChange={(e) => setSelectedCategory(e.target.value)}
              className="w-full rounded-md border border-gray-300 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-gargash focus:border-gargash"
            >
              {getCategories().map(category => (
                <option key={category} value={category}>{category}</option>
              ))}
            </select>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {filteredAgents.map(agent => (
          <SolutionCard 
            key={agent.name} 
            agent={agent} 
            onDelete={handleAgentDelete} 
          />
        ))}
      </div>

      {filteredAgents.length === 0 && (
        <div className="text-center py-12">
          <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          <h3 className="mt-2 text-lg font-medium text-gray-900">No AI solutions found</h3>
          <p className="mt-1 text-gray-500">Try adjusting your search or create a new solution.</p>
        </div>
      )}
    </div>
  );
};

export default AISolutions; 