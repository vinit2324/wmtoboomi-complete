import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { ArrowLeft, GitBranch, CheckCircle, Circle, ChevronRight, ChevronDown, Zap, Eye, Download } from 'lucide-react';

export default function Integrations() {
  const { projectId } = useParams();
  const navigate = useNavigate();
  const [integrations, setIntegrations] = useState<any[]>([]);
  const [project, setProject] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, [projectId]);

  const loadData = async () => {
    try {
      const [integrationsRes, projectRes] = await Promise.all([
        axios.get(`http://localhost:7201/api/integrations/${projectId}`),
        axios.get(`http://localhost:7201/api/projects/${projectId}`)
      ]);
      setIntegrations(integrationsRes.data.integrations || []);
      setProject(projectRes.data);
    } catch (error) {
      console.error('Error:', error);
    } finally {
      setLoading(false);
    }
  };

  const openImplementation = (integration: any) => {
    navigate(`/projects/${projectId}/integrations/${encodeURIComponent(integration.name)}`);
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
      <div className="flex items-center gap-4 mb-6">
        <button onClick={() => navigate(`/projects/${projectId}`)} className="p-2 hover:bg-gray-100 rounded">
          <ArrowLeft size={24} />
        </button>
        <div>
          <h1 className="text-3xl font-bold text-jade-blue">Integration Patterns</h1>
          <p className="text-gray-600">Grouped services with Boomi implementation steps</p>
        </div>
      </div>

      <div className="grid gap-4">
        {integrations.map((integration, idx) => (
          <div key={idx} className="bg-white rounded-lg shadow-lg p-6 hover:shadow-xl transition-shadow border-l-4 border-jade-blue">
            <div className="flex items-start justify-between mb-4">
              <div className="flex-1">
                <h2 className="text-2xl font-bold text-jade-blue mb-2">{integration.name}</h2>
                <p className="text-gray-600 text-sm mb-3">{integration.functionalArea}</p>
                
                <div className="flex gap-4 text-sm flex-wrap">
                  <div>
                    <span className="font-semibold text-jade-blue">{integration.services.length}</span> Services
                  </div>
                  <div>
                    <span className="font-semibold text-jade-blue">{integration.adapters.length}</span> Adapters
                  </div>
                  <div>
                    <span className={`px-2 py-1 rounded text-xs font-semibold ${
                      integration.complexity === 'low' ? 'bg-green-100 text-green-800' :
                      integration.complexity === 'medium' ? 'bg-yellow-100 text-yellow-800' :
                      'bg-red-100 text-red-800'
                    }`}>
                      {integration.complexity} complexity
                    </span>
                  </div>
                  <div>
                    <span className="text-jade-blue font-semibold">{integration.automationLevel}</span> automated
                  </div>
                  <div>
                    <span className="font-semibold text-jade-blue">{integration.estimatedHours}h</span> estimated
                  </div>
                </div>
              </div>
              
              <button
                onClick={() => openImplementation(integration)}
                className="bg-jade-gold text-jade-blue-dark px-6 py-3 rounded-lg hover:bg-jade-gold-dark font-semibold flex items-center gap-2 shadow-md transition-all"
              >
                Start Implementation
                <ChevronRight size={20} />
              </button>
            </div>

            <div className="border-t pt-4">
              <div className="text-sm font-semibold text-jade-blue mb-2">Services in this integration:</div>
              <div className="space-y-1">
                {integration.services.slice(0, 5).map((svc: any, i: number) => (
                  <div key={i} className="text-sm text-gray-600 flex items-center gap-2">
                    <Circle size={6} className="fill-current text-jade-blue" />
                    {svc.name.split('/').pop()} ({svc.type}, {svc.steps} steps)
                  </div>
                ))}
                {integration.services.length > 5 && (
                  <div className="text-sm text-gray-500">+ {integration.services.length - 5} more services...</div>
                )}
              </div>
            </div>

            {/* Quick Preview of Components */}
            <div className="border-t pt-4 mt-4">
              <div className="text-sm font-semibold text-jade-blue mb-3">Components to Build in Boomi:</div>
              <div className="grid grid-cols-4 gap-3">
                <div className="bg-purple-50 p-3 rounded-lg text-center">
                  <div className="text-2xl font-bold text-purple-600">{integration.adapters.length}</div>
                  <div className="text-xs text-purple-700">Connectors</div>
                </div>
                <div className="bg-blue-50 p-3 rounded-lg text-center">
                  <div className="text-2xl font-bold text-blue-600">2</div>
                  <div className="text-xs text-blue-700">Source Profiles</div>
                </div>
                <div className="bg-green-50 p-3 rounded-lg text-center">
                  <div className="text-2xl font-bold text-green-600">2</div>
                  <div className="text-xs text-green-700">Target Profiles</div>
                </div>
                <div className="bg-jade-gold bg-opacity-20 p-3 rounded-lg text-center">
                  <div className="text-2xl font-bold text-jade-blue">{integration.services.length}</div>
                  <div className="text-xs text-jade-blue">Processes</div>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>

      {integrations.length === 0 && (
        <div className="bg-white rounded-lg shadow-lg p-12 text-center">
          <GitBranch className="mx-auto text-gray-300 mb-4" size={64} />
          <h3 className="text-xl font-semibold text-gray-600 mb-2">No Integration Patterns Found</h3>
          <p className="text-gray-500">Upload a webMethods package to analyze integration patterns</p>
        </div>
      )}
    </div>
  );
}
