import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useParams, Link } from 'react-router-dom';
import {
  ArrowLeft,
  FileCode,
  BarChart3,
  GitCompare,
  Loader2,
  Play,
  FileArchive,
  Layers,
  Code,
  Database,
  FileText,
} from 'lucide-react';
import { projectsApi } from '../utils/api';

export default function ProjectDetail() {
  const { projectId } = useParams();
  const queryClient = useQueryClient();

  const { data: project, isLoading } = useQuery({
    queryKey: ['project', projectId],
    queryFn: async () => {
      const response = await projectsApi.get(projectId!);
      return response.data;
    },
    enabled: !!projectId,
  });

  const parseMutation = useMutation({
    mutationFn: () => projectsApi.parse(projectId!),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['project', projectId] });
    },
  });

  const analyzeMutation = useMutation({
    mutationFn: () => projectsApi.analyze(projectId!),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['project', projectId] });
    },
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="w-8 h-8 animate-spin text-jade-500" />
      </div>
    );
  }

  if (!project) {
    return (
      <div className="card text-center py-12">
        <p className="text-gray-500">Project not found</p>
        <Link to="/projects" className="btn-primary mt-4">
          Back to Projects
        </Link>
      </div>
    );
  }

  const services = project.packageInfo?.services;
  const flowVerbs = project.packageInfo?.flowVerbStats;

  return (
    <div className="space-y-6 animate-fadeIn">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center">
          <Link
            to="/projects"
            className="mr-4 p-2 hover:bg-gray-100 rounded-lg text-gray-500"
          >
            <ArrowLeft className="w-5 h-5" />
          </Link>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">{project.packageName}</h1>
            <p className="text-gray-500">
              Uploaded {new Date(project.uploadedAt).toLocaleString()}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {project.status === 'uploaded' && (
            <button
              onClick={() => parseMutation.mutate()}
              disabled={parseMutation.isPending}
              className="btn-primary"
            >
              {parseMutation.isPending ? (
                <Loader2 className="w-5 h-5 animate-spin" />
              ) : (
                <>
                  <Play className="w-5 h-5 mr-2" />
                  Parse Package
                </>
              )}
            </button>
          )}
          {project.status === 'parsed' && (
            <button
              onClick={() => analyzeMutation.mutate()}
              disabled={analyzeMutation.isPending}
              className="btn-primary"
            >
              {analyzeMutation.isPending ? (
                <Loader2 className="w-5 h-5 animate-spin" />
              ) : (
                <>
                  <BarChart3 className="w-5 h-5 mr-2" />
                  Analyze
                </>
              )}
            </button>
          )}
        </div>
      </div>

      {/* Status Banner */}
      <div
        className={`card ${
          project.status === 'analyzed'
            ? 'bg-green-50 border-green-200'
            : project.status === 'failed'
            ? 'bg-red-50 border-red-200'
            : 'bg-blue-50 border-blue-200'
        }`}
      >
        <div className="flex items-center">
          <FileArchive
            className={`w-8 h-8 mr-4 ${
              project.status === 'analyzed'
                ? 'text-green-600'
                : project.status === 'failed'
                ? 'text-red-600'
                : 'text-blue-600'
            }`}
          />
          <div>
            <p className="font-semibold">
              Status: <span className="capitalize">{project.status}</span>
            </p>
            {project.errorMessage && (
              <p className="text-sm text-red-600">{project.errorMessage}</p>
            )}
            {project.analysis && (
              <p className="text-sm text-green-700">
                Automation potential: {project.analysis.automationPotential} •
                Estimated hours: {project.analysis.estimatedHours}
              </p>
            )}
          </div>
        </div>
      </div>

      {/* Quick Links */}
      {(project.status === 'parsed' || project.status === 'analyzed') && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Link
            to={`/projects/${projectId}/files`}
            className="card hover:shadow-md transition-shadow flex items-center p-4"
          >
            <FileCode className="w-10 h-10 text-jade-500 mr-4" />
            <div>
              <h3 className="font-semibold">Document Viewer</h3>
              <p className="text-sm text-gray-500">Browse package files</p>
            </div>
          </Link>
          {project.status === 'analyzed' && (
            <>
              <Link
                to={`/projects/${projectId}/analysis`}
                className="card hover:shadow-md transition-shadow flex items-center p-4"
              >
                <BarChart3 className="w-10 h-10 text-jade-500 mr-4" />
                <div>
                  <h3 className="font-semibold">Analysis Dashboard</h3>
                  <p className="text-sm text-gray-500">View complexity & dependencies</p>
                </div>
              </Link>
              <Link
                to={`/projects/${projectId}/conversions`}
                className="card hover:shadow-md transition-shadow flex items-center p-4"
              >
                <GitCompare className="w-10 h-10 text-jade-500 mr-4" />
                <div>
                  <h3 className="font-semibold">Conversions</h3>
                  <p className="text-sm text-gray-500">Convert to Boomi</p>
                </div>
              </Link>
            </>
          )}
        </div>
      )}

      {/* Service Statistics */}
      {services && (
        <div className="card">
          <h2 className="text-lg font-semibold mb-4">Service Statistics</h2>
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
            <div className="p-4 bg-gray-50 rounded-lg text-center">
              <Layers className="w-8 h-8 mx-auto text-blue-500 mb-2" />
              <p className="text-2xl font-bold">{services.flow}</p>
              <p className="text-sm text-gray-500">Flow Services</p>
            </div>
            <div className="p-4 bg-gray-50 rounded-lg text-center">
              <Code className="w-8 h-8 mx-auto text-purple-500 mb-2" />
              <p className="text-2xl font-bold">{services.java}</p>
              <p className="text-sm text-gray-500">Java Services</p>
            </div>
            <div className="p-4 bg-gray-50 rounded-lg text-center">
              <Database className="w-8 h-8 mx-auto text-green-500 mb-2" />
              <p className="text-2xl font-bold">{services.adapter}</p>
              <p className="text-sm text-gray-500">Adapters</p>
            </div>
            <div className="p-4 bg-gray-50 rounded-lg text-center">
              <GitCompare className="w-8 h-8 mx-auto text-orange-500 mb-2" />
              <p className="text-2xl font-bold">{services.map}</p>
              <p className="text-sm text-gray-500">Map Services</p>
            </div>
            <div className="p-4 bg-gray-50 rounded-lg text-center">
              <FileText className="w-8 h-8 mx-auto text-jade-500 mb-2" />
              <p className="text-2xl font-bold">{services.document}</p>
              <p className="text-sm text-gray-500">Documents</p>
            </div>
          </div>
        </div>
      )}

      {/* Flow Verb Statistics */}
      {flowVerbs && (
        <div className="card">
          <h2 className="text-lg font-semibold mb-4">Flow Verb Usage (The 9 Verbs)</h2>
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
            {[
              { label: 'MAP', value: flowVerbs.map, color: 'bg-blue-100 text-blue-800' },
              { label: 'BRANCH', value: flowVerbs.branch, color: 'bg-yellow-100 text-yellow-800' },
              { label: 'LOOP', value: flowVerbs.loop, color: 'bg-green-100 text-green-800' },
              { label: 'REPEAT', value: flowVerbs.repeat, color: 'bg-purple-100 text-purple-800' },
              { label: 'SEQUENCE', value: flowVerbs.sequence, color: 'bg-gray-100 text-gray-800' },
              { label: 'TRY/CATCH', value: flowVerbs.tryCatch, color: 'bg-red-100 text-red-800' },
              { label: 'TRY/FINALLY', value: flowVerbs.tryFinally, color: 'bg-orange-100 text-orange-800' },
              { label: 'CATCH', value: flowVerbs.catch, color: 'bg-pink-100 text-pink-800' },
              { label: 'FINALLY', value: flowVerbs.finally, color: 'bg-indigo-100 text-indigo-800' },
              { label: 'EXIT', value: flowVerbs.exit, color: 'bg-jade-100 text-jade-800' },
            ].map((verb) => (
              <div key={verb.label} className={`p-3 rounded-lg ${verb.color}`}>
                <p className="text-xl font-bold">{verb.value}</p>
                <p className="text-sm">{verb.label}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* wMPublic Call Count */}
      {project.packageInfo && (
        <div className="card">
          <h2 className="text-lg font-semibold mb-4">Service Invocations</h2>
          <div className="grid grid-cols-2 gap-4">
            <div className="p-4 bg-jade-50 rounded-lg">
              <p className="text-3xl font-bold text-jade-700">
                {project.packageInfo.wMPublicCallCount}
              </p>
              <p className="text-sm text-jade-600">wMPublic Service Calls</p>
              <p className="text-xs text-gray-500 mt-1">
                Built-in webMethods services (pub.*, wm.*)
              </p>
            </div>
            <div className="p-4 bg-purple-50 rounded-lg">
              <p className="text-3xl font-bold text-purple-700">
                {project.packageInfo.customJavaCallCount}
              </p>
              <p className="text-sm text-purple-600">Custom Service Calls</p>
              <p className="text-xs text-gray-500 mt-1">
                Custom Java services and utilities
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
