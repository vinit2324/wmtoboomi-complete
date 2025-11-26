import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { Users, Package, CheckCircle, Clock, ArrowRight, FileCode, Zap } from 'lucide-react';

export default function Dashboard() {
  const navigate = useNavigate();
  const [stats, setStats] = useState({
    customers: 0,
    projects: 0,
    parsed: 0,
    pending: 0
  });
  const [recentProjects, setRecentProjects] = useState<any[]>([]);
  const [recentLogs, setRecentLogs] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      const [customersRes, projectsRes, logsRes] = await Promise.all([
        axios.get('http://localhost:7201/api/customers'),
        axios.get('http://localhost:7201/api/projects'),
        axios.get('http://localhost:7201/api/logs').catch(() => ({ data: { logs: [] } }))
      ]);

      const customers = customersRes.data.customers || [];
      const projects = projectsRes.data.projects || [];
      const logs = logsRes.data.logs || [];

      const parsedCount = projects.filter((p: any) => p.status === 'parsed').length;
      const pendingCount = projects.filter((p: any) => p.status !== 'parsed').length;

      setStats({
        customers: customers.length,
        projects: projects.length,
        parsed: parsedCount,
        pending: pendingCount
      });

      setRecentProjects(projects.slice(0, 5));
      setRecentLogs(logs.slice(0, 5));

    } catch (error) {
      console.error('Error loading dashboard:', error);
    } finally {
      setLoading(false);
    }
  };

  const getStatusBadge = (status: string) => {
    const styles: Record<string, string> = {
      parsed: 'bg-green-100 text-green-800',
      parsing: 'bg-yellow-100 text-yellow-800',
      failed: 'bg-red-100 text-red-800',
      uploaded: 'bg-blue-100 text-blue-800'
    };
    return styles[status] || 'bg-gray-100 text-gray-800';
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-jade-blue"></div>
      </div>
    );
  }

  return (
    <div className="p-6">
      {/* Hero Banner */}
      <div className="bg-gradient-to-r from-jade-blue to-jade-blue-light text-white rounded-lg p-8 mb-6 shadow-lg">
        <h1 className="text-3xl font-bold mb-2">Welcome to the Migration Accelerator</h1>
        <p className="text-jade-gold text-lg">
          Automate 80-90% of your webMethods to Boomi migrations with our enterprise platform.
        </p>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-4 gap-6 mb-6">
        <div 
          className="bg-white rounded-lg shadow-lg p-6 border-l-4 border-jade-blue cursor-pointer hover:shadow-xl transition-shadow"
          onClick={() => navigate('/customers')}
        >
          <div className="flex items-center justify-between mb-4">
            <Users className="text-jade-blue" size={32} />
            <ArrowRight className="text-gray-400" size={20} />
          </div>
          <div className="text-3xl font-bold text-jade-blue">{stats.customers}</div>
          <div className="text-gray-600 font-medium">Customers</div>
        </div>

        <div 
          className="bg-white rounded-lg shadow-lg p-6 border-l-4 border-jade-gold cursor-pointer hover:shadow-xl transition-shadow"
          onClick={() => navigate('/projects')}
        >
          <div className="flex items-center justify-between mb-4">
            <Package className="text-jade-gold" size={32} />
            <ArrowRight className="text-gray-400" size={20} />
          </div>
          <div className="text-3xl font-bold text-jade-blue">{stats.projects}</div>
          <div className="text-gray-600 font-medium">Projects</div>
        </div>

        <div className="bg-white rounded-lg shadow-lg p-6 border-l-4 border-green-500">
          <div className="flex items-center justify-between mb-4">
            <CheckCircle className="text-green-500" size={32} />
          </div>
          <div className="text-3xl font-bold text-jade-blue">{stats.parsed}</div>
          <div className="text-gray-600 font-medium">Parsed</div>
        </div>

        <div className="bg-white rounded-lg shadow-lg p-6 border-l-4 border-orange-500">
          <div className="flex items-center justify-between mb-4">
            <Clock className="text-orange-500" size={32} />
          </div>
          <div className="text-3xl font-bold text-jade-blue">{stats.pending}</div>
          <div className="text-gray-600 font-medium">Pending</div>
        </div>
      </div>

      {/* Two Column Layout */}
      <div className="grid grid-cols-2 gap-6">
        {/* Recent Projects */}
        <div className="bg-white rounded-lg shadow-lg">
          <div className="p-6 border-b border-gray-200 flex items-center justify-between">
            <h2 className="text-xl font-bold text-jade-blue">Recent Projects</h2>
            <button 
              onClick={() => navigate('/projects')}
              className="text-sm text-jade-blue hover:underline flex items-center gap-1"
            >
              View All <ArrowRight size={16} />
            </button>
          </div>
          <div className="p-4">
            {recentProjects.length === 0 ? (
              <div className="text-center py-8">
                <Package className="mx-auto text-gray-300 mb-3" size={48} />
                <p className="text-gray-500">No projects yet</p>
                <button 
                  onClick={() => navigate('/projects')}
                  className="mt-3 text-jade-blue hover:underline text-sm"
                >
                  Upload your first package →
                </button>
              </div>
            ) : (
              <div className="space-y-3">
                {recentProjects.map((project) => (
                  <div 
                    key={project.projectId}
                    className="flex items-center justify-between p-3 border rounded-lg hover:bg-jade-gray cursor-pointer transition-colors"
                    onClick={() => navigate(`/projects/${project.projectId}`)}
                  >
                    <div className="flex items-center gap-3">
                      <FileCode className="text-jade-blue" size={24} />
                      <div>
                        <div className="font-semibold text-jade-blue">{project.packageName}</div>
                        <div className="text-xs text-gray-500">
                          {new Date(project.uploadedAt).toLocaleDateString()} • {project.packageInfo?.services?.total || 0} services
                        </div>
                      </div>
                    </div>
                    <span className={`px-2 py-1 rounded-full text-xs font-semibold ${getStatusBadge(project.status)}`}>
                      {project.status}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Recent Activity */}
        <div className="bg-white rounded-lg shadow-lg">
          <div className="p-6 border-b border-gray-200 flex items-center justify-between">
            <h2 className="text-xl font-bold text-jade-blue">Recent Activity</h2>
            <button 
              onClick={() => navigate('/logs')}
              className="text-sm text-jade-blue hover:underline flex items-center gap-1"
            >
              View All <ArrowRight size={16} />
            </button>
          </div>
          <div className="p-4">
            {recentLogs.length === 0 ? (
              <div className="text-center py-8">
                <Zap className="mx-auto text-gray-300 mb-3" size={48} />
                <p className="text-gray-500">No activity yet</p>
                <p className="text-gray-400 text-sm mt-1">Activity will appear as you use the platform</p>
              </div>
            ) : (
              <div className="space-y-3">
                {recentLogs.map((log, idx) => (
                  <div key={idx} className="flex items-start gap-3 p-3 border rounded-lg">
                    <div className={`w-2 h-2 rounded-full mt-2 ${
                      log.level === 'error' ? 'bg-red-500' :
                      log.level === 'warning' ? 'bg-yellow-500' : 'bg-green-500'
                    }`} />
                    <div>
                      <div className="text-sm text-gray-800">{log.message}</div>
                      <div className="text-xs text-gray-500">
                        {new Date(log.timestamp).toLocaleString()} • {log.category}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="mt-6 bg-white rounded-lg shadow-lg p-6">
        <h2 className="text-xl font-bold text-jade-blue mb-4">Quick Actions</h2>
        <div className="grid grid-cols-4 gap-4">
          <button
            onClick={() => navigate('/customers')}
            className="p-4 border-2 border-jade-blue rounded-lg hover:bg-jade-blue hover:text-white transition-colors text-jade-blue font-semibold flex flex-col items-center gap-2"
          >
            <Users size={24} />
            Add Customer
          </button>
          <button
            onClick={() => navigate('/projects')}
            className="p-4 border-2 border-jade-gold rounded-lg hover:bg-jade-gold hover:text-jade-blue-dark transition-colors text-jade-blue font-semibold flex flex-col items-center gap-2"
          >
            <Package size={24} />
            Upload Package
          </button>
          <button
            onClick={() => navigate('/ai')}
            className="p-4 border-2 border-purple-500 rounded-lg hover:bg-purple-500 hover:text-white transition-colors text-purple-600 font-semibold flex flex-col items-center gap-2"
          >
            <Zap size={24} />
            AI Assistant
          </button>
          <button
            onClick={() => navigate('/logs')}
            className="p-4 border-2 border-gray-400 rounded-lg hover:bg-gray-500 hover:text-white transition-colors text-gray-600 font-semibold flex flex-col items-center gap-2"
          >
            <Clock size={24} />
            View Logs
          </button>
        </div>
      </div>
    </div>
  );
}
