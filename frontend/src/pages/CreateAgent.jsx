import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import AgentForm from '../components/AgentForm';
import axios from 'axios';
import { API_URL } from '../config';

const CreateAgent = () => {
  const navigate = useNavigate();
  const [error, setError] = useState('');

  const handleSubmit = async (formData) => {
    try {
      const response = await axios.post(`${API_URL}/create_agent/`, formData);
      
      // Redirect to dashboard on success
      navigate('/');
    } catch (error) {
      console.error('Error creating agent:', error);
      setError(error.response?.data?.detail || 'Failed to create agent');
      throw error;
    }
  };

  const handleCancel = () => {
    // Redirect back to dashboard
    navigate('/');
  };

  return (
    <div className="container mx-auto p-4">
      <div className="mb-8 relative">
        <div className="absolute -left-4 top-0 bottom-0 w-1 bg-gradient-to-b from-omnitrix to-omnitrix-dark rounded-full"></div>
        <h1 className="text-3xl font-bold bg-gradient-to-r from-omnitrix to-omnitrix-light bg-clip-text text-transparent mb-2">Create New Agent</h1>
        <p className="text-gray-400">Define your agent's abilities, personality, and powers</p>
      </div>
      
      {error && (
        <div className="mb-4 p-3 bg-red-900 bg-opacity-50 border border-red-700 rounded text-red-300">
          {error}
        </div>
      )}
      
      <div className="bg-ben10-black rounded-xl border border-omnitrix-dark shadow-omnitrix p-6">
        <AgentForm onSubmit={handleSubmit} onCancel={handleCancel} />
      </div>
    </div>
  );
};

export default CreateAgent; 