import React, { useState, useEffect, useRef } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { API_URL } from '../config';

const AgentProfile = () => {
  const { agentName } = useParams();
  const navigate = useNavigate();
  const [agent, setAgent] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [editMode, setEditMode] = useState(false);
  const [profilePicture, setProfilePicture] = useState(null);
  const [profilePictureURL, setProfilePictureURL] = useState('');
  const fileInputRef = useRef(null);
  
  // Form values state
  const [formValues, setFormValues] = useState({
    name: '',
    role: '',
    personality: '',
    tools: []
  });
  
  // Fetch available tools
  const [availableTools, setAvailableTools] = useState([]);
  
  useEffect(() => {
    const fetchTools = async () => {
      try {
        const response = await axios.get(`${API_URL}/available_tools/`);
        setAvailableTools(response.data);
      } catch (error) {
        console.error("Error fetching available tools:", error);
      }
    };
    
    fetchTools();
  }, []);
  
  // Fetch agent data
  useEffect(() => {
    const fetchAgentData = async () => {
      setLoading(true);
      try {
        const response = await axios.get(`${API_URL}/agent/${agentName}`);
        setAgent(response.data);
        
        // Initialize form values with the actual user inputs, not the generated system prompt
        setFormValues({
          name: response.data.name,
          role: response.data.role,
          personality: response.data.original_personality || response.data.personality,
          tools: response.data.tools || []
        });
        
        // Check if agent has a profile picture stored
        try {
          const profilePicResponse = await axios.get(`${API_URL}/agent/${agentName}/profile-picture`, { responseType: 'blob' });
          const imageUrl = URL.createObjectURL(profilePicResponse.data);
          setProfilePictureURL(imageUrl);
        } catch (picError) {
          // No profile picture, or error getting it
          console.log("No profile picture found or error:", picError);
        }
      } catch (error) {
        console.error("Error fetching agent:", error);
        setError('Failed to load agent information');
      } finally {
        setLoading(false);
      }
    };
    
    fetchAgentData();
  }, [agentName]);
  
  // Handle profile picture upload
  const handlePictureUpload = (e) => {
    const file = e.target.files[0];
    if (file) {
      setProfilePicture(file);
      setProfilePictureURL(URL.createObjectURL(file));
    }
  };
  
  // Trigger file input click
  const triggerFileUpload = () => {
    fileInputRef.current.click();
  };
  
  // Handle form input changes
  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormValues({
      ...formValues,
      [name]: value
    });
  };
  
  // Handle tool selection
  const handleToolToggle = (toolName) => {
    if (formValues.tools.includes(toolName)) {
      setFormValues({
        ...formValues,
        tools: formValues.tools.filter(t => t !== toolName)
      });
    } else {
      setFormValues({
        ...formValues,
        tools: [...formValues.tools, toolName]
      });
    }
  };
  
  // Save changes
  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(''); // Clear previous errors
    
    try {
      // Update agent details
      await axios.put(`${API_URL}/update_agent/${agent.name}`, {
        name: agent.name, // Include the required name field
        role: formValues.role,
        personality: formValues.personality,
        tools: formValues.tools,
      });
      
      // Upload profile picture if changed - do this separately
      if (profilePicture) {
        try {
          const formData = new FormData();
          formData.append('file', profilePicture);
          
          await axios.post(`${API_URL}/agent/${agent.name}/profile-picture`, formData, {
            headers: {
              'Content-Type': 'multipart/form-data'
            }
          });
        } catch (pictureError) {
          console.error("Error uploading profile picture:", pictureError);
          setError('Profile picture update failed, but agent details were saved. Please try again.');
          // Continue with the rest of the function since we don't want to fail the whole update
        }
      }
      
      // Exit edit mode and refresh data
      setEditMode(false);
      
      // Refetch the agent data to update the view
      try {
        const response = await axios.get(`${API_URL}/agent/${agentName}`);
        setAgent(response.data);
        
        // Update form values
        setFormValues({
          name: response.data.name,
          role: response.data.role,
          personality: response.data.original_personality || response.data.personality,
          tools: response.data.tools || []
        });
        
        // Try to reload the profile picture
        try {
          const profilePicResponse = await axios.get(`${API_URL}/agent/${agentName}/profile-picture`, { responseType: 'blob' });
          const imageUrl = URL.createObjectURL(profilePicResponse.data);
          setProfilePictureURL(imageUrl);
        } catch (picError) {
          // Silently fail if there's no profile picture
          console.log("No profile picture found or error:", picError);
          setProfilePictureURL('');
        }
      } catch (refreshError) {
        console.error("Error refreshing agent data:", refreshError);
        // We'll continue since the main update was successful
      }
      
    } catch (error) {
      console.error("Error updating agent:", error);
      if (error.response && error.response.status === 422) {
        setError('Invalid data format: Make sure all required fields are filled correctly.');
      } else {
        setError('Failed to update agent information: ' + (error.response?.data?.detail || error.message));
      }
      
      // Stay in edit mode if there was an error
      setEditMode(true);
    } finally {
      setLoading(false);
    }
  };
  
  // Cancel edit mode
  const handleCancel = () => {
    // Reset form values to current agent data
    setFormValues({
      name: agent.name,
      role: agent.role,
      personality: agent.original_personality || agent.personality,
      tools: agent.tools || []
    });
    
    // Reset profile picture URL
    if (profilePicture) {
      URL.revokeObjectURL(profilePictureURL);
      setProfilePicture(null);
      setProfilePictureURL('');
      
      // Try to reload the original profile picture
      if (agent.hasProfilePicture) {
        axios.get(`${API_URL}/agent/${agentName}/profile-picture`, { responseType: 'blob' })
          .then(response => {
            const imageUrl = URL.createObjectURL(response.data);
            setProfilePictureURL(imageUrl);
          })
          .catch(error => {
            console.log("Error reloading profile picture:", error);
          });
      }
    }
    
    // Exit edit mode
    setEditMode(false);
  };
  
  // Format system prompt for display
  const formatSystemPrompt = (text) => {
    // Split by headings (lines starting with #)
    const sections = text.split(/^(#.*)$/m);
    
    if (sections.length <= 1) {
      return text; // No headings found, return as is
    }
    
    // Format result with styling
    return sections.map((section, index) => {
      if (index === 0) {
        // Skip first empty section if it exists
        return section ? <p key={index} className="mb-4">{section}</p> : null;
      }
      
      if (section.startsWith('#')) {
        // This is a heading
        const level = section.match(/^#+/)[0].length;
        const title = section.replace(/^#+\s*/, '');
        
        if (level === 1) {
          return <h2 key={index} className="text-xl font-bold text-omnitrix mt-6 mb-2">{title}</h2>;
        } else {
          return <h3 key={index} className="text-lg font-bold text-omnitrix-light mt-4 mb-2">{title}</h3>;
        }
      } else {
        // This is content
        return (
          <div key={index} className="mb-4">
            {section.split('\n').map((line, i) => {
              if (line.trim() === '') return <br key={i} />;
              if (line.trim().startsWith('-')) {
                return <p key={i} className="ml-4 mb-1">• {line.replace(/^-\s*/, '')}</p>;
              }
              return <p key={i} className="mb-1">{line}</p>;
            })}
          </div>
        );
      }
    });
  };
  
  // Group tools by type
  const groupedTools = availableTools.reduce((acc, tool) => {
    const type = tool.type || 'function';
    if (!acc[type]) {
      acc[type] = [];
    }
    acc[type].push(tool);
    return acc;
  }, {});
  
  // Render tool type badge
  const renderToolTypeBadge = (type, name) => {
    // Check if this is a custom tool
    const isCustomTool = availableTools.some(tool => 
      tool.name === name && !['web_search_preview', 'file_search', 'code_interpreter'].includes(tool.type)
    );
    
    if (isCustomTool) {
      return <span className="ml-2 px-2 py-0.5 text-xs bg-blue-900 text-blue-300 rounded-full border border-blue-700">Custom Tool</span>;
    }
    
    switch (type) {
      case 'web_search_preview':
        return <span className="ml-2 px-2 py-0.5 text-xs bg-green-900 text-green-300 rounded-full border border-green-700">Web Search</span>;
      case 'file_search':
        return <span className="ml-2 px-2 py-0.5 text-xs bg-purple-900 text-purple-300 rounded-full border border-purple-700">File Search</span>;
      case 'code_interpreter':
        return <span className="ml-2 px-2 py-0.5 text-xs bg-yellow-900 text-yellow-300 rounded-full border border-yellow-700">Code Interpreter</span>;
      default:
        return <span className="ml-2 px-2 py-0.5 text-xs bg-dark-lighter text-gray-300 rounded-full border border-gray-700">Function</span>;
    }
  };
  
  // Loading state
  if (loading && !agent) {
    return (
      <div className="flex justify-center items-center min-h-[60vh]">
        <div className="w-12 h-12 border-t-4 border-omnitrix border-solid rounded-full animate-spin"></div>
      </div>
    );
  }
  
  // Error state
  if (error && !agent) {
    return (
      <div className="text-center p-8 bg-red-900 bg-opacity-30 border border-red-800 rounded-xl text-red-100">
        <svg xmlns="http://www.w3.org/2000/svg" className="h-12 w-12 mx-auto mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
        </svg>
        <p className="text-xl font-bold mb-2">Error</p>
        <p>{error}</p>
        <Link to="/" className="text-omnitrix hover:text-omnitrix-light mt-4 inline-block">
          Return to Home
        </Link>
      </div>
    );
  }
  
  return (
    <div className="container mx-auto p-4">
      {/* Back button */}
      <div className="mb-6">
        <Link 
          to="/" 
          className="text-gray-400 hover:text-white flex items-center"
        >
          <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2" viewBox="0 0 20 20" fill="currentColor">
            <path fillRule="evenodd" d="M9.707 16.707a1 1 0 01-1.414 0l-6-6a1 1 0 010-1.414l6-6a1 1 0 011.414 1.414L5.414 9H17a1 1 0 110 2H5.414l4.293 4.293a1 1 0 010 1.414z" clipRule="evenodd" />
          </svg>
          Back to Agents
        </Link>
      </div>
      
      {/* Agent Profile Container */}
      <div className="bg-ben10-black rounded-xl overflow-hidden border border-omnitrix-dark shadow-omnitrix">
        {/* Header Section */}
        <div className="bg-gradient-to-r from-omnitrix-dark to-omnitrix p-6">
          <div className="flex flex-col md:flex-row items-center">
            {/* Profile Picture */}
            <div className="relative mb-4 md:mb-0 md:mr-6">
              <input 
                type="file" 
                ref={fileInputRef} 
                onChange={handlePictureUpload} 
                className="hidden"
                accept="image/*"
              />
              <div 
                className="w-24 h-24 md:w-32 md:h-32 rounded-full bg-dark-lighter border-2 border-white flex items-center justify-center overflow-hidden group relative"
                onClick={editMode ? triggerFileUpload : undefined}
                style={{ cursor: editMode ? 'pointer' : 'default' }}
              >
                {profilePictureURL ? (
                  <img 
                    src={profilePictureURL} 
                    alt={`${agent.name}'s profile`}
                    className="w-full h-full object-cover"
                  />
                ) : (
                  <span className="text-4xl md:text-5xl font-bold text-white">
                    {agent?.name.charAt(0).toUpperCase()}
                  </span>
                )}
                
                {editMode && (
                  <div className="absolute inset-0 bg-black bg-opacity-70 flex items-center justify-center opacity-0 group-hover:opacity-100 transition">
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-8 w-8 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z" />
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 13a3 3 0 11-6 0 3 3 0 016 0z" />
                    </svg>
                  </div>
                )}
              </div>
              {editMode && (
                <p className="text-xs text-white text-center mt-2">Click to change</p>
              )}
            </div>
            
            {/* Agent Info */}
            <div className="flex-1 text-center md:text-left">
              <h1 className="text-3xl font-bold text-white mb-2">
                {agent.name}
              </h1>
              
              {!editMode ? (
                <div>
                  <p className="text-gray-200 text-lg mb-2">{agent.role}</p>
                  
                  {/* Tools Used */}
                  {agent.tools && agent.tools.length > 0 && (
                    <div className="flex flex-wrap gap-2 mt-2">
                      {agent.tools.map((tool, index) => {
                        const toolInfo = availableTools.find(t => t.name === tool) || {};
                        const toolType = toolInfo.type || 'function';
                        
                        return (
                          <span 
                            key={index} 
                            className="inline-flex items-center px-2 py-1 bg-dark-lighter bg-opacity-50 text-xs rounded-full border border-omnitrix-dark"
                          >
                            {tool}
                            {renderToolTypeBadge(toolType, tool)}
                          </span>
                        );
                      })}
                    </div>
                  )}
                </div>
              ) : (
                <div className="text-left">
                  <input
                    type="text"
                    name="role"
                    value={formValues.role}
                    onChange={handleChange}
                    className="w-full p-2 mb-2 bg-dark-lighter border border-gray-700 rounded text-white"
                    placeholder="Agent Role"
                  />
                </div>
              )}
              
              {/* Edit/Save Buttons */}
              <div className="mt-4 flex justify-center md:justify-start space-x-3">
                {!editMode ? (
                  <button
                    onClick={() => setEditMode(true)}
                    className="px-4 py-2 bg-omnitrix text-white rounded hover:bg-omnitrix-dark transition flex items-center"
                  >
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 mr-2" viewBox="0 0 20 20" fill="currentColor">
                      <path d="M13.586 3.586a2 2 0 112.828 2.828l-.793.793-2.828-2.828.793-.793zM11.379 5.793L3 14.172V17h2.828l8.38-8.379-2.83-2.828z" />
                    </svg>
                    Edit Profile
                  </button>
                ) : (
                  <>
                    <button
                      onClick={handleSubmit}
                      disabled={loading}
                      className="px-4 py-2 bg-omnitrix text-white rounded hover:bg-omnitrix-dark transition flex items-center"
                    >
                      {loading ? (
                        <div className="w-4 h-4 border-t-2 border-white border-solid rounded-full animate-spin mr-2"></div>
                      ) : (
                        <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 mr-2" viewBox="0 0 20 20" fill="currentColor">
                          <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                        </svg>
                      )}
                      Save
                    </button>
                    <button
                      onClick={handleCancel}
                      className="px-4 py-2 bg-dark-lighter text-white rounded hover:bg-dark transition flex items-center"
                    >
                      <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 mr-2" viewBox="0 0 20 20" fill="currentColor">
                        <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
                      </svg>
                      Cancel
                    </button>
                  </>
                )}
              </div>
            </div>
          </div>
        </div>
        
        {/* Profile Body */}
        <div className="p-6">
          {error && (
            <div className="mb-6 p-4 bg-red-900 bg-opacity-30 border border-red-800 rounded text-red-100">
              {error}
            </div>
          )}
          
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Left Column - Personality */}
            <div className="lg:col-span-1 order-2 lg:order-1">
              <div className="bg-dark-lighter p-4 rounded-lg border border-gray-800 mb-6">
                <h2 className="text-xl font-bold text-omnitrix mb-4 flex items-center">
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M10 9a3 3 0 100-6 3 3 0 000 6zm-7 9a7 7 0 1114 0H3z" clipRule="evenodd" />
                  </svg>
                  Personality & Expertise
                </h2>
                
                <div className="bg-dark p-3 rounded border border-omnitrix-dark text-xs text-gray-400 mb-4">
                  <p>
                    <span className="text-omnitrix">Note:</span> This is the personality description you provided when creating this agent. 
                    It determines how the agent behaves, its expertise, and its communication style.
                  </p>
                </div>
                
                {!editMode ? (
                  <div className="text-gray-300 prose prose-invert max-w-none">
                    {(agent.original_personality || agent.personality).split('\n').map((line, index) => (
                      <p key={index} className="mb-2">{line}</p>
                    ))}
                  </div>
                ) : (
                  <textarea
                    name="personality"
                    value={formValues.personality}
                    onChange={handleChange}
                    className="w-full p-3 bg-ben10-black border border-gray-700 rounded text-white h-64"
                    placeholder="Describe the agent's personality and expertise"
                  />
                )}
              </div>
              
              {/* Tools Section - Only shown in edit mode */}
              {editMode && (
                <div className="bg-dark-lighter p-4 rounded-lg border border-gray-800">
                  <h2 className="text-xl font-bold text-omnitrix mb-4 flex items-center">
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2" viewBox="0 0 20 20" fill="currentColor">
                      <path fillRule="evenodd" d="M5 2a1 1 0 011 1v1h1a1 1 0 010 2H6v1a1 1 0 01-2 0V6H3a1 1 0 010-2h1V3a1 1 0 011-1zm0 10a1 1 0 011 1v1h1a1 1 0 110 2H6v1a1 1 0 11-2 0v-1H3a1 1 0 110-2h1v-1a1 1 0 011-1zM12 2a1 1 0 01.967.744L14.146 7.2 17.5 9.134a1 1 0 010 1.732l-3.354 1.935-1.18 4.455a1 1 0 01-1.933 0L9.854 12.8 6.5 10.866a1 1 0 010-1.732l3.354-1.935 1.18-4.455A1 1 0 0112 2z" clipRule="evenodd" />
                    </svg>
                    Tools
                  </h2>
                  
                  <div className="space-y-4">
                    {Object.entries(groupedTools).map(([type, tools]) => (
                      <div key={type} className="border-b border-gray-700 pb-4 last:border-b-0 last:pb-0">
                        <h3 className="font-semibold mb-2 text-gray-400">
                          {type === 'web_search_preview' ? 'Web Search' : 
                           type === 'file_search' ? 'File Search' : 
                           type === 'code_interpreter' ? 'Code Interpreter' : 
                           'Functions'}
                        </h3>
                        <div className="space-y-2">
                          {tools.map(tool => (
                            <div key={tool.name} className="flex items-start">
                              <input
                                type="checkbox"
                                id={`tool-${tool.name}`}
                                checked={formValues.tools.includes(tool.name)}
                                onChange={() => handleToolToggle(tool.name)}
                                className="mt-1 h-4 w-4 text-omnitrix border-gray-300 rounded focus:ring-0 focus:ring-offset-0"
                              />
                              <label htmlFor={`tool-${tool.name}`} className="ml-2 block text-sm">
                                <span className="font-medium text-gray-300">{tool.name}</span>
                                {renderToolTypeBadge(type, tool.name)}
                                <p className="text-gray-500 text-xs mt-1">{tool.description || "No description available"}</p>
                              </label>
                            </div>
                          ))}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
            
            {/* Right Column - System Prompt */}
            <div className="lg:col-span-2 order-1 lg:order-2">
              <div className="bg-dark-lighter p-4 rounded-lg border border-gray-800">
                <h2 className="text-xl font-bold text-omnitrix mb-4 flex items-center">
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M2 5a2 2 0 012-2h12a2 2 0 012 2v10a2 2 0 01-2 2H4a2 2 0 01-2-2V5zm3.293 1.293a1 1 0 011.414 0l3 3a1 1 0 010 1.414l-3 3a1 1 0 01-1.414-1.414L7.586 10 5.293 7.707a1 1 0 010-1.414zM11 12a1 1 0 100 2h3a1 1 0 100-2h-3z" clipRule="evenodd" />
                  </svg>
                  Generated System Prompt
                  <span className="ml-2 text-xs text-gray-400 font-normal">(Read-only)</span>
                </h2>
                
                <div className="bg-dark p-3 rounded border border-omnitrix-dark text-xs text-gray-400 mb-4">
                  <p>
                    <span className="text-omnitrix">How this works:</span> The system automatically enhances your personality description with safety guardrails, 
                    role-specific guidelines, and structured formatting to create an effective system prompt. When you edit the personality description or role above, 
                    this system prompt is regenerated automatically.
                  </p>
                </div>
                
                <div className="bg-ben10-black border border-gray-800 rounded p-4 max-h-[600px] overflow-y-auto text-sm text-gray-300">
                  {formatSystemPrompt(agent.personality)}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      {/* Quick Actions Footer */}
      <div className="mt-6 flex flex-wrap gap-4 justify-center md:justify-start">
        <Link
          to={`/chat/${agent.name}`}
          className="px-6 py-3 bg-gradient-to-r from-omnitrix-dark to-omnitrix text-white rounded-lg shadow-omnitrix hover:shadow-omnitrix-pulse transition-all duration-300"
        >
          <span className="flex items-center">
            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M18 10c0 3.866-3.582 7-8 7a8.841 8.841 0 01-4.083-.98L2 17l1.338-3.123C2.493 12.767 2 11.434 2 10c0-3.866 3.582-7 8-7s8 3.134 8 7zM7 9H5v2h2V9zm8 0h-2v2h2V9zM9 9h2v2H9V9z" clipRule="evenodd" />
            </svg>
            Chat with {agent.name}
          </span>
        </Link>
        
        <Link
          to={`/agents/${agent.name}/history`}
          className="px-6 py-3 bg-dark-lighter text-white rounded-lg hover:bg-dark border border-gray-700 transition-all duration-300"
        >
          <span className="flex items-center">
            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.828 2.829a1 1 0 101.415-1.415L11 9.586V6z" clipRule="evenodd" />
            </svg>
            View Conversation History
          </span>
        </Link>
      </div>
    </div>
  );
};

export default AgentProfile; 