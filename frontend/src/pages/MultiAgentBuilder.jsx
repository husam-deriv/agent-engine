import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { DndProvider, useDrag, useDrop } from 'react-dnd';
import { HTML5Backend } from 'react-dnd-html5-backend';

const API_URL = 'http://localhost:8000';

// DnD item types
const ItemTypes = {
  AGENT: 'agent',
};

// Draggable agent component
const DraggableAgent = ({ agent, isSelected, onClick }) => {
  const [{ isDragging }, drag] = useDrag(() => ({
    type: ItemTypes.AGENT,
    item: { agent },
    collect: (monitor) => ({
      isDragging: !!monitor.isDragging(),
    }),
  }));

  return (
    <div
      ref={drag}
      className={`p-4 mb-2 rounded-lg cursor-pointer transition-all duration-200 ${
        isDragging ? 'opacity-50' : 'opacity-100'
      } ${isSelected 
        ? 'bg-omnitrix bg-opacity-20 border-2 border-omnitrix shadow-omnitrix' 
        : 'bg-ben10-black border border-gray-700 hover:border-omnitrix-dark'}`}
      onClick={onClick}
      style={{ minHeight: '80px' }}
    >
      <div className="flex items-center">
        <div className="w-8 h-8 rounded-full bg-black flex items-center justify-center mr-3 border border-white">
          <span className="text-omnitrix font-mono font-bold text-xs">{agent.name.charAt(0)}</span>
        </div>
        <div>
          <h3 className="font-bold text-white">{agent.name}</h3>
          <p className="text-sm text-gray-400">{agent.role}</p>
        </div>
      </div>
    </div>
  );
};

