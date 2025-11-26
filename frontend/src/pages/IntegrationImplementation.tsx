import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { ArrowLeft, Database, FileText, GitMerge, Zap, CheckCircle, Clock, Download, Upload, Eye, X } from 'lucide-react';
import BoomiProcessCanvas from '../components/BoomiProcessCanvas';
import { useToast } from '../components/Toast';

export default function IntegrationImplementation() {
  const { projectId, integrationName } = useParams();
  const navigate = useNavigate();
  const { showToast } = useToast();
  const [integration, setIntegration] = useState<any>(null);
  const [project, setProject] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [convertedComponents, setConvertedComponents] = useState<Set<string>>(new Set());
  const [convertedSteps, setConvertedSteps] = useState<Map<string, Set<number>>>(new Map());
  const [converting, setConverting] = useState<string | null>(null);
  const [conversions, setConversions] = useState<Map<string, any>>(new Map());
  
  // Modal states
  const [viewModal, setViewModal] = useState<{open: boolean, title: string, content: any} | null>(null);

  useEffect(() => {
    loadData();
  }, [projectId, integrationName]);

  const loadData = async () => {
    try {
      const [integrationsRes, projectRes] = await Promise.all([
        axios.get(`http://localhost:7201/api/integrations/${projectId}`),
        axios.get(`http://localhost:7201/api/projects/${projectId}`)
      ]);
      
      const foundIntegration = integrationsRes.data.integrations.find(
        (i: any) => i.name === decodeURIComponent(integrationName || '')
      );
      
      setIntegration(foundIntegration);
      setProject(projectRes.data);
    } catch (error) {
      console.error('Error:', error);
    } finally {
      setLoading(false);
    }
  };

  const convertComponent = async (serviceName: string) => {
    setConverting(serviceName);
    try {
      const response = await axios.post('http://localhost:7201/api/conversions/convert', {
        projectId: projectId,
        serviceName: serviceName
      });

      const newConversions = new Map(conversions);
      newConversions.set(serviceName, response.data);
      setConversions(newConversions);
      
      const newConverted = new Set(convertedComponents);
      newConverted.add(serviceName);
      setConvertedComponents(newConverted);
      
      showToast(`${serviceName.split('/').pop()} converted successfully!`, 'success');
    } catch (error: any) {
      showToast(`Conversion failed: ${error.response?.data?.detail || error.message}`, 'error');
    } finally {
      setConverting(null);
    }
  };

  const viewComponent = async (serviceName: string, title: string) => {
    try {
      const response = await axios.get(
        `http://localhost:7201/api/conversions/view-source/${projectId}?service_name=${encodeURIComponent(serviceName)}`
      );
      
      setViewModal({
        open: true,
        title: title,
        content: response.data
      });
    } catch (error: any) {
      showToast(`Failed to load: ${error.response?.data?.detail || error.message}`, 'error');
    }
  };

  const viewStepDetails = (step: any, index: number, serviceName: string) => {
    setViewModal({
      open: true,
      title: `Step ${index + 1}: ${step.name || step.type}`,
      content: {
        step: step,
        boomiMapping: {
          'MAP': 'Map Shape - Data transformation',
          'BRANCH': 'Decision Shape - Conditional routing',
          'LOOP': 'ForEach Shape - Iterate over documents',
          'INVOKE': 'Connector Shape - External service call',
          'SEQUENCE': 'Try/Catch Shape - Error handling',
          'EXIT': 'Stop Shape - End process'
        }[step.type] || 'Business Rules Shape'
      }
    });
  };

  const convertStep = (step: any, index: number, serviceName: string) => {
    // Mark step as converted
    const serviceSteps = convertedSteps.get(serviceName) || new Set();
    serviceSteps.add(index);
    const newConvertedSteps = new Map(convertedSteps);
    newConvertedSteps.set(serviceName, serviceSteps);
    setConvertedSteps(newConvertedSteps);
    
    const boomiShape = {
      'MAP': 'Map Shape',
      'BRANCH': 'Decision Shape',
      'LOOP': 'ForEach Shape',
      'INVOKE': 'Connector Shape',
      'SEQUENCE': 'Try/Catch Shape',
      'EXIT': 'Stop Shape'
    }[step.type] || 'Business Rules Shape';
    
    showToast(`Step ${index + 1} (${step.type}) → ${boomiShape}`, 'success');
  };

  const downloadXml = (serviceName: string) => {
    const conversion = conversions.get(serviceName);
    if (!conversion) return;
    
    const blob = new Blob([conversion.boomiXml], { type: 'application/xml' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${serviceName.split('/').pop()}_boomi.xml`;
    a.click();
    URL.revokeObjectURL(url);
    showToast('XML downloaded successfully', 'info');
  };

  const pushToBoomi = async (serviceName: string) => {
    const conversion = conversions.get(serviceName);
    if (!conversion) return;
    
    try {
      const response = await axios.post('http://localhost:7201/api/conversions/push-to-boomi', {
        projectId: projectId,
        componentXml: conversion.boomiXml,
        componentName: serviceName
      });

      if (response.data.success) {
        showToast(`Successfully pushed to Boomi! Component ID: ${response.data.componentId}`, 'success');
      } else {
        showToast(`Push failed: ${response.data.message}`, 'error');
      }
    } catch (error: any) {
      showToast(`Push error: ${error.message}`, 'error');
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-jade-blue"></div>
      </div>
    );
  }

  if (!integration || !project) {
    return <div className="p-6">Integration not found</div>;
  }

  const allServices = project.parsedData?.services || [];
  const integrationServices = integration.services
    .map((svc: any) => allServices.find((s: any) => s.name === svc.name))
    .filter((s: any) => s);

  const allDocuments = project.parsedData?.documents || [];
  const sourceDocuments = allDocuments.slice(0, 2);
  const targetDocuments = allDocuments.slice(2, 4);

  const totalComponents = integrationServices.length + sourceDocuments.length + targetDocuments.length;
  const convertedCount = convertedComponents.size;

  return (
    <div className="p-6">
      <div className="flex items-center gap-4 mb-6">
        <button onClick={() => navigate(`/projects/${projectId}/integrations`)} className="p-2 hover:bg-gray-100 rounded">
          <ArrowLeft size={24} />
        </button>
        <div>
          <h1 className="text-3xl font-bold text-jade-blue">{integration.name}</h1>
          <p className="text-gray-600">Visual Boomi Implementation Guide</p>
        </div>
      </div>

      {/* Progress Overview */}
      <div className="bg-gradient-to-r from-jade-blue to-jade-blue-light text-white rounded-lg p-6 mb-6 shadow-lg">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-2xl font-bold">Implementation Progress</h2>
          <div className="text-4xl font-bold">{totalComponents > 0 ? Math.round((convertedCount / totalComponents) * 100) : 0}%</div>
        </div>
        <div className="h-4 bg-white bg-opacity-20 rounded-full overflow-hidden">
          <div 
            className="h-full bg-jade-gold transition-all duration-500"
            style={{ width: `${totalComponents > 0 ? (convertedCount / totalComponents) * 100 : 0}%` }}
          />
        </div>
        <div className="mt-2 text-sm opacity-80">
          {convertedCount} of {totalComponents} components converted
        </div>
      </div>

      {/* Step 1: Connectors */}
      {integration.adapters && integration.adapters.length > 0 && (
        <div className="bg-white rounded-lg shadow-lg mb-6 border-l-4 border-purple-500">
          <div className="p-6 border-b">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-full bg-jade-blue text-white flex items-center justify-center font-bold">1</div>
              <div>
                <h3 className="text-xl font-bold text-jade-blue">Create Connectors</h3>
                <p className="text-sm text-gray-600">Set up connections for {integration.adapters.join(', ')}</p>
              </div>
            </div>
          </div>
          <div className="p-6 bg-purple-50">
            <div className="grid gap-3">
              {integration.adapters.map((adapter: string, idx: number) => (
                <div key={idx} className="flex items-center justify-between p-4 bg-white rounded-lg border-2 border-purple-200">
                  <div className="flex items-center gap-3">
                    <Database className="text-purple-600" size={24} />
                    <div>
                      <div className="font-semibold text-jade-blue">{adapter} Connector</div>
                      <div className="text-sm text-gray-600">Database connection configuration</div>
                    </div>
                  </div>
                  <button 
                    onClick={() => showToast('Open Boomi to configure connector manually', 'info')}
                    className="px-4 py-2 bg-jade-blue text-white rounded-lg hover:bg-jade-blue-dark font-semibold"
                  >
                    Configure Manually
                  </button>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Step 2: Source Profiles */}
      {sourceDocuments.length > 0 && (
        <div className="bg-white rounded-lg shadow-lg mb-6 border-l-4 border-blue-500">
          <div className="p-6 border-b">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-full bg-jade-blue text-white flex items-center justify-center font-bold">2</div>
              <div>
                <h3 className="text-xl font-bold text-jade-blue">Create Source Profiles</h3>
                <p className="text-sm text-gray-600">Define incoming data structures</p>
              </div>
            </div>
          </div>
          <div className="p-6 bg-blue-50">
            <div className="grid gap-3">
              {sourceDocuments.map((doc: any) => {
                const isConverted = convertedComponents.has(doc.name);
                return (
                  <div key={doc.name} className="flex items-center justify-between p-4 bg-white rounded-lg border-2 border-blue-200">
                    <div className="flex items-center gap-3">
                      <FileText className="text-blue-600" size={24} />
                      <div>
                        <div className="font-semibold text-jade-blue">{doc.name.split('/').pop()}</div>
                        <div className="text-sm text-gray-600">{doc.fields?.length || 0} fields</div>
                      </div>
                    </div>
                    <div className="flex gap-2">
                      <button
                        onClick={() => viewComponent(doc.name, doc.name.split('/').pop())}
                        className="px-4 py-2 border-2 border-jade-blue text-jade-blue rounded-lg hover:bg-jade-blue hover:text-white font-semibold flex items-center gap-2"
                      >
                        <Eye size={16} />
                        View
                      </button>
                      {isConverted ? (
                        <>
                          <button onClick={() => downloadXml(doc.name)} className="px-4 py-2 bg-jade-blue text-white rounded-lg hover:bg-jade-blue-dark font-semibold flex items-center gap-2">
                            <Download size={16} />
                          </button>
                          <button onClick={() => pushToBoomi(doc.name)} className="px-4 py-2 bg-jade-gold text-jade-blue-dark rounded-lg hover:bg-jade-gold-dark font-semibold flex items-center gap-2">
                            <Upload size={16} />
                          </button>
                          <span className="px-4 py-2 bg-green-100 text-green-800 rounded-lg font-semibold flex items-center gap-2">
                            <CheckCircle size={16} />
                          </span>
                        </>
                      ) : (
                        <button
                          onClick={() => convertComponent(doc.name)}
                          disabled={converting === doc.name}
                          className="px-4 py-2 bg-jade-gold text-jade-blue-dark rounded-lg hover:bg-jade-gold-dark font-semibold flex items-center gap-2 disabled:opacity-50"
                        >
                          <Zap size={16} />
                          {converting === doc.name ? 'Converting...' : 'Convert'}
                        </button>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      )}

      {/* Step 3: Target Profiles */}
      {targetDocuments.length > 0 && (
        <div className="bg-white rounded-lg shadow-lg mb-6 border-l-4 border-green-500">
          <div className="p-6 border-b">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-full bg-jade-blue text-white flex items-center justify-center font-bold">3</div>
              <div>
                <h3 className="text-xl font-bold text-jade-blue">Create Target Profiles</h3>
                <p className="text-sm text-gray-600">Define outgoing data structures</p>
              </div>
            </div>
          </div>
          <div className="p-6 bg-green-50">
            <div className="grid gap-3">
              {targetDocuments.map((doc: any) => {
                const isConverted = convertedComponents.has(doc.name);
                return (
                  <div key={doc.name} className="flex items-center justify-between p-4 bg-white rounded-lg border-2 border-green-200">
                    <div className="flex items-center gap-3">
                      <FileText className="text-green-600" size={24} />
                      <div>
                        <div className="font-semibold text-jade-blue">{doc.name.split('/').pop()}</div>
                        <div className="text-sm text-gray-600">{doc.fields?.length || 0} fields</div>
                      </div>
                    </div>
                    <div className="flex gap-2">
                      <button
                        onClick={() => viewComponent(doc.name, doc.name.split('/').pop())}
                        className="px-4 py-2 border-2 border-jade-blue text-jade-blue rounded-lg hover:bg-jade-blue hover:text-white font-semibold flex items-center gap-2"
                      >
                        <Eye size={16} />
                        View
                      </button>
                      {isConverted ? (
                        <>
                          <button onClick={() => downloadXml(doc.name)} className="px-4 py-2 bg-jade-blue text-white rounded-lg hover:bg-jade-blue-dark font-semibold flex items-center gap-2">
                            <Download size={16} />
                          </button>
                          <button onClick={() => pushToBoomi(doc.name)} className="px-4 py-2 bg-jade-gold text-jade-blue-dark rounded-lg hover:bg-jade-gold-dark font-semibold flex items-center gap-2">
                            <Upload size={16} />
                          </button>
                          <span className="px-4 py-2 bg-green-100 text-green-800 rounded-lg font-semibold flex items-center gap-2">
                            <CheckCircle size={16} />
                          </span>
                        </>
                      ) : (
                        <button
                          onClick={() => convertComponent(doc.name)}
                          disabled={converting === doc.name}
                          className="px-4 py-2 bg-jade-gold text-jade-blue-dark rounded-lg hover:bg-jade-gold-dark font-semibold flex items-center gap-2 disabled:opacity-50"
                        >
                          <Zap size={16} />
                          {converting === doc.name ? 'Converting...' : 'Convert'}
                        </button>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      )}

      {/* Step 4: Process with Visual Canvas */}
      {integrationServices.length > 0 && (
        <div className="bg-white rounded-lg shadow-lg mb-6 border-l-4 border-jade-gold">
          <div className="p-6 border-b">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-full bg-jade-blue text-white flex items-center justify-center font-bold">4</div>
              <div>
                <h3 className="text-xl font-bold text-jade-blue">Create Processes</h3>
                <p className="text-sm text-gray-600">Visual Boomi process flow - Click on each shape to view/convert</p>
              </div>
            </div>
          </div>
          <div className="p-6">
            {integrationServices.map((service: any) => {
              const isConverted = convertedComponents.has(service.name);
              const serviceConvertedSteps = convertedSteps.get(service.name) || new Set();
              
              return (
                <div key={service.name} className="mb-8 p-4 bg-jade-gray rounded-lg">
                  <div className="flex items-center justify-between mb-4">
                    <div>
                      <div className="font-bold text-xl text-jade-blue">{service.name.split('/').pop()}</div>
                      <div className="text-sm text-gray-600">{service.flowSteps?.length || 0} Boomi shapes to create</div>
                    </div>
                    <div className="flex gap-2">
                      <button
                        onClick={() => viewComponent(service.name, service.name.split('/').pop())}
                        className="px-4 py-2 border-2 border-jade-blue text-jade-blue rounded-lg hover:bg-jade-blue hover:text-white font-semibold flex items-center gap-2"
                      >
                        <Eye size={16} />
                        View Source
                      </button>
                      {isConverted ? (
                        <>
                          <button onClick={() => downloadXml(service.name)} className="px-4 py-2 bg-jade-blue text-white rounded-lg hover:bg-jade-blue-dark font-semibold flex items-center gap-2">
                            <Download size={16} />
                            Download
                          </button>
                          <button onClick={() => pushToBoomi(service.name)} className="px-4 py-2 bg-jade-gold text-jade-blue-dark rounded-lg hover:bg-jade-gold-dark font-semibold flex items-center gap-2">
                            <Upload size={16} />
                            Push to Boomi
                          </button>
                          <span className="px-4 py-2 bg-green-100 text-green-800 rounded-lg font-semibold flex items-center gap-2">
                            <CheckCircle size={16} />
                            Converted
                          </span>
                        </>
                      ) : (
                        <button
                          onClick={() => convertComponent(service.name)}
                          disabled={converting === service.name}
                          className="px-4 py-2 bg-jade-gold text-jade-blue-dark rounded-lg hover:bg-jade-gold-dark font-semibold flex items-center gap-2 disabled:opacity-50"
                        >
                          <Zap size={16} />
                          {converting === service.name ? 'Converting...' : 'Convert Entire Process'}
                        </button>
                      )}
                    </div>
                  </div>
                  
                  <BoomiProcessCanvas
                    flowSteps={service.flowSteps || []}
                    serviceName={service.name}
                    onViewStep={(step, idx) => viewStepDetails(step, idx, service.name)}
                    onConvertStep={(step, idx) => convertStep(step, idx, service.name)}
                    convertedSteps={serviceConvertedSteps}
                  />
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* View Modal */}
      {viewModal?.open && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50" onClick={() => setViewModal(null)}>
          <div className="bg-white rounded-lg p-6 max-w-4xl w-full max-h-[90vh] overflow-auto shadow-2xl" onClick={(e) => e.stopPropagation()}>
            <div className="flex items-center justify-between mb-4 pb-4 border-b">
              <h2 className="text-2xl font-bold text-jade-blue">{viewModal.title}</h2>
              <button onClick={() => setViewModal(null)} className="text-gray-500 hover:text-gray-700">
                <X size={24} />
              </button>
            </div>
            
            {viewModal.content.files ? (
              <div>
                <div className="mb-4">
                  <h3 className="font-semibold text-jade-blue mb-2">Source Files:</h3>
                  {Object.entries(viewModal.content.files).map(([filename, content]) => (
                    <div key={filename} className="mb-4">
                      <div className="font-medium text-sm text-gray-700 mb-1">{filename}</div>
                      <pre className="bg-gray-50 p-4 rounded border text-xs overflow-auto max-h-60 font-mono">
                        {content as string}
                      </pre>
                    </div>
                  ))}
                </div>
              </div>
            ) : viewModal.content.step ? (
              <div>
                <div className="grid grid-cols-2 gap-4 mb-4">
                  <div>
                    <div className="font-semibold text-jade-blue">webMethods Step Type:</div>
                    <div className="text-lg">{viewModal.content.step.type}</div>
                  </div>
                  <div>
                    <div className="font-semibold text-jade-blue">Step Name:</div>
                    <div className="text-lg">{viewModal.content.step.name || 'N/A'}</div>
                  </div>
                </div>
                <div className="bg-jade-gold bg-opacity-20 p-4 rounded-lg">
                  <div className="font-semibold text-jade-blue">Boomi Equivalent:</div>
                  <div className="text-lg">{viewModal.content.boomiMapping}</div>
                </div>
              </div>
            ) : (
              <pre className="bg-gray-50 p-4 rounded border text-sm overflow-auto max-h-96 font-mono">
                {JSON.stringify(viewModal.content, null, 2)}
              </pre>
            )}
            
            <div className="mt-6 flex justify-end">
              <button
                onClick={() => setViewModal(null)}
                className="px-6 py-2 border-2 border-gray-300 rounded-lg hover:bg-gray-50 font-medium"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
