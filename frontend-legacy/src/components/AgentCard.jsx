import React from 'react';
import { Link } from 'react-router-dom';

const AgentCard = ({ agent, onDelete, onChat }) => {
  // Function to render a tool badge based on its name
  const getToolBadgeClass = (toolName) => {
    if (toolName === 'web_search_native') {
      return 'bg-green-100 text-green-800';
    } else if (toolName.includes('calculator')) {
      return 'bg-yellow-100 text-yellow-800';
    } else if (toolName.includes('weather')) {
      return 'bg-blue-100 text-blue-800';
    } else if (toolName.includes('calendar')) {
      return 'bg-purple-100 text-purple-800';
    } else if (toolName.includes('knowledge')) {
      return 'bg-indigo-100 text-indigo-800';
    } else {
      return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-6 mb-4">
      <div className="flex justify-between items-start">
        <div>
          <h2 className="text-xl font-bold text-gray-800">{agent.name}</h2>
          <p className="text-gray-600 mt-1">Role: {agent.role}</p>
          <p className="text-gray-600 mt-1">Personality: {agent.personality}</p>
          
          {agent.tools && agent.tools.length > 0 && (
            <div className="mt-3">
              <h3 className="font-semibold text-gray-700">Tools:</h3>
              <div className="flex flex-wrap gap-2 mt-1">
                {agent.tools.map((tool, index) => (
                  <span 
                    key={index} 
                    className={`inline-block text-xs px-2 py-1 rounded ${getToolBadgeClass(tool)}`}
                  >
                    {tool === 'web_search_native' ? 'Web Search (OpenAI)' : tool}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
        
        <div className="flex flex-col space-y-2">
          <button 
            onClick={() => onChat(agent.name)}
            className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600 transition"
          >
            Chat
          </button>
          <Link 
            to={`/agent/profile/${agent.name}`}
            className="bg-omnitrix text-white px-4 py-2 rounded hover:bg-omnitrix-dark transition text-center"
          >
            Profile
          </Link>
          <button 
            onClick={() => onDelete(agent.name)}
            className="bg-red-500 text-white px-4 py-2 rounded hover:bg-red-600 transition"
          >
            Delete
          </button>
        </div>
      </div>
    </div>
  );
};

export default AgentCard; 