// Dropzone for agents
const AgentDropZone = ({ onDrop, selectedAgents, onRemoveAgent, onSetTriageAgent, triageAgent }) => {
  const [{ isOver }, drop] = useDrop(() => ({
    accept: ItemTypes.AGENT,
    drop: (item) => onDrop(item.agent),
    collect: (monitor) => ({
      isOver: !!monitor.isOver(),
    }),
  }));

  return (
    <div
      ref={drop}
      className={`border-2 border-dashed rounded-lg p-4 min-h-[300px] ${
        isOver ? 'border-omnitrix bg-omnitrix bg-opacity-10' : 'border-gray-600'
      }`}
    >
      <h2 className="text-lg font-bold mb-4 text-white">Ultimate Agents</h2>
      {selectedAgents.length === 0 ? (
        <p className="text-gray-400 text-center py-10">
          Drag and drop Agents here to add them to your ultimate form
        </p>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {selectedAgents.map((agent) => (
            <div
              key={agent.name}
              className={`p-3 rounded-lg shadow-sm border ${
                triageAgent && triageAgent.name === agent.name
                  ? 'bg-omnitrix bg-opacity-20 border-omnitrix'
                  : 'bg-ben10-black border-gray-700'
              }`}
              onClick={() => onSetTriageAgent(agent)}
            >
              <div className="flex justify-between items-center">
                <div className="flex items-center">
                  <div className="w-8 h-8 rounded-full bg-black flex items-center justify-center mr-3 border border-white">
                    <span className="text-omnitrix font-mono font-bold text-xs">{agent.name.charAt(0)}</span>
                  </div>
                  <div>
                    <h3 className="font-bold text-white">{agent.name}</h3>
                    <p className="text-xs text-gray-400">{agent.role}</p>
                    {triageAgent && triageAgent.name === agent.name && (
                      <span className="text-xs bg-omnitrix text-black px-2 py-0.5 rounded-full mt-1 inline-block">
                        Primary Agent
                      </span>
                    )}
                  </div>
                </div>
                <button
                  className="text-red-500 hover:text-red-700 p-1"
                  onClick={(e) => {
                    e.stopPropagation();
                    onRemoveAgent(agent.name);
                  }}
                >
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
                  </svg>
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

// Connection visualization component 
const ConnectionVisualizer = ({ agents, connections, onAddConnection, onRemoveConnection, triageAgent }) => {
  const [sourceAgent, setSourceAgent] = useState('');
  const [targetAgent, setTargetAgent] = useState('');

  useEffect(() => {
    if (agents.length > 0) {
      setSourceAgent(agents[0].name);
      setTargetAgent(agents.length > 1 ? agents[1].name : agents[0].name);
    }
  }, [agents]);

  const handleAddConnection = () => {
    if (sourceAgent && targetAgent && sourceAgent !== targetAgent) {
      onAddConnection(sourceAgent, targetAgent);
    }
  };

  return (
    <div className="mt-6 border border-gray-700 rounded-lg p-4 bg-ben10-black">
      <h2 className="text-lg font-bold mb-4 text-white">Agent DNA Connections</h2>
      
      {agents.length < 2 ? (
        <p className="text-gray-400 text-center">Add at least two Agents to create DNA connections</p>
      ) : (
        <>
          <div className="mb-4">
            <label className="block mb-2 text-gray-300">Create New Connection</label>
            <div className="flex flex-col md:flex-row space-y-2 md:space-y-0 md:space-x-4">
              <select 
                className="form-select rounded-md border border-gray-700 bg-ben10-black text-white p-2 flex-1"
                value={sourceAgent}
                onChange={(e) => setSourceAgent(e.target.value)}
              >
                {agents.map(agent => (
                  <option key={`from-${agent.name}`} value={agent.name}>{agent.name}</option>
                ))}
              </select>
              <span className="flex items-center text-omnitrix">→</span>
              <select 
                className="form-select rounded-md border border-gray-700 bg-ben10-black text-white p-2 flex-1"
                value={targetAgent}
                onChange={(e) => setTargetAgent(e.target.value)}
              >
                {agents.map(agent => (
                  <option key={`to-${agent.name}`} value={agent.name}>{agent.name}</option>
                ))}
              </select>
              <button 
                className="bg-gradient-to-r from-omnitrix-dark to-omnitrix text-white px-4 py-2 rounded-md shadow-omnitrix hover:shadow-omnitrix-pulse transition-all duration-300"
                onClick={handleAddConnection}
                disabled={sourceAgent === targetAgent}
              >
                Connect
              </button>
            </div>
          </div>
          
          <div className="mt-4">
            <h3 className="font-semibold mb-2 text-gray-300">Current Connections</h3>
            {connections.length === 0 ? (
              <p className="text-gray-500">No connections defined yet</p>
            ) : (
              <ul className="divide-y divide-gray-700">
                {connections.map((conn, idx) => (
                  <li key={idx} className="py-2 flex justify-between items-center">
                    <span className="text-gray-300">
                      <span className="text-omnitrix">{conn.source_agent}</span> → <span className="text-ben10-alien">{conn.target_agent}</span>
                      {conn.description && <span className="text-sm text-gray-500 ml-2">({conn.description})</span>}
                    </span>
                    <button 
                      className="text-red-500 hover:text-red-700 p-1"
                      onClick={() => onRemoveConnection(idx)}
                    >
                      <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                        <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
                      </svg>
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </>
      )}
    </div>
  );
};

const MultiAgentBuilder = () => {
  const navigate = useNavigate();
  const [agents, setAgents] = useState([]);
  const [selectedAgents, setSelectedAgents] = useState([]);
  const [triageAgent, setTriageAgent] = useState(null);
  const [connections, setConnections] = useState([]);
  const [formData, setFormData] = useState({
    name: '',
    description: '',
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    // Fetch available agents
    const fetchAgents = async () => {
      try {
        setLoading(true);
        const response = await axios.get(`${API_URL}/list_agents/`);
        setAgents(Object.values(response.data));
        setLoading(false);
      } catch (err) {
        setError('Failed to fetch Agents');
        setLoading(false);
        console.error(err);
      }
    };

    fetchAgents();
  }, []);

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData({
      ...formData,
      [name]: value,
    });
  };

  const handleAgentSelect = (agent) => {
    if (selectedAgents.some((a) => a.name === agent.name)) {
      // Deselect agent
      setSelectedAgents(selectedAgents.filter((a) => a.name !== agent.name));
      // If this was the triage agent, reset triage agent
      if (triageAgent && triageAgent.name === agent.name) {
        setTriageAgent(null);
      }
    } else {
      // Select agent
      setSelectedAgents([...selectedAgents, agent]);
    }
  };

  const handleAgentDrop = (agent) => {
    if (!selectedAgents.some((a) => a.name === agent.name)) {
      setSelectedAgents([...selectedAgents, agent]);
    }
  };

  const handleSetTriageAgent = (agent) => {
    setTriageAgent(agent);
  };

  const handleRemoveAgent = (agentName) => {
    setSelectedAgents(selectedAgents.filter((a) => a.name !== agentName));
    // If this was the triage agent, reset triage agent
    if (triageAgent && triageAgent.name === agentName) {
      setTriageAgent(null);
    }
    // Remove any connections involving this agent
    setConnections(connections.filter(
      conn => conn.source_agent !== agentName && conn.target_agent !== agentName
    ));
  };

  const handleAddConnection = (sourceAgent, targetAgent, description = '') => {
    // Don't add duplicate connections
    if (connections.some(
      c => c.source_agent === sourceAgent && c.target_agent === targetAgent
    )) {
      return;
    }
    
    setConnections([
      ...connections,
      {
        source_agent: sourceAgent,
        target_agent: targetAgent,
        description,
      },
    ]);
  };

  const handleRemoveConnection = (index) => {
    setConnections(connections.filter((_, i) => i !== index));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (selectedAgents.length < 2) {
      setError('Please select at least two Agents for your ultimate form');
      return;
    }
    
    if (!triageAgent) {
      setError('Please designate a primary Agent');
      return;
    }
    
    try {
      const payload = {
        name: formData.name,
        description: formData.description,
        agents: selectedAgents.map(a => a.name),
        triage_agent: triageAgent.name,
        connections,
      };
      
      const response = await axios.post(`${API_URL}/multi_agent_systems/`, payload);
      
      // Redirect to the multi-agent system view page
      navigate(`/multi-agent/${response.data.id}`);
    } catch (err) {
      setError('Failed to create ultimate form');
      console.error(err);
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="relative w-16 h-16">
          <div className="absolute top-0 left-0 w-full h-full border-4 border-omnitrix border-t-transparent rounded-full animate-spin"></div>
          <div className="absolute top-2 left-2 w-12 h-12 border-4 border-ben10-alien border-b-transparent rounded-full animate-spin"></div>
        </div>
      </div>
    );
  }

  return (
    <DndProvider backend={HTML5Backend}>
      <div className="container mx-auto p-4">
        <div className="mb-8 relative">
        <div className="absolute -left-4 top-0 bottom-0 w-1 bg-gradient-to-b from-omnitrix to-omnitrix-dark rounded-full"></div>
          <h1 className="text-3xl font-bold bg-gradient-to-r from-omnitrix to-omnitrix-light bg-clip-text text-transparent mb-2">Create Ultimate Agent Form</h1>
          <p className="text-gray-400">Combine multiple Agents to create a powerful ultimate form</p>
        </div>
        
        {error && (
          <div className="bg-red-900 bg-opacity-20 border border-red-800 text-red-400 px-4 py-3 rounded-lg mb-4">
            {error}
          </div>
        )}
        
        <form onSubmit={handleSubmit}>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
            <div>
              <label className="block mb-2 font-semibold text-white">Ultimate Agent Name</label>
              <input
                type="text"
                name="name"
                value={formData.name}
                onChange={handleInputChange}
                className="w-full p-3 bg-ben10-black border border-gray-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-ben10-alien focus:border-transparent"
                placeholder="Enter a name for your ultimate agent"
                required
              />
            </div>
            
            <div>
              <label className="block mb-2 font-semibold text-white">Description</label>
              <input
                type="text"
                name="description"
                value={formData.description}
                onChange={handleInputChange}
                className="w-full p-3 bg-ben10-black border border-gray-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-ben10-alien focus:border-transparent"
                placeholder="Describe your ultimate agent's abilities"
                required
              />
            </div>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="col-span-1">
              <h2 className="text-lg font-bold mb-4 text-white">Available Agents</h2>
              <div className="overflow-y-auto max-h-[400px] border border-gray-700 rounded-lg p-4 bg-ben10-black">
                {agents.length === 0 ? (
                  <p className="text-gray-400">No Agents available. Create some first!</p>
                ) : (
                  agents.map((agent) => (
                    <DraggableAgent
                      key={agent.name}
                      agent={agent}
                      isSelected={selectedAgents.some((a) => a.name === agent.name)}
                      onClick={() => handleAgentSelect(agent)}
                    />
                  ))
                )}
              </div>
            </div>
            
            <div className="col-span-2">
              <AgentDropZone
                onDrop={handleAgentDrop}
                selectedAgents={selectedAgents}
                onRemoveAgent={handleRemoveAgent}
                onSetTriageAgent={handleSetTriageAgent}
                triageAgent={triageAgent}
              />
              
              {selectedAgents.length > 0 && (
                <div className="mt-6 border border-gray-700 rounded-lg p-4 bg-ben10-black">
                  <h2 className="text-lg font-bold mb-4 text-white">Select Primary Agent</h2>
                  <p className="mb-4 text-sm text-gray-400">
                    The primary agent will control the ultimate agent and coordinate with other agents.
                  </p>
                  
                  {!triageAgent && (
                    <div className="p-3 bg-ben10-alien bg-opacity-10 border border-ben10-alien rounded-lg mb-4 text-gray-300">
                      <div className="flex items-center">
                        <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2 text-ben10-alien" viewBox="0 0 20 20" fill="currentColor">
                          <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
                        </svg>
                        <span>Click on an agent above to designate it as the primary agent</span>
                      </div>
                    </div>
                  )}
                </div>
              )}
              
              <ConnectionVisualizer 
                agents={selectedAgents}
                connections={connections}
                onAddConnection={handleAddConnection}
                onRemoveConnection={handleRemoveConnection}
                triageAgent={triageAgent}
              />
            </div>
          </div>
          
          <div className="mt-8 flex justify-end">
            <button
              type="button"
              className="px-6 py-2 border border-gray-700 rounded-md text-gray-300 hover:bg-ben10-black transition-colors duration-200 mr-4"
              onClick={() => navigate('/')}
            >
              Cancel
            </button>
            <button
              type="submit"
              className={`px-6 py-2 rounded-md flex items-center ${
                selectedAgents.length < 2 || !triageAgent || !formData.name
                  ? 'bg-gray-700 cursor-not-allowed text-gray-400'
                  : 'bg-gradient-to-r from-ben10-alien to-ben10-blue hover:from-ben10-blue hover:to-ben10-alien text-white shadow-md'
              } transition-all duration-300`}
              disabled={selectedAgents.length < 2 || !triageAgent || !formData.name}
            >
              <span>Create Ultimate Agent</span>
              <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 ml-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
              </svg>
            </button>
          </div>
        </form>
      </div>
    </DndProvider>
  );
};

export default MultiAgentBuilder; 