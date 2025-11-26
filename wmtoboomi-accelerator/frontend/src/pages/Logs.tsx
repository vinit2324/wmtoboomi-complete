import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  FileText,
  Search,
  Filter,
  RefreshCw,
  AlertCircle,
  CheckCircle,
  Info,
  AlertTriangle,
} from 'lucide-react';
import { logsApi } from '../utils/api';
import { useStore } from '../stores/useStore';
import type { LogEntry } from '../types';

export default function Logs() {
  const { currentCustomer } = useStore();
  const [filters, setFilters] = useState({
    level: '',
    category: '',
    search: '',
  });

  const { data, isLoading, refetch } = useQuery({
    queryKey: ['logs', currentCustomer?.customerId, filters],
    queryFn: async () => {
      const response = await logsApi.list({
        customerId: currentCustomer?.customerId,
        level: filters.level || undefined,
        category: filters.category || undefined,
        limit: 100,
      });
      return response.data;
    },
  });

  const logs = data?.logs || [];

  const getLevelIcon = (level: string) => {
    switch (level) {
      case 'error':
        return <AlertCircle className="w-4 h-4 text-red-500" />;
      case 'warning':
        return <AlertTriangle className="w-4 h-4 text-yellow-500" />;
      case 'info':
        return <Info className="w-4 h-4 text-blue-500" />;
      default:
        return <CheckCircle className="w-4 h-4 text-gray-400" />;
    }
  };

  const getLevelBadge = (level: string) => {
    switch (level) {
      case 'error':
        return 'badge-error';
      case 'warning':
        return 'badge-warning';
      case 'info':
        return 'badge-info';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getCategoryBadge = (category: string) => {
    const colors: Record<string, string> = {
      upload: 'bg-blue-100 text-blue-800',
      parse: 'bg-purple-100 text-purple-800',
      analyze: 'bg-indigo-100 text-indigo-800',
      convert: 'bg-jade-100 text-jade-800',
      validate: 'bg-yellow-100 text-yellow-800',
      push: 'bg-green-100 text-green-800',
      ai: 'bg-pink-100 text-pink-800',
      system: 'bg-gray-100 text-gray-800',
    };
    return colors[category] || 'bg-gray-100 text-gray-800';
  };

  const filteredLogs = logs.filter((log: LogEntry) => {
    if (filters.search) {
      const searchLower = filters.search.toLowerCase();
      return (
        log.action.toLowerCase().includes(searchLower) ||
        log.message.toLowerCase().includes(searchLower)
      );
    }
    return true;
  });

  return (
    <div className="space-y-6 animate-fadeIn">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Activity Logs</h1>
          <p className="text-gray-500">Track all system activities and events</p>
        </div>
        <button
          onClick={() => refetch()}
          className="btn-secondary flex items-center"
        >
          <RefreshCw className="w-4 h-4 mr-2" />
          Refresh
        </button>
      </div>

      {/* Filters */}
      <div className="card">
        <div className="flex items-center gap-4">
          <div className="flex-1 relative">
            <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
            <input
              type="text"
              placeholder="Search logs..."
              className="input pl-9"
              value={filters.search}
              onChange={(e) => setFilters({ ...filters, search: e.target.value })}
            />
          </div>
          <select
            className="input w-40"
            value={filters.level}
            onChange={(e) => setFilters({ ...filters, level: e.target.value })}
          >
            <option value="">All Levels</option>
            <option value="debug">Debug</option>
            <option value="info">Info</option>
            <option value="warning">Warning</option>
            <option value="error">Error</option>
          </select>
          <select
            className="input w-40"
            value={filters.category}
            onChange={(e) => setFilters({ ...filters, category: e.target.value })}
          >
            <option value="">All Categories</option>
            <option value="upload">Upload</option>
            <option value="parse">Parse</option>
            <option value="analyze">Analyze</option>
            <option value="convert">Convert</option>
            <option value="validate">Validate</option>
            <option value="push">Push</option>
            <option value="ai">AI</option>
            <option value="system">System</option>
          </select>
        </div>
      </div>

      {/* Logs Table */}
      <div className="card overflow-hidden">
        {isLoading ? (
          <div className="flex items-center justify-center py-12">
            <RefreshCw className="w-8 h-8 animate-spin text-jade-500" />
          </div>
        ) : filteredLogs.length === 0 ? (
          <div className="text-center py-12">
            <FileText className="w-16 h-16 mx-auto text-gray-300 mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">No logs found</h3>
            <p className="text-gray-500">
              {filters.search || filters.level || filters.category
                ? 'Try adjusting your filters'
                : 'Activity logs will appear as you use the platform'}
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50">
                <tr>
                  <th className="text-left py-3 px-4 text-sm font-medium text-gray-500">
                    Timestamp
                  </th>
                  <th className="text-left py-3 px-4 text-sm font-medium text-gray-500">
                    Level
                  </th>
                  <th className="text-left py-3 px-4 text-sm font-medium text-gray-500">
                    Category
                  </th>
                  <th className="text-left py-3 px-4 text-sm font-medium text-gray-500">
                    Action
                  </th>
                  <th className="text-left py-3 px-4 text-sm font-medium text-gray-500">
                    Message
                  </th>
                </tr>
              </thead>
              <tbody>
                {filteredLogs.map((log: LogEntry) => (
                  <tr
                    key={log.id}
                    className="border-t border-gray-100 hover:bg-gray-50"
                  >
                    <td className="py-3 px-4 text-sm text-gray-500 whitespace-nowrap">
                      {new Date(log.timestamp).toLocaleString()}
                    </td>
                    <td className="py-3 px-4">
                      <span className={`badge ${getLevelBadge(log.level)}`}>
                        {log.level}
                      </span>
                    </td>
                    <td className="py-3 px-4">
                      <span className={`badge ${getCategoryBadge(log.category)}`}>
                        {log.category}
                      </span>
                    </td>
                    <td className="py-3 px-4 font-medium text-sm">
                      {log.action}
                    </td>
                    <td className="py-3 px-4 text-sm text-gray-600 max-w-md truncate">
                      {log.message}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Log Count */}
      <div className="text-sm text-gray-500 text-center">
        Showing {filteredLogs.length} of {logs.length} logs
      </div>
    </div>
  );
}
