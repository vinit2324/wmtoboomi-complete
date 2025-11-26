import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import Customers from './pages/Customers';
import Projects from './pages/Projects';
import ProjectDetail from './pages/ProjectDetail';
import DocumentViewer from './pages/DocumentViewer';
import Conversions from './pages/Conversions';
import Analysis from './pages/Analysis';
import AIAssistant from './pages/AIAssistant';
import Logs from './pages/Logs';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Dashboard />} />
          <Route path="customers" element={<Customers />} />
          <Route path="projects" element={<Projects />} />
          <Route path="projects/:projectId" element={<ProjectDetail />} />
          <Route path="projects/:projectId/files" element={<DocumentViewer />} />
          <Route path="projects/:projectId/analysis" element={<Analysis />} />
          <Route path="projects/:projectId/conversions" element={<Conversions />} />
          <Route path="ai" element={<AIAssistant />} />
          <Route path="logs" element={<Logs />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
