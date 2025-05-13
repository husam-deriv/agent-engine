import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';

const API_URL = 'http://localhost:8000';

// Step indicator component
const StepIndicator = ({ currentStep, steps }) => {
  return (
    <div className="flex items-center mb-10">
      {steps.map((step, index) => (
        <React.Fragment key={index}>
          {index > 0 && (
            <div className={`h-0.5 w-16 ${index <= currentStep ? 'bg-[#c2161f]' : 'bg-gray-600/30'}`}></div>
          )}
          <div className="flex flex-col items-center">
            <div 
              className={`w-10 h-10 rounded-full flex items-center justify-center text-sm
              ${index < currentStep ? 'bg-[#c2161f] text-white' : 
                index === currentStep ? 'border-2 border-[#c2161f] text-[#c2161f]' : 'bg-gray-800/50 text-gray-400'}`}
            >
              {index + 1}
            </div>
            <div className="text-xs mt-2 text-muted-foreground font-medium">{step}</div>
          </div>
        </React.Fragment>
      ))}
    </div>
  );
};

const NewProject = () => {
  const navigate = useNavigate();
  const [currentStep, setCurrentStep] = useState(0);
  const [departments, setDepartments] = useState([]);
  const [companies, setCompanies] = useState([]);
  const [agents, setAgents] = useState([]);
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    department: '',
    company_id: '',
    goal: 'Productivity',
    solution_ids: [],
    skip_data_integration: false,
    skip_slack_integration: false
  });
  const [projectAnalysis, setProjectAnalysis] = useState(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [createSpecializedAgent, setCreateSpecializedAgent] = useState(true);
  const [generatingAgent, setGeneratingAgent] = useState(false);
  const [specializedAgent, setSpecializedAgent] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [recommendedAgents, setRecommendedAgents] = useState([]);
  const [creatingRecommendedAgent, setCreatingRecommendedAgent] = useState(false);
  
  // New state for multi-step architecture planning
  const [followupQuestions, setFollowupQuestions] = useState([]);
  const [questionAnswers, setQuestionAnswers] = useState([]);
  const [isLoadingQuestions, setIsLoadingQuestions] = useState(false);
  const [recommendedArchitecture, setRecommendedArchitecture] = useState(null);
  const [isGeneratingArchitecture, setIsGeneratingArchitecture] = useState(false);
  const [showQuestionsStep, setShowQuestionsStep] = useState(false);

  const steps = showQuestionsStep 
    ? ["Project Details", "Follow-up Questions", "AI Architecture", "Data Integration", "Slack Integration"] 
    : ["Project Details", "AI Agent Configuration", "Data Integration", "Slack Integration"];

  useEffect(() => {
    // Fetch departments
    const fetchDepartments = async () => {
      try {
        const response = await axios.get(`${API_URL}/departments`);
        setDepartments(response.data);
      } catch (err) {
        console.error('Error fetching departments:', err);
        setError('Failed to load departments. Please try again.');
      }
    };

    // Fetch companies
    const fetchCompanies = async () => {
      try {
        const response = await axios.get(`${API_URL}/companies`);
        setCompanies(response.data);
      } catch (err) {
        console.error('Error fetching companies:', err);
        setError('Failed to load companies. Please try again.');
      }
    };

    // Fetch AI solutions (agents)
    const fetchAgents = async () => {
      try {
        const response = await axios.get(`${API_URL}/list_agents`);
        setAgents(Object.values(response.data));
      } catch (err) {
        console.error('Error fetching agents:', err);
        setError('Failed to load AI solutions. Please try again.');
      }
    };

    fetchDepartments();
    fetchCompanies();
    fetchAgents();
  }, []);

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    
    if (type === 'checkbox') {
      const newSolutionIds = [...formData.solution_ids];
      if (checked) {
        newSolutionIds.push(parseInt(value));
      } else {
        const index = newSolutionIds.indexOf(parseInt(value));
        if (index > -1) {
          newSolutionIds.splice(index, 1);
        }
      }
      setFormData({ ...formData, solution_ids: newSolutionIds });
    } else {
      setFormData({ ...formData, [name]: value });
    }
  };

  const analyzeProject = async () => {
    // Only analyze if we have a title, description, and company
    if (!formData.title || !formData.description || !formData.company_id) {
      return;
    }
    
    setIsAnalyzing(true);
    try {
      const response = await axios.post(`${API_URL}/projects/analyze`, {
        title: formData.title,
        description: formData.description,
        company_id: parseInt(formData.company_id)
      });
      
      setProjectAnalysis(response.data);
      
      // Set skip integration flags based on project needs
      setFormData({
        ...formData,
        skip_data_integration: !response.data.needs_data_integration,
        skip_slack_integration: !response.data.needs_slack_integration
      });
      
      // Generate 3 recommended agent types for this project
      if (response.data.analysis && response.data.analysis.problem_type) {
        generateRecommendedAgentTypes(response.data);
      }
      
      // Set flag to show questions step and fetch questions
      setShowQuestionsStep(true);
      await fetchFollowupQuestions();
      
      // Optionally pre-select suggested tools
      if (response.data.agent_configuration.tools && response.data.agent_configuration.tools.length > 0) {
        // Find agent IDs for the suggested tools
        const suggestedAgentIds = agents
          .filter(agent => response.data.agent_configuration.tools.includes(agent.name))
          .map(agent => agent.id)
          .filter(id => id !== null && id !== undefined);
        
        if (suggestedAgentIds.length > 0) {
          setFormData({
            ...formData,
            solution_ids: suggestedAgentIds,
            skip_data_integration: !response.data.needs_data_integration,
            skip_slack_integration: !response.data.needs_slack_integration
          });
        }
      }
    } catch (err) {
      console.error('Error analyzing project:', err);
    } finally {
      setIsAnalyzing(false);
    }
  };

  // Generate 3 recommended agent types based on project analysis
  const generateRecommendedAgentTypes = (analysisData) => {
    const baseType = analysisData.analysis.problem_type;
    const company = companies.find(c => c.id.toString() === formData.company_id.toString());
    
    if (!company) return;
    
    const sector = company.sector_name;
    const recommendedAgents = [];
    
    // Add 3 different specialized roles based on project type
    if (baseType.includes('data') || baseType.includes('analytics')) {
      recommendedAgents.push({
        name: 'DataAnalyst',
        role: 'Data Analysis Specialist',
        description: `Specialized in ${sector} data processing and visualization`,
        problemType: 'Data Analysis',
        created: false
      });
      recommendedAgents.push({
        name: 'InsightGenerator',
        role: 'Business Insights Expert',
        description: `Generates key insights from ${company.name} data`,
        problemType: 'Business Intelligence',
        created: false
      });
      recommendedAgents.push({
        name: 'ReportAutomator',
        role: 'Automated Reporting Expert',
        description: `Creates automated reports for ${sector} metrics`,
        problemType: 'Report Automation',
        created: false
      });
    } else if (baseType.includes('marketing') || baseType.includes('content')) {
      recommendedAgents.push({
        name: 'ContentCreator',
        role: 'Content Generation Specialist',
        description: `Creates engaging content for ${company.name}`,
        problemType: 'Content Creation',
        created: false
      });
      recommendedAgents.push({
        name: 'MarketingAnalyst',
        role: 'Marketing Analysis Expert',
        description: `Analyzes marketing performance for ${sector} businesses`,
        problemType: 'Marketing Analysis',
        created: false
      });
      recommendedAgents.push({
        name: 'CampaignManager',
        role: 'Campaign Strategy Expert',
        description: `Develops marketing campaigns for ${company.name}`,
        problemType: 'Campaign Management',
        created: false
      });
    } else {
      // Generic recommendations
      recommendedAgents.push({
        name: `${baseType}Expert`,
        role: `${baseType} Expert`,
        description: `Specialized in ${baseType} for ${company.name}`,
        problemType: baseType,
        created: false
      });
      recommendedAgents.push({
        name: `${sector}Specialist`,
        role: `${sector} Industry Specialist`,
        description: `Expert in ${sector} industry solutions`,
        problemType: `${sector} Solutions`,
        created: false
      });
      recommendedAgents.push({
        name: 'ProcessAutomator',
        role: 'Process Automation Expert',
        description: `Automates workflows for ${company.name}`,
        problemType: 'Process Automation',
        created: false
      });
    }
    
    setRecommendedAgents(recommendedAgents);
  };

  const createRecommendedAgent = async (agent, index) => {
    if (!formData.company_id) return;
    
    setCreatingRecommendedAgent(true);
    try {
      const response = await axios.post(`${API_URL}/api/generate-agent`, {
        project_title: formData.title,
        project_description: formData.description,
        company_id: parseInt(formData.company_id),
        problem_type: agent.problemType,
        suggested_tools: projectAnalysis.agent_configuration.tools || []
      });
      
      // Update the recommended agents list to show this one as created
      const updatedRecommendedAgents = [...recommendedAgents];
      updatedRecommendedAgents[index] = {
        ...updatedRecommendedAgents[index],
        created: true,
        id: response.data.id
      };
      setRecommendedAgents(updatedRecommendedAgents);
      
      // Add to the agents list and update the formData to include this agent
      const newAgent = {
        id: response.data.id,
        name: response.data.name,
        role: response.data.role,
        personality: response.data.personality,
        tools: response.data.tools
      };
      
      setAgents(prevAgents => [...prevAgents, newAgent]);
      
      // Add to selected solutions
      const newSolutionIds = [...formData.solution_ids, response.data.id];
      setFormData({ ...formData, solution_ids: newSolutionIds });
      
    } catch (err) {
      console.error('Error creating recommended agent:', err);
      setError('Failed to create recommended agent. Please try again.');
    } finally {
      setCreatingRecommendedAgent(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);

    try {
      // Use recommendedArchitecture if available to create a project with custom agents
      if (recommendedArchitecture) {
        // We'll need to create agents from the architecture recommendation
        const response = await axios.post(`${API_URL}/projects/create-with-agent`, {
          ...formData,
          recommended_architecture: recommendedArchitecture
        });
        
        setSpecializedAgent(response.data.specialized_agent);
        setGeneratingAgent(false);
        navigate('/roadmap');
      } else if (createSpecializedAgent && projectAnalysis) {
        // If no architecture but user wants a specialized agent, use the specialized endpoint
        setGeneratingAgent(true);
        const response = await axios.post(`${API_URL}/projects/create-with-agent`, formData);
        setSpecializedAgent(response.data.specialized_agent);
        setGeneratingAgent(false);
        navigate('/roadmap');
      } else {
        // Create a basic project (possibly with pre-selected existing agents)
        const response = await axios.post(`${API_URL}/projects`, formData);
        navigate('/roadmap');
      }
      
      // Reset form and move to success state
      setCurrentStep(steps.length - 1);
    } catch (err) {
      console.error('Error creating project:', err);
      setError(`Failed to create project: ${err.response?.data?.detail || err.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  const nextStep = () => {
    if (currentStep < steps.length - 1) {
      // If moving from project details to follow-up questions or agent config, analyze the project
      if (currentStep === 0) {
        analyzeProject();
      }
      
      // If moving from follow-up questions to architecture recommendation, generate architecture
      if (showQuestionsStep && currentStep === 1) {
        generateArchitectureRecommendation();
      }
      
      // Skip logic for data and slack integration steps
      const dataIntegrationStep = showQuestionsStep ? 3 : 2;
      const slackIntegrationStep = showQuestionsStep ? 4 : 3;
      
      // If we're at the current step before data integration and it should be skipped
      if (currentStep === dataIntegrationStep - 1 && 
          (!projectAnalysis || 
           !projectAnalysis.data_requirements || 
           projectAnalysis.data_requirements.length === 0 ||
           formData.skip_data_integration)) {
        setFormData({...formData, skip_data_integration: true});
        // Skip to the next step (Slack integration) or finish if Slack should also be skipped
        if (formData.skip_slack_integration) {
          handleSubmit(new Event('skip'));
          return;
        }
        setCurrentStep(slackIntegrationStep);
        return;
      }
      
      // If we're at data integration step and should skip slack
      if (currentStep === slackIntegrationStep - 1 && formData.skip_slack_integration) {
        setFormData({...formData, skip_slack_integration: true});
        handleSubmit(new Event('skip'));
        return;
      }
      
      setCurrentStep(currentStep + 1);
    }
  };

  const prevStep = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1);
    }
  };

  // New functions for fetching questions and recommending architecture
  const fetchFollowupQuestions = async () => {
    if (!formData.title || !formData.description || !formData.company_id) {
      return;
    }
    
    setIsLoadingQuestions(true);
    try {
      const response = await axios.post(`${API_URL}/projects/generate-questions`, {
        title: formData.title,
        description: formData.description,
        company_id: parseInt(formData.company_id)
      });
      
      setFollowupQuestions(response.data.questions);
      
      // Initialize question answers with empty answers
      const initialAnswers = response.data.questions.map(question => ({
        question,
        answer: ""
      }));
      
      setQuestionAnswers(initialAnswers);
    } catch (err) {
      console.error('Error fetching follow-up questions:', err);
      setError('Failed to generate follow-up questions. Please try again.');
    } finally {
      setIsLoadingQuestions(false);
    }
  };
  
  const handleAnswerChange = (index, answer) => {
    const updatedAnswers = [...questionAnswers];
    updatedAnswers[index] = {
      ...updatedAnswers[index],
      answer
    };
    setQuestionAnswers(updatedAnswers);
  };
  
  const generateArchitectureRecommendation = async () => {
    if (questionAnswers.length === 0 || questionAnswers.some(qa => !qa.answer.trim())) {
      setError('Please answer all questions before proceeding.');
      return;
    }
    
    setIsGeneratingArchitecture(true);
    try {
      const response = await axios.post(`${API_URL}/projects/recommend-architecture`, {
        title: formData.title,
        description: formData.description,
        company_id: parseInt(formData.company_id),
        question_answers: questionAnswers
      });
      
      setRecommendedArchitecture(response.data);
      
      // Add agents from architecture to solution_ids
      if (response.data.agents && response.data.agents.length > 0) {
        // For now, we'll need to create these agents from the architecture
        // This will be implemented in the next step
      }
    } catch (err) {
      console.error('Error generating architecture recommendation:', err);
      setError('Failed to generate architecture recommendation. Please try again.');
    } finally {
      setIsGeneratingArchitecture(false);
    }
  };

  // Render different steps based on currentStep
  const renderStep = () => {
    switch (currentStep) {
      case 0:
        return (
          <div className="space-y-6">
            <div className="mb-8">
              <h3 className="text-xl font-semibold text-foreground mb-2">Project Details</h3>
              <p className="text-sm text-muted-foreground">Add information about your new AI project for the roadmap</p>
            </div>
            
            <div className="space-y-6">
              <div>
                <label htmlFor="title" className="block text-sm font-medium text-foreground mb-2">Project Title</label>
                <input
                  type="text"
                  id="title"
                  name="title"
                  value={formData.title}
                  onChange={handleChange}
                  placeholder="e.g. Deep Research Agent for Supply Chain Optimization"
                  className="w-full px-4 py-3 bg-background border border-border rounded-md focus:outline-none focus:ring-2 focus:ring-[#c2161f] focus:border-[#c2161f] text-foreground"
                  required
                />
              </div>
              
              <div>
                <label htmlFor="description" className="block text-sm font-medium text-foreground mb-2">Project Description</label>
                <textarea
                  id="description"
                  name="description"
                  value={formData.description}
                  onChange={handleChange}
                  placeholder="Describe the project goals, expected outcomes, and key milestones. Include details about what data sources will be used, what insights are needed, and how the AI solution should work."
                  rows="5"
                  className="w-full px-4 py-3 bg-background border border-border rounded-md focus:outline-none focus:ring-2 focus:ring-[#c2161f] focus:border-[#c2161f] text-foreground"
                ></textarea>
              </div>
              
              <div>
                <label htmlFor="company_id" className="block text-sm font-medium text-foreground mb-2">Company</label>
                <select
                  id="company_id"
                  name="company_id"
                  value={formData.company_id}
                  onChange={handleChange}
                  className="w-full px-4 py-3 bg-background border border-border rounded-md focus:outline-none focus:ring-2 focus:ring-[#c2161f] focus:border-[#c2161f] text-foreground"
                  required
                >
                  <option value="">Select a company</option>
                  {companies.map(company => (
                    <option key={company.id} value={company.id}>
                      {company.name} ({company.sector_name})
                    </option>
                  ))}
                </select>
              </div>
              
              <div>
                <label htmlFor="department" className="block text-sm font-medium text-foreground mb-2">Department</label>
                <select
                  id="department"
                  name="department"
                  value={formData.department}
                  onChange={handleChange}
                  className="w-full px-4 py-3 bg-background border border-border rounded-md focus:outline-none focus:ring-2 focus:ring-[#c2161f] focus:border-[#c2161f] text-foreground"
                  required
                >
                  <option value="">Select a department</option>
                  {departments.map(dept => (
                    <option key={dept.id} value={dept.name}>{dept.name}</option>
                  ))}
                </select>
              </div>
              
              <div>
                <label htmlFor="goal" className="block text-sm font-medium text-foreground mb-2">Project Goal</label>
                <select
                  id="goal"
                  name="goal"
                  value={formData.goal}
                  onChange={handleChange}
                  className="w-full px-4 py-3 bg-background border border-border rounded-md focus:outline-none focus:ring-2 focus:ring-[#c2161f] focus:border-[#c2161f] text-foreground"
                >
                  <option value="Productivity">Productivity</option>
                  <option value="Cost Savings">Cost Savings</option>
                  <option value="Win new Customers">Win new Customers</option>
                  <option value="Learning and Governance">Learning and Governance</option>
                </select>
              </div>
            </div>
          </div>
        );
      case 1:
        if (showQuestionsStep) {
          return (
            <div className="space-y-6">
              <div className="mb-8">
                <h3 className="text-xl font-semibold text-foreground mb-2">Follow-up Questions</h3>
                <p className="text-sm text-muted-foreground">Please answer these questions to help us better understand your project requirements</p>
              </div>
              
              {isLoadingQuestions ? (
                <div className="flex justify-center py-16">
                  <div className="animate-spin rounded-full h-14 w-14 border-t-2 border-b-2 border-[#c2161f]"></div>
                </div>
              ) : (
                <div className="space-y-6">
                  {followupQuestions.map((question, index) => (
                    <div key={index} className="bg-card/40 border border-border rounded-lg p-5 hover:bg-card/70 transition-colors">
                      <p className="text-foreground font-medium mb-3">{question}</p>
                      <textarea
                        value={questionAnswers[index]?.answer || ""}
                        onChange={(e) => handleAnswerChange(index, e.target.value)}
                        placeholder="Your answer..."
                        rows="3"
                        className="w-full px-4 py-3 bg-background border border-border rounded-md focus:outline-none focus:ring-2 focus:ring-[#c2161f] focus:border-[#c2161f] text-foreground"
                      ></textarea>
                    </div>
                  ))}
                </div>
              )}
            </div>
          );
        }
      case 2:
        if (showQuestionsStep && currentStep === 2) {
          return (
            <div className="space-y-6">
              <div className="mb-8">
                <h3 className="text-xl font-semibold text-foreground mb-2">AI Architecture Recommendation</h3>
                <p className="text-sm text-muted-foreground">Based on your project description and answers, here's our recommended AI solution architecture</p>
              </div>
              
              {isGeneratingArchitecture ? (
                <div className="flex flex-col items-center justify-center py-16 space-y-5">
                  <div className="animate-spin rounded-full h-14 w-14 border-t-2 border-b-2 border-[#c2161f]"></div>
                  <p className="text-foreground">Designing the optimal AI architecture for your project...</p>
                </div>
              ) : recommendedArchitecture ? (
                <div className="space-y-8">
                  <div className="bg-[#c2161f]/10 border border-[#c2161f]/30 rounded-lg p-6">
                    <h4 className="text-lg font-semibold text-[#c2161f] mb-4">Recommended Architecture</h4>
                    <div className="flex items-center">
                      <span className="bg-[#c2161f] text-white text-xs px-3 py-1.5 rounded-full font-medium">
                        {recommendedArchitecture.architecture_type === 'single_agent' ? 'Single Agent' :
                         recommendedArchitecture.architecture_type === 'sequential' ? 'Sequential Workflow' :
                         'Multi-Agent Team'}
                      </span>
                      <p className="ml-3 text-sm text-foreground">{recommendedArchitecture.description}</p>
                    </div>
                    
                    {recommendedArchitecture.workflow && (
                      <div className="mt-4 pt-4 border-t border-[#c2161f]/20">
                        <h5 className="text-sm font-medium text-foreground mb-2">Workflow</h5>
                        <p className="text-sm text-muted-foreground">{recommendedArchitecture.workflow}</p>
                      </div>
                    )}
                  </div>
                  
                  <div>
                    <h4 className="text-lg font-semibold text-foreground mb-4">Recommended Agents</h4>
                    
                    <div className="space-y-5">
                      {recommendedArchitecture.agents.map((agent, index) => (
                        <div key={index} className="border border-border rounded-lg p-5 bg-card/50 hover:bg-card transition-colors">
                          <div className="flex justify-between items-start">
                            <div>
                              <h5 className="font-medium text-foreground">{agent.name}</h5>
                              <p className="text-sm text-muted-foreground">{agent.role}</p>
                            </div>
                            <span className="bg-[#c2161f]/20 text-[#c2161f] text-xs px-3 py-1.5 rounded-full font-medium">
                              {recommendedArchitecture.architecture_type === 'multi_agent' && index === 0 ? 'Triage Agent' : 
                               `Agent ${index + 1}`}
                            </span>
                          </div>
                          
                          <p className="text-xs text-muted-foreground mt-3">{agent.personality}</p>
                          
                          {agent.tools && agent.tools.length > 0 && (
                            <div className="mt-4">
                              <h6 className="text-xs font-medium text-foreground mb-2">Tools</h6>
                              <div className="flex flex-wrap gap-2 mt-1">
                                {agent.tools.map((tool, i) => (
                                  <span key={i} className="text-xs bg-secondary text-secondary-foreground py-1.5 px-3 rounded-full">{tool}</span>
                                ))}
                              </div>
                            </div>
                          )}
                          
                          {agent.knowledge_sources && agent.knowledge_sources.length > 0 && (
                            <div className="mt-4">
                              <h6 className="text-xs font-medium text-foreground mb-2">Knowledge Sources</h6>
                              <ul className="text-xs text-muted-foreground list-disc list-inside space-y-1">
                                {agent.knowledge_sources.map((source, i) => (
                                  <li key={i}>{source}</li>
                                ))}
                              </ul>
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              ) : (
                <div className="text-center py-16 text-muted-foreground">
                  No architecture recommendation available. Please go back to answer the follow-up questions.
                </div>
              )}
            </div>
          );
        } else {
          return (
            <div className="space-y-6">
              <div className="mb-8">
                <h3 className="text-xl font-semibold text-foreground mb-2">AI Agent Configuration</h3>
                <p className="text-sm text-muted-foreground">Select the AI solutions to use in this project</p>
              </div>
              
              {projectAnalysis && (
                <div className="border border-[#c2161f]/30 rounded-lg p-6 mb-6 bg-[#c2161f]/10">
                  <h4 className="font-semibold text-[#c2161f] text-lg mb-3">Recommended Configuration</h4>
                  <p className="text-sm text-foreground mb-4">Based on your project description, we recommend the following:</p>
                  
                  <div className="space-y-4">
                    <div className="flex items-center">
                      <span className="text-sm font-medium text-foreground w-36">Type:</span>
                      <span className="text-sm text-muted-foreground">{projectAnalysis.agent_configuration.type} Agent</span>
                    </div>
                    <div className="flex items-center">
                      <span className="text-sm font-medium text-foreground w-36">Suggested Name:</span>
                      <span className="text-sm text-muted-foreground">{projectAnalysis.agent_configuration.name}</span>
                    </div>
                    <div>
                      <span className="text-sm font-medium text-foreground block mb-2">Recommended Tools:</span>
                      <div className="flex flex-wrap gap-2 mt-1">
                        {projectAnalysis.agent_configuration.tools.map((tool, index) => (
                          <span key={index} className="text-xs bg-[#c2161f] text-white py-1.5 px-3 rounded-full">{tool}</span>
                        ))}
                      </div>
                    </div>
                    <div className="flex items-center">
                      <span className="text-sm font-medium text-foreground w-36">Scheduling:</span>
                      <span className="text-sm text-muted-foreground">
                        {projectAnalysis.agent_configuration.is_scheduled 
                          ? `Scheduled (${projectAnalysis.agent_configuration.schedule_frequency})` 
                          : 'On-demand'}
                      </span>
                    </div>
                    <div className="flex items-center">
                      <span className="text-sm font-medium text-foreground w-36">Slack Channel:</span>
                      <span className="text-sm text-muted-foreground">#{projectAnalysis.agent_configuration.slack_channel}</span>
                    </div>
                  </div>
                  
                  {recommendedAgents.length > 0 && (
                    <div className="mt-8 border-t border-border pt-6">
                      <h5 className="font-semibold text-[#c2161f] text-base mb-4">Recommended Specialized Agents</h5>
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        {recommendedAgents.map((agent, index) => (
                          <div key={index} className="border border-border rounded-lg p-4 relative hover:bg-card/70 transition-colors">
                            <h6 className="font-medium text-foreground">{agent.name}</h6>
                            <p className="text-sm text-muted-foreground">{agent.role}</p>
                            <p className="text-xs text-muted-foreground mt-2">{agent.description}</p>
                            {agent.created ? (
                              <div className="mt-4 bg-green-900/20 text-green-500 text-xs py-1.5 px-3 rounded-md flex items-center">
                                <svg xmlns="http://www.w3.org/2000/svg" className="h-3.5 w-3.5 mr-1.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                                </svg>
                                Added to available agents
                              </div>
                            ) : (
                              <button
                                type="button"
                                onClick={() => createRecommendedAgent(agent, index)}
                                disabled={creatingRecommendedAgent}
                                className="mt-4 bg-[#c2161f] text-white text-xs py-1.5 px-3 rounded-md hover:bg-[#c2161f]/90 transition-colors flex items-center"
                              >
                                {creatingRecommendedAgent ? (
                                  <>
                                    <svg className="animate-spin -ml-1 mr-1.5 h-3.5 w-3.5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                                    </svg>
                                    Creating...
                                  </>
                                ) : (
                                  <>Create Agent</>
                                )}
                              </button>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                  
                  <div className="mt-6 border-t border-border pt-6">
                    <div className="flex items-center">
                      <input
                        type="checkbox"
                        id="create-specialized-agent"
                        checked={createSpecializedAgent}
                        onChange={(e) => setCreateSpecializedAgent(e.target.checked)}
                        className="h-4 w-4 text-[#c2161f] focus:ring-[#c2161f] border-border rounded bg-background"
                      />
                      <label htmlFor="create-specialized-agent" className="ml-2 block text-sm text-foreground">
                        Create a specialized AI agent for this project
                      </label>
                    </div>
                    <p className="text-xs text-muted-foreground mt-2 ml-6">
                      We'll automatically generate a custom AI agent optimized for this specific project
                    </p>
                  </div>
                  
                  {specializedAgent && (
                    <div className="mt-6 border-t border-border pt-6">
                      <h5 className="font-semibold text-[#c2161f] mb-3">Generated Specialized Agent</h5>
                      <div className="mt-3 p-4 bg-card border border-border rounded-lg">
                        <div className="font-medium text-foreground">{specializedAgent.name}</div>
                        <div className="text-sm text-muted-foreground">{specializedAgent.role}</div>
                        <div className="text-xs text-muted-foreground mt-3">{specializedAgent.personality.substring(0, 150)}...</div>
                      </div>
                    </div>
                  )}
                </div>
              )}
              
              <div className="border border-border rounded-lg p-6 space-y-5">
                <h4 className="font-semibold text-foreground text-lg">Available AI Solutions</h4>
                
                <div className="space-y-4 max-h-96 overflow-y-auto pr-2 scrollbar-thin scrollbar-thumb-gray-700 scrollbar-track-transparent">
                  {agents.map(agent => (
                    <div key={agent.name} className="border border-border rounded-lg p-4 flex items-start bg-card/50 hover:bg-card transition-colors">
                      <input
                        type="checkbox"
                        id={`solution-${agent.name}`}
                        name="solution_ids"
                        value={agent.id || ''}
                        checked={formData.solution_ids.includes(agent.id)}
                        onChange={handleChange}
                        className="mt-1 h-4 w-4 text-[#c2161f] focus:ring-[#c2161f] border-border rounded bg-background"
                      />
                      <div className="ml-3">
                        <label htmlFor={`solution-${agent.name}`} className="font-medium text-foreground block">{agent.name}</label>
                        <p className="text-xs text-muted-foreground">{agent.role}</p>
                        <p className="text-sm text-muted-foreground mt-2">{agent.personality?.substring(0, 100)}...</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          );
        }
      case 3:
        const dataIntegrationCase = showQuestionsStep ? 3 : 2;
        if (currentStep === dataIntegrationCase) {
          return (
            <div className="space-y-6">
              <div className="mb-8">
                <h3 className="text-xl font-semibold text-foreground mb-2">Data Integration</h3>
                <p className="text-sm text-muted-foreground">
                  {projectAnalysis && projectAnalysis.needs_data_integration 
                    ? "Connect your data sources to enhance the AI project"
                    : "This project type doesn't require data integration"}
                </p>
              </div>
              
              {projectAnalysis && projectAnalysis.data_requirements && projectAnalysis.data_requirements.length > 0 ? (
                <div className="border border-[#c2161f]/30 rounded-lg p-6 mb-6 bg-[#c2161f]/10">
                  <h4 className="font-semibold text-[#c2161f] text-lg mb-3">Recommended Data Sources</h4>
                  <p className="text-sm text-foreground mb-4">Based on your project description, we recommend the following data:</p>
                  
                  <div className="space-y-4">
                    {projectAnalysis.data_requirements.map((req, index) => (
                      <div key={index} className="border border-border rounded-lg p-5 bg-card/50 hover:bg-card transition-colors">
                        <h5 className="font-medium text-foreground mb-2">{req.description}</h5>
                        <div className="flex items-center">
                          <span className="text-xs bg-secondary text-secondary-foreground py-1.5 px-3 rounded-full">{req.type}</span>
                          <span className="text-xs ml-3 text-muted-foreground">
                            {req.is_company_specific ? 'Company Specific' : 'Sector-Wide Data'}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              ) : (
                <div className="border border-border rounded-lg p-6 mb-6">
                  <p className="text-center text-muted-foreground my-6">
                    {projectAnalysis && !projectAnalysis.needs_data_integration 
                      ? "No data integration is required for this project type." 
                      : "No specific data requirements identified for this project."}
                  </p>
                  <div className="text-center">
                    <button
                      type="button"
                      onClick={() => {
                        setFormData({...formData, skip_data_integration: true});
                        nextStep();
                      }}
                      className="px-5 py-2.5 bg-secondary text-secondary-foreground rounded-md hover:bg-secondary/80 transition-colors"
                    >
                      Skip This Step
                    </button>
                  </div>
                </div>
              )}
              
              {(!projectAnalysis || projectAnalysis.needs_data_integration) && (
                <div className="border border-border rounded-lg p-6">
                  <div className="text-center py-8">
                    <button 
                      type="button"
                      className="px-6 py-3 bg-[#c2161f] text-white rounded-md hover:bg-[#c2161f]/90 transition-colors flex items-center mx-auto"
                      onClick={() => console.log("Data upload will be implemented")}
                    >
                      <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                      </svg>
                      Upload Data Files
                    </button>
                    <p className="text-sm text-muted-foreground mt-4">
                      Upload CSV files, databases, or other data sources for your AI project.
                    </p>
                  </div>
                </div>
              )}
            </div>
          );
        }
      case 4:
        const slackCase = showQuestionsStep ? 4 : 3;
        if (currentStep === slackCase) {
          return (
            <div className="space-y-6">
              <div className="mb-8">
                <h3 className="text-xl font-semibold text-foreground mb-2">Slack Integration</h3>
                <p className="text-sm text-muted-foreground">
                  {projectAnalysis && projectAnalysis.needs_slack_integration 
                    ? "Configure Slack integration for this project"
                    : "Slack integration is optional for this project type"}
                </p>
              </div>
              
              {projectAnalysis && projectAnalysis.agent_configuration && projectAnalysis.agent_configuration.slack_channel ? (
                <div className="border border-[#c2161f]/30 rounded-lg p-6 mb-6 bg-[#c2161f]/10">
                  <h4 className="font-semibold text-[#c2161f] text-lg mb-4">Recommended Slack Configuration</h4>
                  <div className="space-y-4">
                    <div className="flex items-center">
                      <span className="text-sm font-medium text-foreground w-36">Channel:</span>
                      <span className="text-sm text-muted-foreground">#{projectAnalysis.agent_configuration.slack_channel}</span>
                    </div>
                    <div className="flex items-center">
                      <span className="text-sm font-medium text-foreground w-36">Mode:</span>
                      <span className="text-sm text-muted-foreground">{projectAnalysis.agent_configuration.is_scheduled ? 'Scheduled Posts + On-demand' : 'On-demand Only'}</span>
                    </div>
                    {projectAnalysis.agent_configuration.is_scheduled && (
                      <div className="flex items-center">
                        <span className="text-sm font-medium text-foreground w-36">Frequency:</span>
                        <span className="text-sm text-muted-foreground">{projectAnalysis.agent_configuration.schedule_frequency}</span>
                      </div>
                    )}
                  </div>
                </div>
              ) : (
                <div className="border border-border rounded-lg p-6 mb-6">
                  <p className="text-center text-muted-foreground my-6">
                    {projectAnalysis && !projectAnalysis.needs_slack_integration 
                      ? "Slack integration is optional for this project type." 
                      : "No specific Slack configuration identified for this project."}
                  </p>
                  <div className="text-center">
                    <button
                      type="button"
                      onClick={() => {
                        setFormData({...formData, skip_slack_integration: true});
                        handleSubmit(new Event('skip'));
                      }}
                      className="px-5 py-2.5 bg-secondary text-secondary-foreground rounded-md hover:bg-secondary/80 transition-colors"
                    >
                      Skip This Step
                    </button>
                  </div>
                </div>
              )}
              
              <div className="border border-border rounded-lg p-6">
                <div className="text-center py-10">
                  <div className="flex items-center justify-center mb-4">
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-12 w-12 text-[#c2161f]/70" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8 12h.01M12 12h.01M16 12h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  </div>
                  <p className="text-foreground mb-3">Slack integration will be set up after project creation.</p>
                  <p className="text-sm text-muted-foreground">You can configure your Slack workspace and channels in the project settings later.</p>
                </div>
              </div>
            </div>
          );
        }
      default:
        return null;
    }
  };

  return (
    <div className="container mx-auto py-10 px-4 max-w-5xl">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-foreground">Add New AI Project</h1>
      </div>

      <div className="bg-card rounded-xl border border-border p-8 shadow-lg">
        <StepIndicator currentStep={currentStep} steps={steps} />
        
        <form onSubmit={handleSubmit}>
          {renderStep()}
          
          {error && (
            <div className="mt-6 bg-destructive/10 border border-destructive/20 text-destructive px-4 py-3 rounded-md" role="alert">
              <span className="block sm:inline">{error}</span>
            </div>
          )}
          
          <div className="mt-10 flex justify-between">
            <button
              type="button"
              onClick={prevStep}
              disabled={currentStep === 0}
              className={`px-5 py-2.5 rounded-md font-medium transition-colors ${currentStep === 0 ? 'bg-background text-muted-foreground cursor-not-allowed' : 'bg-secondary text-secondary-foreground hover:bg-secondary/80'}`}
            >
              Previous
            </button>
            
            {currentStep < steps.length - 1 ? (
              <button
                type="button"
                onClick={nextStep}
                className="px-5 py-2.5 bg-[#c2161f] text-white rounded-md hover:bg-[#c2161f]/90 transition-colors font-medium"
              >
                Next: {steps[currentStep + 1]}
              </button>
            ) : (
              <button
                type="submit"
                disabled={isLoading || generatingAgent}
                className="px-5 py-2.5 bg-[#c2161f] text-white rounded-md hover:bg-[#c2161f]/90 transition-colors font-medium flex items-center"
              >
                {isLoading || generatingAgent ? (
                  <>
                    <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    {generatingAgent ? 'Generating Agent...' : 'Creating...'}
                  </>
                ) : (
                  'Create Project'
                )}
              </button>
            )}
          </div>
        </form>
      </div>
    </div>
  );
};

export default NewProject; 