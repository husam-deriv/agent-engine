import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import axios from 'axios';

const API_URL = 'http://localhost:8000';

const ProjectDetail = () => {
  const { projectId } = useParams();
  const navigate = useNavigate();
  
  const [project, setProject] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  
  useEffect(() => {
    const fetchProject = async () => {
      try {
        const response = await axios.get(`${API_URL}/projects/${projectId}`);
        setProject(response.data);
        setIsLoading(false);
      } catch (error) {
        console.error('Error fetching project:', error);
        setError(`Failed to fetch project: ${error.response?.data?.detail || error.message}`);
        setIsLoading(false);
      }
    };
    
    fetchProject();
  }, [projectId]);
  
  const runProject = () => {
    navigate(`/projects/${projectId}/chat`);
  };
  
  const deleteProject = async () => {
    setIsDeleting(true);
    try {
      await axios.delete(`${API_URL}/projects/${projectId}`);
      // Redirect to roadmap after successful deletion
      navigate('/roadmap', { state: { message: `Project "${project.title}" deleted successfully` } });
    } catch (error) {
      console.error('Error deleting project:', error);
      setError(`Failed to delete project: ${error.response?.data?.detail || error.message}`);
      setShowDeleteConfirm(false);
      setIsDeleting(false);
    }
  };
  
  // Modal outside click handler
  const handleModalOutsideClick = (e) => {
    if (e.target.id === 'delete-modal-backdrop') {
      setShowDeleteConfirm(false);
    }
  };
  
  if (isLoading) {
    return (
      <div className="flex justify-center items-center h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary"></div>
      </div>
    );
  }
  
  if (error || !project) {
    return (
      <div className="container mx-auto p-4">
        <div className="bg-destructive/10 border border-destructive/30 text-destructive dark:text-destructive-foreground px-4 py-3 rounded">
          {error || "Project not found"}
        </div>
        <div className="mt-4">
          <Link to="/roadmap" className="text-primary hover:underline">
            &larr; Back to Roadmap
          </Link>
        </div>
      </div>
    );
  }
  
  return (
    <div className="container mx-auto p-4">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-2xl font-bold text-foreground">{project.title}</h1>
          <div className="text-sm text-muted-foreground">
            {new Date(project.created_at).toLocaleDateString()}
          </div>
        </div>
        <div className="flex gap-2">
          <Link to="/roadmap" className="px-4 py-2 bg-secondary text-secondary-foreground rounded-md hover:bg-secondary/80 transition-colors">
            Back to Roadmap
          </Link>
          <button
            onClick={runProject}
            className="px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 transition-colors flex items-center"
          >
            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            Run Project
          </button>
          <button
            onClick={() => setShowDeleteConfirm(true)}
            className="px-4 py-2 bg-destructive/10 text-destructive dark:text-destructive/90 rounded-md hover:bg-destructive/20 transition-colors flex items-center"
          >
            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
            </svg>
            Delete
          </button>
        </div>
      </div>
      
      {/* Delete confirmation modal */}
      {showDeleteConfirm && (
        <div 
          id="delete-modal-backdrop"
          className="fixed inset-0 bg-background/80 backdrop-blur-sm flex justify-center items-center z-50"
          onClick={handleModalOutsideClick}
        >
          <div className="bg-card text-card-foreground rounded-lg p-6 w-full max-w-md shadow-xl border border-border">
            <h3 className="text-xl font-bold text-foreground mb-4">Confirm Deletion</h3>
            <p className="text-muted-foreground mb-6">
              Are you sure you want to delete the project "{project.title}"? This action cannot be undone.
            </p>
            <div className="flex justify-end gap-3">
              <button
                onClick={() => setShowDeleteConfirm(false)}
                className="px-4 py-2 bg-secondary text-secondary-foreground rounded-md hover:bg-secondary/80 transition-colors"
                disabled={isDeleting}
              >
                Cancel
              </button>
              <button
                onClick={deleteProject}
                className="px-4 py-2 bg-destructive text-destructive-foreground rounded-md hover:bg-destructive/90 transition-colors flex items-center"
                disabled={isDeleting}
              >
                {isDeleting ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-t-2 border-b-2 border-destructive-foreground mr-2"></div>
                    Deleting...
                  </>
                ) : (
                  'Delete Project'
                )}
              </button>
            </div>
          </div>
        </div>
      )}
      
      <div className="bg-card text-card-foreground shadow-sm rounded-lg p-6 mb-6 border border-border">
        <div className="mb-4">
          <h2 className="text-lg font-semibold text-foreground mb-2">Project Details</h2>
          <p className="text-muted-foreground whitespace-pre-line">{project.description}</p>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
          <div>
            <h3 className="text-sm font-medium text-muted-foreground">Department</h3>
            <p className="text-foreground">{project.department}</p>
          </div>
          <div>
            <h3 className="text-sm font-medium text-muted-foreground">Goal</h3>
            <p className="text-foreground">{project.goal}</p>
          </div>
          <div>
            <h3 className="text-sm font-medium text-muted-foreground">Status</h3>
            <p className="text-foreground">{project.status}</p>
          </div>
        </div>
        
        {project.schedule_frequency && (
          <div className="mb-4">
            <h3 className="text-sm font-medium text-muted-foreground">Scheduling</h3>
            <p className="text-foreground">
              {project.is_scheduled ? `Scheduled (${project.schedule_frequency})` : 'On-demand'}
            </p>
          </div>
        )}
        
        {project.slack_channel && (
          <div>
            <h3 className="text-sm font-medium text-muted-foreground">Slack Integration</h3>
            <p className="text-foreground">#{project.slack_channel}</p>
          </div>
        )}
      </div>
      
      {/* AI Solutions Section */}
      <div className="bg-card text-card-foreground shadow-sm rounded-lg p-6 mb-6 border border-border">
        <h2 className="text-lg font-semibold text-foreground mb-4">AI Solutions</h2>
        
        {project.agents && project.agents.length > 0 ? (
          <div className="space-y-4">
            {project.agents.map((agent) => (
              <div key={agent.id} className="border border-border rounded-lg p-4">
                <div className="flex justify-between">
                  <div>
                    <h3 className="font-medium text-foreground">{agent.name}</h3>
                    <p className="text-sm text-muted-foreground">{agent.role}</p>
                  </div>
                  <Link 
                    to={`/agent/profile/${agent.name}`} 
                    className="text-primary hover:text-primary/80 transition-colors text-sm"
                  >
                    View Agent
                  </Link>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-muted-foreground">No AI solutions associated with this project.</p>
        )}
        
        {project.multi_agent_system && (
          <div className="mt-4 border-t border-border pt-4">
            <h3 className="font-medium text-foreground mb-2">Multi-Agent System</h3>
            <div className="bg-primary/5 border border-primary/20 rounded-lg p-4">
              <p className="text-sm text-muted-foreground mb-2">
                This project uses a multi-agent system for handling complex tasks.
              </p>
              <div>
                <h4 className="text-sm font-medium text-foreground">System ID:</h4>
                <p className="text-sm text-muted-foreground">{project.multi_agent_system.id}</p>
              </div>
              <div className="mt-2">
                <h4 className="text-sm font-medium text-foreground">Agents:</h4>
                <div className="flex flex-wrap gap-1 mt-1">
                  {project.multi_agent_system.agents.map((agentName, index) => (
                    <span 
                      key={index} 
                      className="text-xs bg-primary/15 text-primary-foreground dark:text-primary py-1 px-2 rounded-full"
                    >
                      {agentName}
                      {agentName === project.multi_agent_system.triage_agent && 
                        " (Triage)"}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
      
      {/* Recent Conversations Section */}
      <div className="bg-card text-card-foreground shadow-sm rounded-lg p-6 border border-border">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-lg font-semibold text-foreground">Recent Conversations</h2>
          <button
            onClick={runProject}
            className="text-primary hover:text-primary/80 transition-colors text-sm"
          >
            View All
          </button>
        </div>
        
        <div id="conversations-container" className="max-h-60 overflow-y-auto">
          {/* This will be populated with recent conversations once implemented */}
          <p className="text-muted-foreground text-center py-4">
            No recent conversations. Click "Run Project" to start chatting!
          </p>
        </div>
      </div>
    </div>
  );
};

export default ProjectDetail; 