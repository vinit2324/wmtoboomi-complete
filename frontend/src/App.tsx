import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { ToastProvider } from './components/Toast';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import Customers from './pages/Customers';
import Projects from './pages/Projects';
import ProjectDetail from './pages/ProjectDetail';
import Integrations from './pages/Integrations';
import IntegrationImplementation from './pages/IntegrationImplementation';
import AIAssistant from './pages/AIAssistant';
import ActivityLogs from './pages/ActivityLogs';

function App() {
  return (
    <ToastProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Layout />}>
            <Route index element={<Navigate to="/dashboard" replace />} />
            <Route path="dashboard" element={<Dashboard />} />
            <Route path="customers" element={<Customers />} />
            <Route path="projects" element={<Projects />} />
            <Route path="projects/:projectId" element={<ProjectDetail />} />
            <Route path="projects/:projectId/integrations" element={<Integrations />} />
            <Route path="projects/:projectId/integrations/:integrationName" element={<IntegrationImplementation />} />
            <Route path="ai" element={<AIAssistant />} />
            <Route path="logs" element={<ActivityLogs />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </ToastProvider>
  );
}

export default App;
