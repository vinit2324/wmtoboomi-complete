import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import {
  Users,
  FolderOpen,
  GitCompare,
  Clock,
  ArrowRight,
  TrendingUp,
  CheckCircle,
  AlertCircle,
} from 'lucide-react';
import { customersApi, projectsApi, logsApi } from '../utils/api';
import { useStore } from '../stores/useStore';

export default function Dashboard() {
  const { currentCustomer } = useStore();

  const { data: customersData } = useQuery({
    queryKey: ['customers'],
    queryFn: async () => {
      const response = await customersApi.list();
      return response.data;
    },
  });

  const { data: projectsData } = useQuery({
    queryKey: ['projects', currentCustomer?.customerId],
    queryFn: async () => {
      const response = await projectsApi.list(currentCustomer?.customerId);
      return response.data;
    },
  });

  const { data: logsData } = useQuery({
    queryKey: ['logs', 'recent'],
    queryFn: async () => {
      const response = await logsApi.list({ limit: 5 });
      return response.data;
    },
  });

  const customers = customersData?.customers || [];
  const projects = projectsData?.projects || [];
  const logs = logsData?.logs || [];

  const stats = [
    {
      label: 'Customers',
      value: customers.length,
      icon: Users,
      color: 'bg-blue-500',
      link: '/customers',
    },
    {
      label: 'Projects',
      value: projects.length,
      icon: FolderOpen,
      color: 'bg-jade-500',
      link: '/projects',
    },
    {
      label: 'Parsed',
      value: projects.filter((p) => p.status === 'parsed' || p.status === 'analyzed').length,
      icon: CheckCircle,
      color: 'bg-green-500',
      link: '/projects',
    },
    {
      label: 'Pending',
      value: projects.filter((p) => p.status === 'uploaded' || p.status === 'parsing').length,
      icon: Clock,
      color: 'bg-yellow-500',
      link: '/projects',
    },
  ];

  return (
    <div className="space-y-6 animate-fadeIn">
      {/* Welcome Section */}
      <div className="card bg-gradient-to-r from-jade-500 to-jade-600 text-white">
        <h1 className="text-2xl font-bold mb-2">
          Welcome to the Migration Accelerator
        </h1>
        <p className="opacity-90">
          Automate 80-90% of your webMethods to Boomi migrations with our enterprise platform.
        </p>
        {!currentCustomer && (
          <div className="mt-4 bg-white/20 rounded-lg p-4">
            <p className="text-sm">
              👉 Select a customer from the sidebar or{' '}
              <Link to="/customers" className="underline font-medium">
                create a new customer
              </Link>{' '}
              to get started.
            </p>
          </div>
        )}
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {stats.map((stat) => (
          <Link
            key={stat.label}
            to={stat.link}
            className="card hover:shadow-md transition-shadow"
          >
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">{stat.label}</p>
                <p className="text-3xl font-bold mt-1">{stat.value}</p>
              </div>
              <div className={`p-3 rounded-lg ${stat.color}`}>
                <stat.icon className="w-6 h-6 text-white" />
              </div>
            </div>
          </Link>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Projects */}
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold">Recent Projects</h2>
            <Link
              to="/projects"
              className="text-jade-600 hover:text-jade-700 text-sm flex items-center"
            >
              View all <ArrowRight className="w-4 h-4 ml-1" />
            </Link>
          </div>
          {projects.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              <FolderOpen className="w-12 h-12 mx-auto mb-3 opacity-50" />
              <p>No projects yet</p>
              <p className="text-sm">Upload a webMethods package to get started</p>
            </div>
          ) : (
            <div className="space-y-3">
              {projects.slice(0, 5).map((project) => (
                <Link
                  key={project.projectId}
                  to={`/projects/${project.projectId}`}
                  className="flex items-center justify-between p-3 rounded-lg hover:bg-gray-50"
                >
                  <div className="flex items-center">
                    <FolderOpen className="w-5 h-5 text-jade-500 mr-3" />
                    <div>
                      <p className="font-medium">{project.packageName}</p>
                      <p className="text-sm text-gray-500">
                        {project.packageInfo?.services?.total || 0} services
                      </p>
                    </div>
                  </div>
                  <span
                    className={`badge ${
                      project.status === 'analyzed'
                        ? 'badge-success'
                        : project.status === 'failed'
                        ? 'badge-error'
                        : 'badge-info'
                    }`}
                  >
                    {project.status}
                  </span>
                </Link>
              ))}
            </div>
          )}
        </div>

        {/* Recent Activity */}
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold">Recent Activity</h2>
            <Link
              to="/logs"
              className="text-jade-600 hover:text-jade-700 text-sm flex items-center"
            >
              View all <ArrowRight className="w-4 h-4 ml-1" />
            </Link>
          </div>
          {logs.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              <Clock className="w-12 h-12 mx-auto mb-3 opacity-50" />
              <p>No activity yet</p>
              <p className="text-sm">Activity will appear as you use the platform</p>
            </div>
          ) : (
            <div className="space-y-3">
              {logs.map((log) => (
                <div
                  key={log.id}
                  className="flex items-start p-3 rounded-lg hover:bg-gray-50"
                >
                  <div
                    className={`p-2 rounded-lg mr-3 ${
                      log.level === 'error'
                        ? 'bg-red-100'
                        : log.level === 'warning'
                        ? 'bg-yellow-100'
                        : 'bg-jade-100'
                    }`}
                  >
                    {log.level === 'error' ? (
                      <AlertCircle className="w-4 h-4 text-red-600" />
                    ) : (
                      <CheckCircle className="w-4 h-4 text-jade-600" />
                    )}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium truncate">{log.action}</p>
                    <p className="text-xs text-gray-500 truncate">{log.message}</p>
                  </div>
                  <span className="text-xs text-gray-400 whitespace-nowrap ml-2">
                    {new Date(log.timestamp).toLocaleTimeString()}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Quick Actions */}
      <div className="card">
        <h2 className="text-lg font-semibold mb-4">Quick Actions</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Link
            to="/customers"
            className="p-4 border border-gray-200 rounded-lg hover:border-jade-500 hover:bg-jade-50 transition-colors"
          >
            <Users className="w-8 h-8 text-jade-500 mb-2" />
            <h3 className="font-medium">Manage Customers</h3>
            <p className="text-sm text-gray-500">
              Configure customer accounts and credentials
            </p>
          </Link>
          <Link
            to="/projects"
            className="p-4 border border-gray-200 rounded-lg hover:border-jade-500 hover:bg-jade-50 transition-colors"
          >
            <FolderOpen className="w-8 h-8 text-jade-500 mb-2" />
            <h3 className="font-medium">Upload Package</h3>
            <p className="text-sm text-gray-500">
              Upload a webMethods package for migration
            </p>
          </Link>
          <Link
            to="/ai"
            className="p-4 border border-gray-200 rounded-lg hover:border-jade-500 hover:bg-jade-50 transition-colors"
          >
            <TrendingUp className="w-8 h-8 text-jade-500 mb-2" />
            <h3 className="font-medium">AI Assistant</h3>
            <p className="text-sm text-gray-500">
              Get help with migration questions
            </p>
          </Link>
        </div>
      </div>
    </div>
  );
}
