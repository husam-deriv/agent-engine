import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Navbar from './components/Navbar';
import { useTheme } from './lib/ThemeProvider';

// Import existing pages
import Home from './pages/Home';
import CreateAgent from './pages/CreateAgent';
import ChatWithAgent from './pages/ChatWithAgent';
import MultiAgentBuilder from './pages/MultiAgentBuilder';
import MultiAgentChat from './pages/MultiAgentChat';
import ConversationHistory from './pages/ConversationHistory';
import CustomToolCreator from './components/CustomToolCreator';
import AgentProfile from './pages/AgentProfile';

// Import new Gargash AI Builder Platform pages
import Roadmap from './pages/Roadmap';
import NewProject from './pages/NewProject';
import AISolutions from './pages/AISolutions';
import ProjectDetail from './pages/ProjectDetail';
import ProjectChat from './pages/ProjectChat';
import FileUploadPage from './pages/FileUpload';

function App() {
  const { theme } = useTheme();

  return (
    <Router>
      <div className="min-h-screen bg-background text-foreground font-sans relative">
        <Navbar />
        <div className="pt-2">
          <Routes>
            {/* Redirect home to fileupload for testing */}
            <Route path="/" element={<FileUploadPage />} />
            
            {/* New Gargash AI Builder Platform routes */}
            <Route path="/roadmap" element={<Roadmap />} />
            <Route path="/projects/new" element={<NewProject />} />
            <Route path="/projects/:projectId" element={<ProjectDetail />} />
            <Route path="/projects/:projectId/chat" element={<ProjectChat />} />
            <Route path="/projects/:projectId/chat/:conversationId" element={<ProjectChat />} />
            <Route path="/ai-solutions" element={<AISolutions />} />
            <Route path="/fileupload" element={<FileUploadPage />} />
            
            {/* Existing routes but renamed for Gargash branding */}
            <Route path="/create-agent" element={<CreateAgent />} />
            <Route path="/chat/:agentName" element={<ChatWithAgent />} />
            <Route path="/multi-agent/create" element={<MultiAgentBuilder />} />
            <Route path="/multi-agent/:systemId" element={<MultiAgentChat />} />
            <Route path="/agents/:agentName/history" element={<ConversationHistory />} />
            <Route path="/custom-tools" element={<CustomToolCreator />} />
            <Route path="/agent/profile/:agentName" element={<AgentProfile />} />
          </Routes>
        </div>
      </div>
    </Router>
  );
}

export default App;