import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { ArrowLeft, GitBranch, CheckCircle, Circle, ChevronRight, FileInput, FileOutput, Zap, Eye, Download, Database, Layers } from 'lucide-react';

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

      <div className="grid gap-6">
        {integrations.map((integration, idx) => {
          // Use actual document counts from integration data
          const sourceDocCount = integration.sourceDocuments?.length || 0;
          const targetDocCount = integration.targetDocuments?.length || 0;
          const adapterCount = integration.adapters?.length || 0;
          const serviceCount = integration.services?.length || 0;
          
          return (
            <div key={idx} className="bg-white rounded-lg shadow-lg p-6 hover:shadow-xl transition-shadow border-l-4 border-jade-blue">
              <div className="flex items-start justify-between mb-4">
                <div className="flex-1">
                  <h2 className="text-2xl font-bold text-jade-blue mb-2">{integration.name}</h2>
                  <p className="text-gray-600 text-sm mb-3">{integration.functionalArea}</p>
                  
                  <div className="flex gap-4 text-sm flex-wrap">
                    <div>
                      <span className="font-semibold text-jade-blue">{serviceCount}</span> Services
                    </div>
                    <div>
                      <span className="font-semibold text-jade-blue">{adapterCount}</span> Adapters
                    </div>
                    <div>
                      <span className={`px-2 py-1 rounded text-xs font-semibold ${
                        integration.complexity === 'low' ? 'bg-green-100 text-green-700' :
                        integration.complexity === 'medium' ? 'bg-yellow-100 text-yellow-700' :
                        'bg-red-100 text-red-700'
                      }`}>
                        {integration.complexity} complexity
                      </span>
                    </div>
                    <div>
                      <span className="text-green-600 font-semibold">{integration.automation}</span> automated
                    </div>
                    <div className="text-gray-500">
                      {integration.estimatedHours} estimated
                    </div>
                  </div>
                </div>
                
                <button
                  onClick={() => openImplementation(integration)}
                  className="bg-jade-gold text-jade-blue-dark px-6 py-3 rounded-lg hover:bg-jade-gold-dark font-semibold flex items-center gap-2 transition-all shadow-md hover:shadow-lg"
                >
                  Start Implementation
                  <ChevronRight size={20} />
                </button>
              </div>
              
              {/* Services List */}
              <div className="mb-4">
                <h4 className="text-sm font-semibold text-gray-700 mb-2">Services in this integration:</h4>
                <ul className="text-sm text-gray-600 list-disc list-inside">
                  {integration.services?.slice(0, 5).map((svc: any, svcIdx: number) => (
                    <li key={svcIdx}>
                      {svc.name?.split('/').pop() || svc.name} ({svc.type}, {svc.steps || 0} steps)
                    </li>
                  ))}
                  {integration.services?.length > 5 && (
                    <li className="text-jade-blue">+ {integration.services.length - 5} more services</li>
                  )}
                </ul>
              </div>
              
              {/* Components to Build */}
              <div>
                <h4 className="text-sm font-semibold text-gray-700 mb-3">Components to Build in Boomi:</h4>
                <div className="grid grid-cols-4 gap-3">
                  <div className="bg-purple-50 p-3 rounded-lg text-center">
                    <Database className="mx-auto text-purple-600 mb-1" size={20} />
                    <div className="text-2xl font-bold text-purple-600">{adapterCount}</div>
                    <div className="text-xs text-purple-700">Connectors</div>
                  </div>
                  <div className="bg-blue-50 p-3 rounded-lg text-center">
                    <FileInput className="mx-auto text-blue-600 mb-1" size={20} />
                    <div className="text-2xl font-bold text-blue-600">{sourceDocCount}</div>
                    <div className="text-xs text-blue-700">Source Profiles</div>
                  </div>
                  <div className="bg-green-50 p-3 rounded-lg text-center">
                    <FileOutput className="mx-auto text-green-600 mb-1" size={20} />
                    <div className="text-2xl font-bold text-green-600">{targetDocCount}</div>
                    <div className="text-xs text-green-700">Target Profiles</div>
                  </div>
                  <div className="bg-jade-gold bg-opacity-20 p-3 rounded-lg text-center">
                    <Layers className="mx-auto text-jade-blue mb-1" size={20} />
                    <div className="text-2xl font-bold text-jade-blue">{serviceCount}</div>
                    <div className="text-xs text-jade-blue">Processes</div>
                  </div>
                </div>
              </div>
              
              {/* Document Details */}
              {(sourceDocCount > 0 || targetDocCount > 0) && (
                <div className="mt-4 grid grid-cols-2 gap-4">
                  {sourceDocCount > 0 && (
                    <div>
                      <h5 className="text-xs font-semibold text-blue-700 mb-1 flex items-center gap-1">
                        <FileInput size={12} /> Source Documents:
                      </h5>
                      <ul className="text-xs text-gray-600">
                        {integration.sourceDocuments?.map((doc: any, docIdx: number) => (
                          <li key={docIdx}>
                            • {doc.name?.split('/').pop() || doc.name} ({doc.fields?.length || 0} fields)
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                  {targetDocCount > 0 && (
                    <div>
                      <h5 className="text-xs font-semibold text-green-700 mb-1 flex items-center gap-1">
                        <FileOutput size={12} /> Target Documents:
                      </h5>
                      <ul className="text-xs text-gray-600">
                        {integration.targetDocuments?.map((doc: any, docIdx: number) => (
                          <li key={docIdx}>
                            • {doc.name?.split('/').pop() || doc.name} ({doc.fields?.length || 0} fields)
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              )}
            </div>
          );
        })}
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
