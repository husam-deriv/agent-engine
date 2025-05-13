import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { API_URL } from '../config';

// Example prompts for different agent types
const EXAMPLE_PROMPTS = {
  customerSupport: {
    role: "Customer Support Specialist",
    personality: "I am a friendly and patient customer support specialist with expertise in technical troubleshooting. I communicate clearly, show empathy towards customer frustrations, and always follow up to ensure issues are resolved. I maintain a professional tone while being approachable and understanding."
  },
  developer: {
    role: "Software Developer",
    personality: "I am a detail-oriented software developer with expertise in multiple programming languages. I write clean, efficient code and provide thorough explanations of technical concepts. I'm analytical, methodical, and focused on creating robust solutions while following best practices for security and performance."
  },
  tutor: {
    role: "Educational Tutor",
    personality: "I am a supportive and encouraging educational tutor who adapts my teaching style to different learning needs. I break down complex concepts into understandable parts, use relevant examples, and ask guiding questions to promote critical thinking. I'm patient, positive, and committed to helping students achieve their learning goals."
  },
  dataAnalyst: {
    role: "Data Analyst",
    personality: "I am a methodical data analyst with strong analytical skills and attention to detail. I communicate insights clearly using visualizations and plain language. I'm objective, thorough, and focused on extracting meaningful patterns from data to support informed decision-making."
  },
  contentWriter: {
    role: "Content Writer",
    personality: "I am a creative content writer with a strong command of language and storytelling. I adapt my writing style to different audiences and purposes while maintaining clarity and engagement. I'm imaginative, detail-oriented, and skilled at crafting compelling narratives that resonate with readers."
  }
};

