import React, { useState, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import axios from 'axios';

const API_URL = 'http://localhost:8000';

// Project card component
const ProjectCard = ({ project }) => {
  // Format date from ISO to MMM-DD format
  const formatDate = (dateString) => {
    if (!dateString) return 'No date';
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { 
      year: 'numeric',
      month: '2-digit',
      day: '2-digit'
    });
  };

  return (
    <Link to={`/projects/${project.id}`} className="block">
      <div className="bg-card text-card-foreground p-4 rounded-lg border border-border hover:shadow-md transition-shadow duration-200">
        <h3 className="font-medium text-foreground mb-1">{project.title}</h3>
        <p className="text-sm text-muted-foreground mb-3">Goal: {project.goal}</p>
        
        <div className="flex justify-between items-center mb-3">
          <div className="text-xs text-muted-foreground">Target: {formatDate(project.target_date)}</div>
        </div>

        <div className="mt-3 flex justify-end">
          <button 
            className="text-xs bg-[#c2161f] text-white px-3 py-1.5 rounded-md hover:bg-[#c2161f]/90 flex items-center transition-colors"
            onClick={(e) => {
              e.preventDefault(); // Prevent the Link from activating
              window.location.href = `/projects/${project.id}/chat`;
            }}
          >
            <svg xmlns="http://www.w3.org/2000/svg" className="h-3 w-3 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            Run
          </button>
        </div>
      </div>
    </Link>
  );
};

// Department column component
const DepartmentColumn = ({ department, projects }) => {
  return (
    <div className="flex-1 min-w-[250px]">
      <div className="border-b border-border pb-2 mb-4">
        <h2 className="font-semibold text-foreground">{department.name}</h2>
        <p className="text-sm text-muted-foreground">{department.project_count} projects</p>
      </div>
      
      <div className="space-y-3">
        {projects.map(project => (
          <ProjectCard key={project.id} project={project} />
        ))}
      </div>
    </div>
  );
};

const Roadmap = () => {
  const [roadmapData, setRoadmapData] = useState({});
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [retryCount, setRetryCount] = useState(0);
  const [successMessage, setSuccessMessage] = useState('');
  
  const location = useLocation();

  useEffect(() => {
    // Check for success message in navigation state
    if (location.state && location.state.message) {
      setSuccessMessage(location.state.message);
      // Clear the message from location state after 5 seconds
      const timer = setTimeout(() => {
        setSuccessMessage('');
        window.history.replaceState({}, document.title);
      }, 5000);
      return () => clearTimeout(timer);
    }
  }, [location]);

  useEffect(() => {
    const fetchRoadmap = async () => {
      setIsLoading(true);
      try {
        console.log('Fetching roadmap data from:', `${API_URL}/roadmap`);
        const response = await axios.get(`${API_URL}/roadmap`);
        console.log('Roadmap API response:', response.data);
        setRoadmapData(response.data);
        setError(null);
      } catch (err) {
        console.error('Error fetching roadmap:', err);
        setError(`Failed to load roadmap data. ${err.message}`);
      } finally {
        setIsLoading(false);
      }
    };

    fetchRoadmap();
  }, [retryCount]);

  const handleRetry = () => {
    setRetryCount(prevCount => prevCount + 1);
  };

  if (isLoading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-[#c2161f]"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="container mx-auto py-6 px-4">
        <div className="bg-destructive/10 border border-destructive/30 text-destructive px-4 py-3 rounded relative mb-6" role="alert">
          <strong className="font-bold">Error:</strong>
          <span className="block sm:inline ml-1">{error}</span>
          <div className="mt-3">
            <button 
              onClick={handleRetry}
              className="bg-destructive hover:bg-destructive/90 text-destructive-foreground py-1 px-3 rounded text-sm"
            >
              Retry
            </button>
            <span className="text-xs text-muted-foreground ml-3">
              Make sure the backend server is running at {API_URL}
            </span>
          </div>
        </div>
        
        <div className="flex justify-between items-center mb-8">
          <h1 className="text-2xl font-bold text-foreground">AI Product Roadmap</h1>
          <Link 
            to="/projects/new" 
            className="bg-[#c2161f] hover:bg-[#c2161f]/90 text-white py-2 px-4 rounded-md flex items-center transition-colors duration-200"
          >
            <svg className="w-5 h-5 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6"></path>
            </svg>
            Add New Project
          </Link>
        </div>
      </div>
    );
  }

  // Check if roadmapData is valid
  if (!roadmapData || Object.keys(roadmapData).length === 0) {
    return (
      <div className="container mx-auto py-6 px-4">
        <div className="bg-yellow-500/10 border border-yellow-500/30 text-yellow-700 dark:text-yellow-500 px-4 py-3 rounded relative mb-6" role="alert">
          <strong className="font-bold">No data:</strong>
          <span className="block sm:inline ml-1">No roadmap data available yet. Try adding a project.</span>
        </div>
        
        <div className="flex justify-between items-center mb-8">
          <h1 className="text-2xl font-bold text-foreground">AI Product Roadmap</h1>
          <Link 
            to="/projects/new" 
            className="bg-[#c2161f] hover:bg-[#c2161f]/90 text-white py-2 px-4 rounded-md flex items-center transition-colors duration-200"
          >
            <svg className="w-5 h-5 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6"></path>
            </svg>
            Add New Project
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8 max-w-6xl">
      <div className="text-center mb-12">
        <h1 className="text-4xl font-bold mb-3">Gargash AI Solution Roadmap</h1>
        <p className="text-lg text-zinc-600 dark:text-zinc-400 max-w-3xl mx-auto mb-6">
          Track the progress of our AI projects and solutions, from planning to deployment.
        </p>
        <div className="flex justify-center gap-4 mb-6">
          <Link to="/fileupload" className="inline-flex items-center px-4 py-2 rounded-lg bg-[#c2161f] text-white hover:bg-[#c2161f]/90 transition-colors">
            Go to File Upload
          </Link>
          <Link 
            to="/projects/new" 
            className="bg-[#c2161f] hover:bg-[#c2161f]/90 text-white py-2 px-4 rounded-md flex items-center transition-colors duration-200"
          >
            <svg className="w-5 h-5 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6"></path>
            </svg>
            Add New Project
          </Link>
        </div>
      </div>
      
      {successMessage && (
        <div className="bg-green-500/10 border border-green-500/30 text-green-700 dark:text-green-500 px-4 py-3 rounded mb-6 flex justify-between items-center">
          <span>{successMessage}</span>
          <button 
            onClick={() => setSuccessMessage('')}
            className="text-green-700 dark:text-green-500 hover:text-green-900 dark:hover:text-green-400"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12"></path>
            </svg>
          </button>
        </div>
      )}
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {Object.entries(roadmapData).map(([deptName, deptData]) => (
          <DepartmentColumn 
            key={deptName} 
            department={deptData} 
            projects={deptData.projects || []} 
          />
        ))}
      </div>
    </div>
  );
};

export default Roadmap; 