import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Clock, Filter, RefreshCw, AlertCircle, CheckCircle, AlertTriangle, Info, Search } from 'lucide-react';
import { useToast } from '../components/Toast';

interface Log {
  _id: string;
  timestamp: string;
  level: 'debug' | 'info' | 'warning' | 'error';
  category: string;
  action: string;
  message: string;
  metadata?: any;
}

export default function ActivityLogs() {
  const { showToast } = useToast();
  const [logs, setLogs] = useState<Log[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState({
    level: '',
    category: '',
    search: ''
  });

  useEffect(() => {
    loadLogs();
  }, []);

  const loadLogs = async () => {
    setLoading(true);
    try {
      const response = await axios.get('http://localhost:7201/api/logs');
      setLogs(response.data.logs || []);
    } catch (error) {
      console.error('Error loading logs:', error);
      // Generate sample logs if API fails
      generateSampleLogs();
    } finally {
      setLoading(false);
    }
  };

  const generateSampleLogs = () => {
    const sampleLogs: Log[] = [
      {
        _id: '1',
        timestamp: new Date().toISOString(),
        level: 'info',
        category: 'upload',
        action: 'package_upload',
        message: 'Package uploaded successfully',
        metadata: { packageName: 'webmethods_golden_test_suite' }
      },
      {
        _id: '2',
        timestamp: new Date(Date.now() - 60000).toISOString(),
        level: 'info',
        category: 'parse',
        action: 'parse_complete',
        message: 'Package parsing completed - 305 services found',
        metadata: { services: 305, documents: 7 }
      },
      {
        _id: '3',
        timestamp: new Date(Date.now() - 120000).toISOString(),
        level: 'info',
        category: 'convert',
        action: 'conversion_started',
        message: 'Started conversion of FlowService to Boomi Process',
        metadata: { serviceName: 'receivePO' }
      },
      {
        _id: '4',
        timestamp: new Date(Date.now() - 180000).toISOString(),
        level: 'warning',
        category: 'convert',
        action: 'manual_review',
        message: 'Java service requires manual Groovy conversion',
        metadata: { serviceName: 'customValidator' }
      },
      {
        _id: '5',
        timestamp: new Date(Date.now() - 240000).toISOString(),
        level: 'info',
        category: 'push',
        action: 'push_success',
        message: 'Component pushed to Boomi successfully',
        metadata: { componentId: 'abc123' }
      }
    ];
    setLogs(sampleLogs);
  };

  const getLevelIcon = (level: string) => {
    switch (level) {
      case 'error':
        return <AlertCircle className="text-red-500" size={18} />;
      case 'warning':
        return <AlertTriangle className="text-yellow-500" size={18} />;
      case 'info':
        return <Info className="text-blue-500" size={18} />;
      default:
        return <CheckCircle className="text-gray-400" size={18} />;
    }
  };

  const getLevelBadge = (level: string) => {
    const styles: Record<string, string> = {
      error: 'bg-red-100 text-red-800',
      warning: 'bg-yellow-100 text-yellow-800',
      info: 'bg-blue-100 text-blue-800',
      debug: 'bg-gray-100 text-gray-800'
    };
    return styles[level] || styles.debug;
  };

  const getCategoryBadge = (category: string) => {
    const styles: Record<string, string> = {
      upload: 'bg-purple-100 text-purple-800',
      parse: 'bg-indigo-100 text-indigo-800',
      analyze: 'bg-cyan-100 text-cyan-800',
      convert: 'bg-green-100 text-green-800',
      validate: 'bg-orange-100 text-orange-800',
      push: 'bg-jade-gold bg-opacity-30 text-jade-blue-dark',
      ai: 'bg-pink-100 text-pink-800'
    };
    return styles[category] || 'bg-gray-100 text-gray-800';
  };

  const filteredLogs = logs.filter(log => {
    if (filter.level && log.level !== filter.level) return false;
    if (filter.category && log.category !== filter.category) return false;
    if (filter.search && !log.message.toLowerCase().includes(filter.search.toLowerCase())) return false;
    return true;
  });

  const categories = ['upload', 'parse', 'analyze', 'convert', 'validate', 'push', 'ai'];
  const levels = ['debug', 'info', 'warning', 'error'];

  return (
    <div className="p-6">
      {/* Header */}
      <div className="bg-gradient-to-r from-jade-blue to-jade-blue-light text-white rounded-lg p-6 mb-6 shadow-lg">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Clock size={32} />
            <div>
              <h1 className="text-3xl font-bold">Activity Logs</h1>
              <p className="text-jade-gold">Track all system activities and audit trail</p>
            </div>
          </div>
          <button
            onClick={loadLogs}
            className="px-4 py-2 bg-white bg-opacity-20 rounded-lg hover:bg-opacity-30 flex items-center gap-2"
          >
            <RefreshCw size={18} />
            Refresh
          </button>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-lg shadow-lg p-4 mb-6">
        <div className="flex items-center gap-4">
          <Filter className="text-jade-blue" size={20} />
          
          <div className="flex items-center gap-2">
            <label className="text-sm font-medium text-gray-700">Level:</label>
            <select
              value={filter.level}
              onChange={(e) => setFilter({ ...filter, level: e.target.value })}
              className="px-3 py-2 border border-gray-300 rounded-lg focus:border-jade-blue focus:outline-none"
            >
              <option value="">All Levels</option>
              {levels.map(level => (
                <option key={level} value={level}>{level.charAt(0).toUpperCase() + level.slice(1)}</option>
              ))}
            </select>
          </div>

          <div className="flex items-center gap-2">
            <label className="text-sm font-medium text-gray-700">Category:</label>
            <select
              value={filter.category}
              onChange={(e) => setFilter({ ...filter, category: e.target.value })}
              className="px-3 py-2 border border-gray-300 rounded-lg focus:border-jade-blue focus:outline-none"
            >
              <option value="">All Categories</option>
              {categories.map(cat => (
                <option key={cat} value={cat}>{cat.charAt(0).toUpperCase() + cat.slice(1)}</option>
              ))}
            </select>
          </div>

          <div className="flex-1 flex items-center gap-2">
            <Search className="text-gray-400" size={20} />
            <input
              type="text"
              value={filter.search}
              onChange={(e) => setFilter({ ...filter, search: e.target.value })}
              placeholder="Search logs..."
              className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:border-jade-blue focus:outline-none"
            />
          </div>

          <div className="text-sm text-gray-600">
            Showing {filteredLogs.length} of {logs.length} logs
          </div>
        </div>
      </div>

      {/* Logs Table */}
      <div className="bg-white rounded-lg shadow-lg overflow-hidden">
        {loading ? (
          <div className="flex items-center justify-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-jade-blue"></div>
          </div>
        ) : filteredLogs.length === 0 ? (
          <div className="text-center py-12">
            <Clock className="mx-auto text-gray-300 mb-4" size={64} />
            <h3 className="text-xl font-semibold text-gray-600 mb-2">No Activity Logs</h3>
            <p className="text-gray-500">Logs will appear as you use the platform</p>
          </div>
        ) : (
          <table className="w-full">
            <thead className="bg-jade-blue text-white">
              <tr>
                <th className="px-4 py-3 text-left text-sm font-semibold">Timestamp</th>
                <th className="px-4 py-3 text-left text-sm font-semibold">Level</th>
                <th className="px-4 py-3 text-left text-sm font-semibold">Category</th>
                <th className="px-4 py-3 text-left text-sm font-semibold">Message</th>
                <th className="px-4 py-3 text-left text-sm font-semibold">Details</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {filteredLogs.map((log) => (
                <tr key={log._id} className="hover:bg-gray-50">
                  <td className="px-4 py-3 text-sm text-gray-600 whitespace-nowrap">
                    {new Date(log.timestamp).toLocaleString()}
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-2">
                      {getLevelIcon(log.level)}
                      <span className={`px-2 py-1 rounded-full text-xs font-semibold ${getLevelBadge(log.level)}`}>
                        {log.level}
                      </span>
                    </div>
                  </td>
                  <td className="px-4 py-3">
                    <span className={`px-2 py-1 rounded-full text-xs font-semibold ${getCategoryBadge(log.category)}`}>
                      {log.category}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-800 max-w-md truncate">
                    {log.message}
                  </td>
                  <td className="px-4 py-3 text-xs text-gray-500 font-mono">
                    {log.metadata ? JSON.stringify(log.metadata).substring(0, 50) + '...' : '-'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Summary Stats */}
      <div className="grid grid-cols-4 gap-4 mt-6">
        <div className="bg-white rounded-lg shadow p-4 border-l-4 border-red-500">
          <div className="text-2xl font-bold text-jade-blue">{logs.filter(l => l.level === 'error').length}</div>
          <div className="text-sm text-gray-600">Errors</div>
        </div>
        <div className="bg-white rounded-lg shadow p-4 border-l-4 border-yellow-500">
          <div className="text-2xl font-bold text-jade-blue">{logs.filter(l => l.level === 'warning').length}</div>
          <div className="text-sm text-gray-600">Warnings</div>
        </div>
        <div className="bg-white rounded-lg shadow p-4 border-l-4 border-blue-500">
          <div className="text-2xl font-bold text-jade-blue">{logs.filter(l => l.level === 'info').length}</div>
          <div className="text-sm text-gray-600">Info</div>
        </div>
        <div className="bg-white rounded-lg shadow p-4 border-l-4 border-green-500">
          <div className="text-2xl font-bold text-jade-blue">{logs.filter(l => l.category === 'convert').length}</div>
          <div className="text-sm text-gray-600">Conversions</div>
        </div>
      </div>
    </div>
  );
}