const AgentForm = ({ onSubmit, onCancel }) => {
  const [formData, setFormData] = useState({
    name: '',
    role: '',
    personality: '',
    tools: [],
  });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [availableTools, setAvailableTools] = useState([]);
  const [isLoadingTools, setIsLoadingTools] = useState(false);
  const [showExamples, setShowExamples] = useState(false);
  const [showToolCreator, setShowToolCreator] = useState(false);
  const [customToolDescription, setCustomToolDescription] = useState('');
  const [isCreatingTool, setIsCreatingTool] = useState(false);
  const [customToolSecrets, setCustomToolSecrets] = useState({});
  const [showSecretForm, setShowSecretForm] = useState(false);
  const [currentTool, setCurrentTool] = useState(null);

  // Fetch available tools when component mounts
  useEffect(() => {
    fetchTools();
  }, []);

  const fetchTools = async () => {
    setIsLoadingTools(true);
    try {
      const response = await axios.get(`${API_URL}/available_tools`);
      setAvailableTools(response.data);
    } catch (error) {
      console.error('Error fetching tools:', error);
      setError('Failed to load available tools. Please try again later.');
    } finally {
      setIsLoadingTools(false);
    }
  };

  // Add a function to create a custom tool
  const handleCreateCustomTool = async () => {
    if (!customToolDescription.trim()) {
      setError('Please provide a description for your custom tool');
      return;
    }

    setIsCreatingTool(true);
    setError('');
    setSuccess('');

    try {
      const response = await axios.post(`${API_URL}/custom_tools`, {
        description: customToolDescription,
        install_requirements: true
      });

      if (response.data.success) {
        setSuccess(`Custom tool "${response.data.name}" created successfully!`);
        setCustomToolDescription('');
        
        // If the tool requires secrets/API keys
        if (response.data.secrets && response.data.secrets.length > 0) {
          setCurrentTool({
            name: response.data.name,
            secrets: response.data.secrets
          });
          setShowSecretForm(true);
        }
        
        // Add the tool to selected tools
        if (!formData.tools.includes(response.data.name)) {
          setFormData({
            ...formData,
            tools: [...formData.tools, response.data.name]
          });
        }
        
        // Refresh tool list
        fetchTools();
      } else {
        setError(response.data.message || 'Failed to create tool');
      }
    } catch (error) {
      console.error('Error creating custom tool:', error);
      setError(error.response?.data?.detail || 'Failed to create custom tool');
    } finally {
      setIsCreatingTool(false);
      setShowToolCreator(false);
    }
  };

  // Handle saving API keys/secrets
  const handleSaveSecrets = async () => {
    if (!currentTool) return;
    
    setIsSubmitting(true);
    setError('');
    
    try {
      const response = await axios.post(
        `${API_URL}/custom_tools/${currentTool.name}/secrets`,
        { secrets: customToolSecrets }
      );
      
      if (response.data.success) {
        setSuccess(`API keys for ${currentTool.name} saved! The tool is ready to use.`);
      } else {
        setError(response.data.message || 'Failed to save API keys');
      }
    } catch (error) {
      console.error('Error saving API keys:', error);
      setError(error.response?.data?.detail || 'Failed to save API keys');
    } finally {
      setIsSubmitting(false);
      setShowSecretForm(false);
      setCurrentTool(null);
    }
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData({ ...formData, [name]: value });
  };

  const handleToolSelection = (toolName) => {
    // Toggle tool selection
    if (formData.tools.includes(toolName)) {
      setFormData({
        ...formData,
        tools: formData.tools.filter(name => name !== toolName)
      });
    } else {
      setFormData({
        ...formData,
        tools: [...formData.tools, toolName]
      });
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsSubmitting(true);
    setError('');

    // Validate form
    if (!formData.name || !formData.role || !formData.personality) {
      setError('Please fill in all required fields');
      setIsSubmitting(false);
      return;
    }
    
    try {
      await onSubmit(formData);
    } catch (error) {
      setError(error.message || 'An error occurred while creating the agent');
    } finally {
      setIsSubmitting(false);
    }
  };

  const applyExample = (exampleKey) => {
    const example = EXAMPLE_PROMPTS[exampleKey];
    setFormData({
      ...formData,
      role: example.role,
      personality: example.personality
    });
    setShowExamples(false);
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

  // Update renderToolTypeBadge to include custom tools
  const renderToolTypeBadge = (type, name) => {
    // Check if this is a custom tool by checking if it's in the custom tools list
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

  // Tooltip component
  const Tooltip = ({ children, text }) => {
    const [isVisible, setIsVisible] = useState(false);
    
    return (
      <div className="relative inline-block">
        <div 
          className="flex items-center cursor-help"
          onMouseEnter={() => setIsVisible(true)}
          onMouseLeave={() => setIsVisible(false)}
        >
          {children}
          <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 ml-1 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        </div>
        {isVisible && (
          <div className="absolute z-10 w-64 p-2 mt-2 text-sm text-white bg-gray-800 rounded-md shadow-lg">
            {text}
          </div>
        )}
      </div>
    );
  };

  return (
    <div>
      {error && (
        <div className="bg-red-900 bg-opacity-20 border border-red-800 text-red-400 p-4 mb-6 rounded-lg">
          {error}
        </div>
      )}
      
      <div className="mb-6 p-4 bg-omnitrix bg-opacity-10 border border-omnitrix-dark rounded-lg">
        <h3 className="text-white font-semibold mb-2 flex items-center">
          <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2 text-omnitrix" viewBox="0 0 20 20" fill="currentColor">
            <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
          </svg>
          Agent Creation Guide
        </h3>
        <p className="text-gray-300 text-sm mb-2">
          Create a specialized agent by defining its name, role, and personality. The more specific and detailed your descriptions, the better your agent will perform.
        </p>
        <div className="flex justify-between items-center">
          <button
            type="button"
            onClick={() => setShowExamples(!showExamples)}
            className="text-omnitrix hover:text-omnitrix-light text-sm flex items-center"
          >
            {showExamples ? 'Hide Examples' : 'Show Examples'}
            <svg xmlns="http://www.w3.org/2000/svg" className={`h-4 w-4 ml-1 transition-transform ${showExamples ? 'rotate-180' : ''}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </button>
        </div>
        
        {showExamples && (
          <div className="mt-3 grid grid-cols-1 md:grid-cols-2 gap-3">
            <button
              type="button"
              onClick={() => applyExample('customerSupport')}
              className="text-left p-3 bg-ben10-black border border-gray-700 rounded-lg hover:border-omnitrix transition-all"
            >
              <h4 className="font-medium text-white">Customer Support Agent</h4>
              <p className="text-xs text-gray-400 mt-1 line-clamp-2">Friendly, patient specialist with technical troubleshooting expertise</p>
            </button>
            <button
              type="button"
              onClick={() => applyExample('developer')}
              className="text-left p-3 bg-ben10-black border border-gray-700 rounded-lg hover:border-omnitrix transition-all"
            >
              <h4 className="font-medium text-white">Developer Agent</h4>
              <p className="text-xs text-gray-400 mt-1 line-clamp-2">Detail-oriented programmer with multi-language expertise</p>
            </button>
            <button
              type="button"
              onClick={() => applyExample('tutor')}
              className="text-left p-3 bg-ben10-black border border-gray-700 rounded-lg hover:border-omnitrix transition-all"
            >
              <h4 className="font-medium text-white">Educational Tutor</h4>
              <p className="text-xs text-gray-400 mt-1 line-clamp-2">Supportive educator who adapts to different learning styles</p>
            </button>
            <button
              type="button"
              onClick={() => applyExample('dataAnalyst')}
              className="text-left p-3 bg-ben10-black border border-gray-700 rounded-lg hover:border-omnitrix transition-all"
            >
              <h4 className="font-medium text-white">Data Analyst</h4>
              <p className="text-xs text-gray-400 mt-1 line-clamp-2">Methodical analyst with strong visualization skills</p>
            </button>
            <button
              type="button"
              onClick={() => applyExample('contentWriter')}
              className="text-left p-3 bg-ben10-black border border-gray-700 rounded-lg hover:border-omnitrix transition-all"
            >
              <h4 className="font-medium text-white">Content Writer</h4>
              <p className="text-xs text-gray-400 mt-1 line-clamp-2">Creative writer with strong storytelling abilities</p>
            </button>
          </div>
        )}
      </div>
      
      <form onSubmit={handleSubmit}>
        <div className="mb-6">
          <label className="block text-gray-300 font-semibold mb-2">
            <Tooltip text="Choose a unique, descriptive name that reflects the agent's purpose or personality.">
              Agent Name*
            </Tooltip>
          </label>
          <input
            type="text"
            name="name"
            value={formData.name}
            onChange={handleChange}
            className="w-full p-3 bg-ben10-black border border-gray-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-omnitrix focus:border-transparent"
            placeholder="Enter agent name (e.g., TechHelper, CodeMaster)"
            required
          />
        </div>
        
        <div className="mb-6">
          <label className="block text-gray-300 font-semibold mb-2">
            <Tooltip text="Define the agent's professional role or area of expertise. Be specific to help the agent understand its boundaries and capabilities.">
              Role*
            </Tooltip>
          </label>
          <input
            type="text"
            name="role"
            value={formData.role}
            onChange={handleChange}
            className="w-full p-3 bg-ben10-black border border-gray-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-omnitrix focus:border-transparent"
            placeholder="Enter agent role (e.g., Customer Support Specialist, Python Developer)"
            required
          />
          <p className="mt-1 text-xs text-gray-500">
            Example: "Technical Support Specialist", "Full-Stack Developer", "Data Science Tutor"
          </p>
        </div>
        
        <div className="mb-6">
          <label className="block text-gray-300 font-semibold mb-2">
            <Tooltip text="Describe the agent's personality traits, communication style, and approach to problem-solving. The more detailed, the better the agent will perform.">
              Personality & Expertise*
            </Tooltip>
          </label>
          <textarea
            name="personality"
            value={formData.personality}
            onChange={handleChange}
            className="w-full p-3 bg-ben10-black border border-gray-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-omnitrix focus:border-transparent"
            placeholder="Describe the agent's personality, expertise, and how it should interact with users"
            rows="6"
            required
          />
          <p className="mt-1 text-xs text-gray-500">
            Include details about: expertise areas, communication style, problem-solving approach, and any specific knowledge domains.
          </p>
        </div>
        
        <div className="mb-6">
          <label className="block text-gray-300 font-semibold mb-2">
            <Tooltip text="Select tools that your agent can use to accomplish tasks. Choose tools that align with the agent's role and expertise.">
              Tools
            </Tooltip>
          </label>
          {isLoadingTools ? (
            <div className="flex justify-center items-center h-20">
              <div className="relative w-12 h-12">
                <div className="absolute top-0 left-0 w-full h-full border-4 border-omnitrix border-t-transparent rounded-full animate-spin"></div>
                <div className="absolute top-1 left-1 w-10 h-10 border-4 border-ben10-alien border-b-transparent rounded-full animate-spin"></div>
              </div>
            </div>
          ) : (
            <div className="space-y-6">
              {/* Success message for tool creation */}
              {success && (
                <div className="mb-4 p-3 bg-green-900 bg-opacity-50 border border-green-700 rounded text-green-300">
                  {success}
                </div>
              )}
            
              {/* Custom Tool Creator Button */}
              <div className="mb-4">
                <button
                  type="button"
                  onClick={() => setShowToolCreator(!showToolCreator)}
                  className="px-4 py-2 bg-blue-800 hover:bg-blue-700 text-white rounded-md flex items-center"
                >
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                  </svg>
                  Create Custom Tool
                </button>
              </div>
              
              {/* Custom Tool Creator Form */}
              {showToolCreator && (
                <div className="mb-6 p-4 border border-blue-700 bg-blue-900 bg-opacity-20 rounded-lg">
                  <h3 className="text-white font-medium mb-3">Create a New Custom Tool</h3>
                  <div className="mb-3">
                    <label className="block text-gray-300 text-sm mb-1">
                      Tool Description (be specific about functionality)
                    </label>
                    <textarea
                      value={customToolDescription}
                      onChange={(e) => setCustomToolDescription(e.target.value)}
                      className="w-full p-3 bg-ben10-black border border-gray-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      placeholder="Create a tool that can fetch cryptocurrency prices from CoinGecko API..."
                      rows="3"
                    />
                    <p className="text-xs text-gray-400 mt-1">
                      Example: "Create a tool that can translate text between languages" or "Create a tool to get stock price information"
                    </p>
                  </div>
                  <div className="flex justify-end">
                    <button
                      type="button"
                      onClick={() => setShowToolCreator(false)}
                      className="px-3 py-1 text-sm border border-gray-700 text-gray-300 rounded-md mr-2"
                    >
                      Cancel
                    </button>
                    <button
                      type="button"
                      onClick={handleCreateCustomTool}
                      className="px-3 py-1 text-sm bg-blue-600 hover:bg-blue-500 text-white rounded-md flex items-center"
                      disabled={isCreatingTool}
                    >
                      {isCreatingTool ? (
                        <>
                          <svg className="animate-spin h-4 w-4 mr-2" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                          </svg>
                          Creating...
                        </>
                      ) : (
                        <>Create Tool</>
                      )}
                    </button>
                  </div>
                </div>
              )}
              
              {/* API Keys / Secrets Form */}
              {showSecretForm && currentTool && (
                <div className="mb-6 p-4 border border-yellow-700 bg-yellow-900 bg-opacity-20 rounded-lg">
                  <h3 className="text-white font-medium mb-3">
                    API Keys Required for {currentTool.name}
                  </h3>
                  <p className="text-sm text-gray-300 mb-3">
                    This tool requires the following API keys to function. Enter them below:
                  </p>
                  
                  {currentTool.secrets.map((secret) => (
                    <div className="mb-3" key={secret}>
                      <label className="block text-gray-300 text-sm mb-1">
                        {secret}
                      </label>
                      <input
                        type="password"
                        value={customToolSecrets[secret] || ''}
                        onChange={(e) => setCustomToolSecrets({
                          ...customToolSecrets,
                          [secret]: e.target.value
                        })}
                        className="w-full p-2 bg-ben10-black border border-gray-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-yellow-500 focus:border-transparent"
                        placeholder={`Enter your ${secret} here`}
                      />
                    </div>
                  ))}
                  
                  <div className="flex justify-end">
                    <button
                      type="button"
                      onClick={() => {
                        setShowSecretForm(false);
                        setCurrentTool(null);
                      }}
                      className="px-3 py-1 text-sm border border-gray-700 text-gray-300 rounded-md mr-2"
                    >
                      Skip
                    </button>
                    <button
                      type="button"
                      onClick={handleSaveSecrets}
                      className="px-3 py-1 text-sm bg-yellow-600 hover:bg-yellow-500 text-white rounded-md"
                    >
                      Save API Keys
                    </button>
                  </div>
                </div>
              )}

              {/* Native OpenAI tools section */}
              {groupedTools.web_search_preview && (
                <div>
                  <h3 className="text-sm font-semibold text-white mb-3 flex items-center">
                    OpenAI Native Tools
                    <span className="ml-2 px-2 py-0.5 text-xs bg-omnitrix bg-opacity-30 text-omnitrix-light rounded-full border border-omnitrix-dark">Recommended</span>
                  </h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    {groupedTools.web_search_preview.map((tool) => (
                      <div 
                        key={tool.name}
                        className={`p-4 border rounded-lg cursor-pointer transition-all duration-200 ${
                          formData.tools.includes(tool.name) 
                            ? 'bg-omnitrix bg-opacity-20 border-omnitrix shadow-omnitrix' 
                            : 'bg-ben10-black border-gray-700 hover:border-omnitrix-dark'
                        }`}
                        onClick={() => handleToolSelection(tool.name)}
                      >
                        <div className="flex items-start">
                          <div className={`w-5 h-5 mt-0.5 mr-3 rounded flex-shrink-0 border ${
                            formData.tools.includes(tool.name)
                              ? 'bg-omnitrix border-omnitrix-light'
                              : 'bg-ben10-black border-gray-700'
                          } flex items-center justify-center`}>
                            {formData.tools.includes(tool.name) && (
                              <svg xmlns="http://www.w3.org/2000/svg" className="h-3 w-3 text-white" viewBox="0 0 20 20" fill="currentColor">
                                <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                              </svg>
                            )}
                          </div>
                          <div>
                            <div className="font-medium flex items-center text-white">
                              {tool.name}
                              {renderToolTypeBadge(tool.type, tool.name)}
                            </div>
                            <div className="text-sm text-gray-400 mt-1">{tool.description}</div>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
              
              {/* Custom function tools section */}
              {groupedTools.function && (
                <div>
                  <h3 className="text-sm font-semibold text-white mb-3 flex items-center">
                    Function Tools
                    <span className="ml-2 px-2 py-0.5 text-xs bg-blue-900 bg-opacity-30 text-blue-300 rounded-full border border-blue-800">Standard & Custom</span>
                  </h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    {groupedTools.function.map((tool) => (
                      <div 
                        key={tool.name}
                        className={`p-4 border rounded-lg cursor-pointer transition-all duration-200 ${
                          formData.tools.includes(tool.name) 
                            ? 'bg-omnitrix bg-opacity-20 border-omnitrix shadow-omnitrix' 
                            : 'bg-ben10-black border-gray-700 hover:border-omnitrix-dark'
                        }`}
                        onClick={() => handleToolSelection(tool.name)}
                      >
                        <div className="flex items-start">
                          <div className={`w-5 h-5 mt-0.5 mr-3 rounded flex-shrink-0 border ${
                            formData.tools.includes(tool.name)
                              ? 'bg-omnitrix border-omnitrix-light'
                              : 'bg-ben10-black border-gray-700'
                          } flex items-center justify-center`}>
                            {formData.tools.includes(tool.name) && (
                              <svg xmlns="http://www.w3.org/2000/svg" className="h-3 w-3 text-white" viewBox="0 0 20 20" fill="currentColor">
                                <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                              </svg>
                            )}
                          </div>
                          <div>
                            <div className="font-medium flex items-center text-white">
                              {tool.name}
                              {renderToolTypeBadge(tool.type, tool.name)}
                            </div>
                            <div className="text-sm text-gray-400 mt-1">{tool.description}</div>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
        
        <div className="flex justify-end space-x-4">
          <button
            type="button"
            onClick={onCancel}
            className="px-6 py-2 border border-gray-700 rounded-md text-gray-300 hover:bg-ben10-black transition-colors duration-200"
            disabled={isSubmitting}
          >
            Cancel
          </button>
          <button
            type="submit"
            className="px-6 py-2 bg-gradient-to-r from-omnitrix-dark to-omnitrix text-white rounded-md shadow-omnitrix hover:shadow-omnitrix-pulse transition-all duration-300 flex items-center"
            disabled={isSubmitting}
          >
            {isSubmitting ? (
              <>
                <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Creating...
              </>
            ) : (
              <>
                Create Agent
                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 ml-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
                </svg>
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  );
};

export default AgentForm; 