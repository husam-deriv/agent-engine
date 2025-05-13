import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { API_URL } from '../config';

const CustomToolCreator = () => {
  const [description, setDescription] = useState('');
  const [installRequirements, setInstallRequirements] = useState(true);
  const [customTools, setCustomTools] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [showSecrets, setShowSecrets] = useState({});
  
  // Fetch custom tools on component mount
  useEffect(() => {
    fetchCustomTools();
  }, []);
  
  const fetchCustomTools = async () => {
    try {
      const response = await axios.get(`${API_URL}/custom_tools`);
      setCustomTools(response.data);
    } catch (error) {
      console.error('Error fetching custom tools:', error);
      setError('Failed to fetch custom tools');
    }
  };
  
  const handleCreateTool = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');
    setSuccess('');
    
    try {
      const response = await axios.post(`${API_URL}/custom_tools`, {
        description,
        install_requirements: installRequirements
      });
      
      if (response.data.success) {
        setSuccess(`Custom tool "${response.data.name}" created successfully!`);
        setDescription('');
        fetchCustomTools();
        
        // Check if there are secrets that need to be set
        if (response.data.secrets && response.data.secrets.length > 0) {
          setShowSecrets({
            ...showSecrets,
            [response.data.name]: true
          });
          setSuccess(`Tool created! Please set up the required API keys: ${response.data.secrets.join(', ')}`);
        }
      } else {
        setError(response.data.message);
      }
    } catch (error) {
      console.error('Error creating custom tool:', error);
      setError(error.response?.data?.detail || 'Failed to create custom tool');
    } finally {
      setIsLoading(false);
    }
  };
  
  const handleDeleteTool = async (toolName) => {
    if (!window.confirm(`Are you sure you want to delete the tool "${toolName}"?`)) {
      return;
    }
    
    try {
      await axios.delete(`${API_URL}/custom_tools/${toolName}`);
      setSuccess(`Custom tool "${toolName}" deleted successfully!`);
      fetchCustomTools();
    } catch (error) {
      console.error('Error deleting custom tool:', error);
      setError('Failed to delete custom tool');
    }
  };
  
  const handleInstallRequirements = async (toolName) => {
    try {
      const response = await axios.post(`${API_URL}/custom_tools/${toolName}/install`);
      if (response.data.status === 'success') {
        setSuccess(`Requirements for "${toolName}" installed successfully!`);
      } else {
        setError(`Failed to install requirements: ${response.data.message}`);
      }
    } catch (error) {
      console.error('Error installing requirements:', error);
      setError('Failed to install requirements');
    }
  };

  return (
    <div className="w-full max-w-4xl mx-auto p-6 bg-gray-800 rounded-lg shadow-lg">
      <h2 className="text-2xl font-bold mb-6 text-white">Custom Tool Creator</h2>
      
      {/* Error and success messages */}
      {error && (
        <div className="mb-4 p-3 bg-red-900 bg-opacity-50 border border-red-700 rounded text-red-300">
          {error}
        </div>
      )}
      {success && (
        <div className="mb-4 p-3 bg-green-900 bg-opacity-50 border border-green-700 rounded text-green-300">
          {success}
        </div>
      )}
      
      {/* Form for creating new tools */}
      <form onSubmit={handleCreateTool} className="mb-8">
        <div className="mb-4">
          <label className="block text-gray-300 mb-2">
            Tool Description (be specific about what the tool should do):
          </label>
          <textarea 
            className="w-full p-3 bg-gray-700 text-white rounded border border-gray-600 focus:border-blue-500 focus:outline-none"
            rows="4"
            placeholder="Create a tool that can fetch cryptocurrency prices from CoinGecko API..."
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            required
          />
        </div>
        
        <div className="mb-4 flex items-center">
          <input 
            type="checkbox" 
            id="installRequirements"
            className="mr-2"
            checked={installRequirements}
            onChange={(e) => setInstallRequirements(e.target.checked)}
          />
          <label htmlFor="installRequirements" className="text-gray-300">
            Automatically install required packages
          </label>
        </div>
        
        <button 
          type="submit" 
          className="py-2 px-4 bg-blue-600 hover:bg-blue-700 text-white rounded"
          disabled={isLoading}
        >
          {isLoading ? 'Creating...' : 'Create Custom Tool'}
        </button>
      </form>
      
      {/* List of existing tools */}
      <h3 className="text-xl font-semibold mb-4 text-white">Your Custom Tools</h3>
      
      {customTools.length === 0 ? (
        <p className="text-gray-400">No custom tools created yet.</p>
      ) : (
        <div className="space-y-4">
          {customTools.map((tool) => (
            <div key={tool.name} className="p-4 bg-gray-700 rounded border border-gray-600">
              <div className="flex justify-between items-start">
                <div>
                  <h4 className="text-lg font-medium text-white">{tool.name}</h4>
                  <p className="text-gray-300 mt-1">{tool.description}</p>
                </div>
                <div className="flex">
                  <button
                    onClick={() => handleInstallRequirements(tool.name)}
                    className="py-1 px-3 mr-2 bg-purple-600 hover:bg-purple-700 text-white text-sm rounded"
                  >
                    Install Requirements
                  </button>
                  <button
                    onClick={() => handleDeleteTool(tool.name)}
                    className="py-1 px-3 bg-red-600 hover:bg-red-700 text-white text-sm rounded"
                  >
                    Delete
                  </button>
                </div>
              </div>
              
              {/* Show button to view/manage secrets */}
              <div className="mt-2">
                <button
                  onClick={() => setShowSecrets({...showSecrets, [tool.name]: !showSecrets[tool.name]})}
                  className="text-blue-400 hover:text-blue-300 text-sm"
                >
                  {showSecrets[tool.name] ? 'Hide API Keys' : 'Manage API Keys'}
                </button>
                
                {showSecrets[tool.name] && (
                  <div className="mt-2 p-3 bg-gray-800 rounded">
                    <p className="text-gray-300 text-sm mb-2">
                      If this tool requires API keys, you should set them as environment variables:
                    </p>
                    <div className="bg-gray-900 p-2 rounded overflow-x-auto">
                      <code className="text-green-400 text-sm">
                        # Example commands to set environment variables:<br />
                        export TOOL_API_KEY=your-api-key-here
                      </code>
                    </div>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default CustomToolCreator; 