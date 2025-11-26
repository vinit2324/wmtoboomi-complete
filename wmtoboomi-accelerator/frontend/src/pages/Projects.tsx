import { useState, useCallback } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { useDropzone } from 'react-dropzone';
import {
  FolderOpen,
  Upload,
  Trash2,
  Loader2,
  FileArchive,
  Play,
  BarChart3,
  FileCode,
  GitCompare,
  AlertCircle,
} from 'lucide-react';
import { projectsApi } from '../utils/api';
import { useStore } from '../stores/useStore';
import type { Project } from '../types';

export default function Projects() {
  const queryClient = useQueryClient();
  const { currentCustomer } = useStore();
  const [uploading, setUploading] = useState(false);

  const { data, isLoading } = useQuery({
    queryKey: ['projects', currentCustomer?.customerId],
    queryFn: async () => {
      const response = await projectsApi.list(currentCustomer?.customerId);
      return response.data;
    },
    enabled: !!currentCustomer,
  });

  const uploadMutation = useMutation({
    mutationFn: async (file: File) => {
      if (!currentCustomer) throw new Error('No customer selected');
      return projectsApi.upload(currentCustomer.customerId, file);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projects'] });
      setUploading(false);
    },
    onError: () => {
      setUploading(false);
    },
  });

  const parseMutation = useMutation({
    mutationFn: (id: string) => projectsApi.parse(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projects'] });
    },
  });

  const analyzeMutation = useMutation({
    mutationFn: (id: string) => projectsApi.analyze(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projects'] });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => projectsApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projects'] });
    },
  });

  const onDrop = useCallback(
    (acceptedFiles: File[]) => {
      const file = acceptedFiles[0];
      if (file && file.name.endsWith('.zip')) {
        setUploading(true);
        uploadMutation.mutate(file);
      }
    },
    [uploadMutation]
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'application/zip': ['.zip'] },
    maxFiles: 1,
    disabled: !currentCustomer || uploading,
  });

  const projects = data?.projects || [];

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'analyzed':
        return 'badge-success';
      case 'parsed':
        return 'badge-jade';
      case 'parsing':
      case 'analyzing':
        return 'badge-info';
      case 'failed':
        return 'badge-error';
      default:
        return 'badge-warning';
    }
  };

  if (!currentCustomer) {
    return (
      <div className="card text-center py-12 animate-fadeIn">
        <AlertCircle className="w-16 h-16 mx-auto text-yellow-500 mb-4" />
        <h3 className="text-lg font-medium text-gray-900 mb-2">No Customer Selected</h3>
        <p className="text-gray-500 mb-4">
          Please select a customer from the sidebar to view and manage projects.
        </p>
        <Link to="/customers" className="btn-primary">
          Go to Customers
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fadeIn">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Projects</h1>
          <p className="text-gray-500">
            Upload and manage webMethods migration projects for {currentCustomer.customerName}
          </p>
        </div>
      </div>

      {/* Upload Area */}
      <div
        {...getRootProps()}
        className={`card border-2 border-dashed transition-colors cursor-pointer ${
          isDragActive
            ? 'border-jade-500 bg-jade-50'
            : 'border-gray-300 hover:border-jade-400'
        } ${!currentCustomer || uploading ? 'opacity-50 cursor-not-allowed' : ''}`}
      >
        <input {...getInputProps()} />
        <div className="text-center py-8">
          {uploading ? (
            <>
              <Loader2 className="w-12 h-12 mx-auto text-jade-500 animate-spin mb-4" />
              <p className="text-lg font-medium">Uploading package...</p>
            </>
          ) : (
            <>
              <Upload className="w-12 h-12 mx-auto text-gray-400 mb-4" />
              <p className="text-lg font-medium">
                {isDragActive
                  ? 'Drop the file here...'
                  : 'Drag & drop a webMethods package ZIP'}
              </p>
              <p className="text-sm text-gray-500 mt-2">
                or click to select a file
              </p>
            </>
          )}
        </div>
      </div>

      {/* Project List */}
      {isLoading ? (
        <div className="card flex items-center justify-center py-12">
          <Loader2 className="w-8 h-8 animate-spin text-jade-500" />
        </div>
      ) : projects.length === 0 ? (
        <div className="card text-center py-12">
          <FolderOpen className="w-16 h-16 mx-auto text-gray-300 mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No projects yet</h3>
          <p className="text-gray-500">
            Upload a webMethods package ZIP file to get started
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {projects.map((project: Project) => (
            <div key={project.projectId} className="card hover:shadow-md transition-shadow">
              <div className="flex items-start justify-between">
                <div className="flex items-start">
                  <div className="w-12 h-12 bg-jade-100 rounded-lg flex items-center justify-center">
                    <FileArchive className="w-6 h-6 text-jade-600" />
                  </div>
                  <div className="ml-4">
                    <Link
                      to={`/projects/${project.projectId}`}
                      className="font-semibold text-lg hover:text-jade-600"
                    >
                      {project.packageName}
                    </Link>
                    <p className="text-sm text-gray-500">
                      {project.packageInfo?.services?.total || 0} services •{' '}
                      {((project.packageInfo?.fileSize || 0) / 1024).toFixed(1)} KB
                    </p>
                    <div className="flex items-center gap-2 mt-2">
                      <span className={`badge ${getStatusColor(project.status)}`}>
                        {project.status}
                      </span>
                      {project.analysis?.automationPotential && (
                        <span className="badge badge-jade">
                          {project.analysis.automationPotential} automation
                        </span>
                      )}
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  {project.status === 'uploaded' && (
                    <button
                      onClick={() => parseMutation.mutate(project.projectId)}
                      disabled={parseMutation.isPending}
                      className="btn-primary text-sm"
                    >
                      {parseMutation.isPending ? (
                        <Loader2 className="w-4 h-4 animate-spin" />
                      ) : (
                        <>
                          <Play className="w-4 h-4 mr-1" />
                          Parse
                        </>
                      )}
                    </button>
                  )}
                  {project.status === 'parsed' && (
                    <button
                      onClick={() => analyzeMutation.mutate(project.projectId)}
                      disabled={analyzeMutation.isPending}
                      className="btn-primary text-sm"
                    >
                      {analyzeMutation.isPending ? (
                        <Loader2 className="w-4 h-4 animate-spin" />
                      ) : (
                        <>
                          <BarChart3 className="w-4 h-4 mr-1" />
                          Analyze
                        </>
                      )}
                    </button>
                  )}
                  {(project.status === 'parsed' || project.status === 'analyzed') && (
                    <>
                      <Link
                        to={`/projects/${project.projectId}/files`}
                        className="btn-secondary text-sm"
                      >
                        <FileCode className="w-4 h-4 mr-1" />
                        Files
                      </Link>
                      {project.status === 'analyzed' && (
                        <>
                          <Link
                            to={`/projects/${project.projectId}/analysis`}
                            className="btn-secondary text-sm"
                          >
                            <BarChart3 className="w-4 h-4 mr-1" />
                            Analysis
                          </Link>
                          <Link
                            to={`/projects/${project.projectId}/conversions`}
                            className="btn-secondary text-sm"
                          >
                            <GitCompare className="w-4 h-4 mr-1" />
                            Convert
                          </Link>
                        </>
                      )}
                    </>
                  )}
                  <button
                    onClick={() => {
                      if (confirm('Delete this project?')) {
                        deleteMutation.mutate(project.projectId);
                      }
                    }}
                    className="p-2 text-red-500 hover:bg-red-50 rounded-lg"
                  >
                    <Trash2 className="w-5 h-5" />
                  </button>
                </div>
              </div>
              {project.errorMessage && (
                <div className="mt-4 p-3 bg-red-50 text-red-700 rounded-lg text-sm">
                  {project.errorMessage}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
