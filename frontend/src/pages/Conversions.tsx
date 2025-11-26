import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useParams, Link } from 'react-router-dom';
import Editor from '@monaco-editor/react';
import {
  ArrowLeft,
  Loader2,
  Play,
  Upload,
  CheckCircle,
  AlertCircle,
  Eye,
  X,
  ExternalLink,
} from 'lucide-react';
import { projectsApi, conversionsApi } from '../utils/api';
import { useStore } from '../stores/useStore';
import type { Conversion, ParsedService } from '../types';

export default function Conversions() {
  const { projectId } = useParams();
  const queryClient = useQueryClient();
  const { currentCustomer } = useStore();
  const [selectedConversion, setSelectedConversion] = useState<Conversion | null>(null);

  const { data: project, isLoading: projectLoading } = useQuery({
    queryKey: ['project', projectId],
    queryFn: async () => {
      const response = await projectsApi.get(projectId!);
      return response.data;
    },
    enabled: !!projectId,
  });

  const { data: conversionsData, isLoading: conversionsLoading } = useQuery({
    queryKey: ['conversions', projectId],
    queryFn: async () => {
      const response = await conversionsApi.list(projectId!);
      return response.data;
    },
    enabled: !!projectId,
  });

  const convertAllMutation = useMutation({
    mutationFn: () =>
      conversionsApi.convertAll(projectId!, currentCustomer!.customerId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['conversions', projectId] });
    },
  });

  const convertSingleMutation = useMutation({
    mutationFn: (service: ParsedService) =>
      conversionsApi.convert({
        projectId: projectId!,
        sourceName: service.name,
        sourceType: service.type,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['conversions', projectId] });
    },
  });

  const pushMutation = useMutation({
    mutationFn: (conversionId: string) => conversionsApi.push(conversionId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['conversions', projectId] });
    },
  });

  const pushAllMutation = useMutation({
    mutationFn: () =>
      conversionsApi.pushAll(projectId!, currentCustomer!.customerId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['conversions', projectId] });
    },
  });

  const conversions = conversionsData?.conversions || [];
  const services = project?.parsedData?.services || [];

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'converted':
      case 'validated':
        return <CheckCircle className="w-5 h-5 text-green-500" />;
      case 'pushed':
        return <Upload className="w-5 h-5 text-jade-500" />;
      case 'failed':
        return <AlertCircle className="w-5 h-5 text-red-500" />;
      default:
        return <Loader2 className="w-5 h-5 text-gray-400 animate-spin" />;
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'converted':
      case 'validated':
        return 'badge-success';
      case 'pushed':
        return 'badge-jade';
      case 'failed':
        return 'badge-error';
      default:
        return 'badge-info';
    }
  };

  if (projectLoading || conversionsLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="w-8 h-8 animate-spin text-jade-500" />
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fadeIn">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center">
          <Link
            to={`/projects/${projectId}`}
            className="mr-4 p-2 hover:bg-gray-100 rounded-lg text-gray-500"
          >
            <ArrowLeft className="w-5 h-5" />
          </Link>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Conversions</h1>
            <p className="text-gray-500">{project?.packageName}</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {conversions.length === 0 ? (
            <button
              onClick={() => convertAllMutation.mutate()}
              disabled={convertAllMutation.isPending || !currentCustomer}
              className="btn-primary"
            >
              {convertAllMutation.isPending ? (
                <Loader2 className="w-5 h-5 animate-spin" />
              ) : (
                <>
                  <Play className="w-5 h-5 mr-2" />
                  Convert All Services
                </>
              )}
            </button>
          ) : (
            <button
              onClick={() => pushAllMutation.mutate()}
              disabled={pushAllMutation.isPending || !currentCustomer}
              className="btn-primary"
            >
              {pushAllMutation.isPending ? (
                <Loader2 className="w-5 h-5 animate-spin" />
              ) : (
                <>
                  <Upload className="w-5 h-5 mr-2" />
                  Push All to Boomi
                </>
              )}
            </button>
          )}
        </div>
      </div>

      {/* Conversions List */}
      {conversions.length === 0 ? (
        <div className="card">
          <h2 className="text-lg font-semibold mb-4">Services to Convert</h2>
          <div className="space-y-2">
            {services.map((service: ParsedService) => (
              <div
                key={service.name}
                className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
              >
                <div>
                  <p className="font-medium">{service.name}</p>
                  <p className="text-sm text-gray-500">{service.type}</p>
                </div>
                <button
                  onClick={() => convertSingleMutation.mutate(service)}
                  disabled={convertSingleMutation.isPending}
                  className="btn-secondary text-sm"
                >
                  Convert
                </button>
              </div>
            ))}
          </div>
        </div>
      ) : (
        <div className="space-y-4">
          {/* Summary */}
          <div className="grid grid-cols-4 gap-4">
            <div className="card text-center">
              <p className="text-3xl font-bold">{conversions.length}</p>
              <p className="text-sm text-gray-500">Total</p>
            </div>
            <div className="card text-center">
              <p className="text-3xl font-bold text-green-600">
                {conversions.filter((c) => c.status === 'converted' || c.status === 'validated').length}
              </p>
              <p className="text-sm text-gray-500">Converted</p>
            </div>
            <div className="card text-center">
              <p className="text-3xl font-bold text-jade-600">
                {conversions.filter((c) => c.status === 'pushed').length}
              </p>
              <p className="text-sm text-gray-500">Pushed</p>
            </div>
            <div className="card text-center">
              <p className="text-3xl font-bold text-red-600">
                {conversions.filter((c) => c.status === 'failed').length}
              </p>
              <p className="text-sm text-gray-500">Failed</p>
            </div>
          </div>

          {/* Conversion List */}
          <div className="card">
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-gray-200">
                    <th className="text-left py-3 px-4">Service</th>
                    <th className="text-left py-3 px-4">Type</th>
                    <th className="text-left py-3 px-4">Status</th>
                    <th className="text-left py-3 px-4">Automation</th>
                    <th className="text-left py-3 px-4">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {conversions.map((conversion: Conversion) => (
                    <tr key={conversion.conversionId} className="border-b border-gray-100 hover:bg-gray-50">
                      <td className="py-3 px-4">
                        <p className="font-medium">{conversion.sourceName.split(':').pop()}</p>
                        <p className="text-xs text-gray-500">{conversion.targetName}</p>
                      </td>
                      <td className="py-3 px-4">
                        <span className="text-sm">{conversion.sourceType}</span>
                      </td>
                      <td className="py-3 px-4">
                        <span className={`badge ${getStatusBadge(conversion.status)}`}>
                          {conversion.status}
                        </span>
                      </td>
                      <td className="py-3 px-4">
                        <span className={`font-medium ${
                          parseInt(conversion.automationLevel) >= 80
                            ? 'text-green-600'
                            : parseInt(conversion.automationLevel) >= 50
                            ? 'text-yellow-600'
                            : 'text-red-600'
                        }`}>
                          {conversion.automationLevel}
                        </span>
                      </td>
                      <td className="py-3 px-4">
                        <div className="flex items-center gap-2">
                          <button
                            onClick={() => setSelectedConversion(conversion)}
                            className="p-2 hover:bg-gray-100 rounded-lg"
                            title="View XML"
                          >
                            <Eye className="w-4 h-4" />
                          </button>
                          {conversion.status !== 'pushed' && (
                            <button
                              onClick={() => pushMutation.mutate(conversion.conversionId)}
                              disabled={pushMutation.isPending}
                              className="p-2 hover:bg-jade-100 rounded-lg text-jade-600"
                              title="Push to Boomi"
                            >
                              <Upload className="w-4 h-4" />
                            </button>
                          )}
                          {conversion.boomiComponent?.componentUrl && (
                            <a
                              href={conversion.boomiComponent.componentUrl}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="p-2 hover:bg-blue-100 rounded-lg text-blue-600"
                              title="Open in Boomi"
                            >
                              <ExternalLink className="w-4 h-4" />
                            </a>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* XML Viewer Modal */}
      {selectedConversion && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl shadow-xl w-full max-w-4xl max-h-[90vh] m-4 flex flex-col">
            <div className="p-4 border-b border-gray-200 flex items-center justify-between">
              <div>
                <h2 className="text-lg font-semibold">{selectedConversion.targetName}</h2>
                <div className="flex items-center gap-2 mt-1">
                  <span className={`badge ${getStatusBadge(selectedConversion.status)}`}>
                    {selectedConversion.status}
                  </span>
                  <span className="text-sm text-gray-500">
                    {selectedConversion.automationLevel} automation
                  </span>
                </div>
              </div>
              <button
                onClick={() => setSelectedConversion(null)}
                className="p-2 hover:bg-gray-100 rounded-lg"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
            {/* Conversion Notes */}
            {selectedConversion.conversionNotes.length > 0 && (
              <div className="p-4 border-b border-gray-200 bg-gray-50">
                <h3 className="font-medium mb-2">Conversion Notes</h3>
                <ul className="text-sm space-y-1">
                  {selectedConversion.conversionNotes.map((note, i) => (
                    <li key={i} className="flex items-start">
                      <span className="mr-2">{note.includes('⚠️') ? '⚠️' : '✓'}</span>
                      {note.replace('⚠️', '')}
                    </li>
                  ))}
                </ul>
              </div>
            )}
            <div className="flex-1 min-h-0">
              <Editor
                height="100%"
                language="xml"
                value={selectedConversion.boomiXml || ''}
                options={{
                  readOnly: true,
                  minimap: { enabled: false },
                  fontSize: 13,
                  fontFamily: 'JetBrains Mono, monospace',
                  wordWrap: 'on',
                }}
                theme="vs-light"
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
