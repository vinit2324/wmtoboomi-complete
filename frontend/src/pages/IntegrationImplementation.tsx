import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { ArrowLeft, Database, FileText, GitMerge, Zap, CheckCircle, Clock, Download, Upload, Eye, X, Loader2 } from 'lucide-react';
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
  const [pushing, setPushing] = useState<string | null>(null);
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

  const convertComponent = async (componentName: string, componentType: string) => {
    setConverting(componentName);
    try {
      const response = await axios.post('http://localhost:7201/api/conversions/convert', {
        projectId: projectId,
        serviceName: componentName
      });

      if (response.data.boomiXml) {
        setConversions(prev => new Map(prev).set(componentName, response.data));
        setConvertedComponents(prev => new Set(prev).add(componentName));
        showToast(`Converted ${componentName} successfully!`, 'success');
      }
    } catch (error: any) {
      showToast(`Conversion failed: ${error.message}`, 'error');
    } finally {
      setConverting(null);
    }
  };

  const convertAllComponents = async () => {
    const allDocuments = project?.parsedData?.documents || [];
    const sourceDocuments = integration?.sourceDocuments || allDocuments.slice(0, Math.ceil(allDocuments.length / 2));
    const targetDocuments = integration?.targetDocuments || allDocuments.slice(Math.ceil(allDocuments.length / 2));
    
    const allItems = [
      ...sourceDocuments.map((d: any) => ({ name: d.name || d, type: 'profile' })),
      ...targetDocuments.map((d: any) => ({ name: d.name || d, type: 'profile' })),
      ...(integration?.services || []).map((s: any) => ({ name: s.name, type: 'process' }))
    ];

    for (const item of allItems) {
      if (!convertedComponents.has(item.name)) {
        await convertComponent(item.name, item.type);
        await new Promise(resolve => setTimeout(resolve, 500));
      }
    }
  };

  const viewConvertedXml = (componentName: string) => {
    const conversion = conversions.get(componentName);
    if (conversion) {
      setViewModal({
        open: true,
        title: `${componentName} - Boomi XML`,
        content: conversion.boomiXml
      });
    }
  };

  const downloadXml = (componentName: string) => {
    const conversion = conversions.get(componentName);
    if (!conversion) return;
    
    const blob = new Blob([conversion.boomiXml], { type: 'application/xml' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${componentName.split('/').pop()}_boomi.xml`;
    a.click();
    URL.revokeObjectURL(url);
    showToast('XML downloaded successfully', 'info');
  };

  // Push to Boomi - NO frontend credential check, let backend handle it
  const pushToBoomi = async (componentName: string) => {
    const conversion = conversions.get(componentName);
    if (!conversion) {
      showToast('Please convert the component first', 'warning');
      return;
    }
    
    setPushing(componentName);
    
    try {
      const response = await axios.post('http://localhost:7201/api/conversions/push-to-boomi', {
        projectId: projectId,
        componentXml: conversion.boomiXml,
        componentName: componentName
      });

      if (response.data.success) {
        showToast(`Successfully pushed to Boomi! Component ID: ${response.data.componentId}`, 'success');
      } else {
        showToast(`Push failed: ${response.data.message}`, 'error');
      }
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || error.message || 'Unknown error';
      showToast(`Push error: ${errorMessage}`, 'error');
    } finally {
      setPushing(null);
    }
  };

  const showStepInfo = (step: any) => {
    showToast(`Step: ${step.type} - ${
      {
        'MAP': 'Map Shape - Data transformation',
        'BRANCH': 'Decision Shape - Conditional routing',
        'LOOP': 'ForEach Shape - Iterate over data',
        'INVOKE': 'Connector call',
        'SEQUENCE': 'Try/Catch Shape - Error handling',
        'EXIT': 'Stop Shape - End process'
      }[step.type] || 'Business Rules Shape'
    }`, 'info');
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
  const sourceDocuments = integration.sourceDocuments || allDocuments.slice(0, Math.ceil(allDocuments.length / 2));
  const targetDocuments = integration.targetDocuments || allDocuments.slice(Math.ceil(allDocuments.length / 2));

  const totalComponents = integrationServices.length + sourceDocuments.length + targetDocuments.length;
  const convertedCount = convertedComponents.size;

  return (
    <div className="p-6">
      {/* Header */}
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
        <div className="mt-2 text-sm opacity-90">{convertedCount} of {totalComponents} components converted</div>
        
        <button 
          onClick={convertAllComponents}
          className="mt-4 px-6 py-2 bg-jade-gold text-jade-blue font-semibold rounded-lg hover:bg-yellow-400 transition-colors"
        >
          Convert All to Boomi
        </button>
      </div>

      {/* Step 1: Connectors */}
      <div className="bg-white rounded-lg shadow-md mb-6 overflow-hidden">
        <div className="bg-gray-50 px-6 py-4 flex items-center gap-4 border-b">
          <div className="w-10 h-10 bg-jade-blue text-white rounded-full flex items-center justify-center font-bold">1</div>
          <div>
            <h3 className="text-xl font-bold text-jade-blue">Create Connectors</h3>
            <p className="text-gray-600">Set up connections for EDI</p>
          </div>
        </div>
        <div className="p-6">
          <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
            <div className="flex items-center gap-3">
              <Database className="text-purple-600" size={24} />
              <div>
                <div className="font-semibold">EDI Connector</div>
                <div className="text-sm text-gray-500">Connection configuration for EDI</div>
              </div>
            </div>
            <button className="px-4 py-2 bg-jade-blue text-white rounded-lg hover:bg-jade-blue-dark">
              Configure Manually
            </button>
          </div>
        </div>
      </div>

      {/* Step 2: Source Profiles */}
      <div className="bg-white rounded-lg shadow-md mb-6 overflow-hidden">
        <div className="bg-gray-50 px-6 py-4 flex items-center gap-4 border-b">
          <div className="w-10 h-10 bg-jade-blue text-white rounded-full flex items-center justify-center font-bold">2</div>
          <div>
            <h3 className="text-xl font-bold text-jade-blue">Create Source Profiles</h3>
            <p className="text-gray-600">Define incoming data structures ({sourceDocuments.length} profiles)</p>
          </div>
        </div>
        <div className="p-6 space-y-4">
          {sourceDocuments.map((doc: any, idx: number) => {
            const docName = doc.name || doc;
            const isConverted = convertedComponents.has(docName);
            const isConverting = converting === docName;
            const isPushing = pushing === docName;
            
            return (
              <div key={idx} className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                <div className="flex items-center gap-3">
                  <FileText className="text-blue-600" size={24} />
                  <div>
                    <div className="font-semibold">{docName.split('/').pop()}</div>
                    <div className="text-sm text-gray-500">{doc.fields?.length || 0} fields • Source Profile</div>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  {isConverted ? (
                    <>
                      <button onClick={() => viewConvertedXml(docName)} className="p-2 bg-jade-blue text-white rounded-lg hover:bg-jade-blue-dark" title="View XML">
                        <Eye size={18} />
                      </button>
                      <button onClick={() => downloadXml(docName)} className="p-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700" title="Download XML">
                        <Download size={18} />
                      </button>
                      <button 
                        onClick={() => pushToBoomi(docName)} 
                        disabled={isPushing}
                        className="p-2 bg-jade-gold text-jade-blue rounded-lg hover:bg-yellow-400 disabled:opacity-50" 
                        title="Push to Boomi"
                      >
                        {isPushing ? <Loader2 size={18} className="animate-spin" /> : <Upload size={18} />}
                      </button>
                      <div className="p-2 text-green-600"><CheckCircle size={18} /></div>
                    </>
                  ) : (
                    <button 
                      onClick={() => convertComponent(docName, 'profile')}
                      disabled={isConverting}
                      className="px-4 py-2 bg-jade-gold text-jade-blue rounded-lg hover:bg-yellow-400 font-semibold disabled:opacity-50"
                    >
                      {isConverting ? 'Converting...' : 'Convert'}
                    </button>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Step 3: Target Profiles */}
      <div className="bg-white rounded-lg shadow-md mb-6 overflow-hidden">
        <div className="bg-gray-50 px-6 py-4 flex items-center gap-4 border-b">
          <div className="w-10 h-10 bg-jade-blue text-white rounded-full flex items-center justify-center font-bold">3</div>
          <div>
            <h3 className="text-xl font-bold text-jade-blue">Create Target Profiles</h3>
            <p className="text-gray-600">Define outgoing data structures ({targetDocuments.length} profiles)</p>
          </div>
        </div>
        <div className="p-6 space-y-4">
          {targetDocuments.map((doc: any, idx: number) => {
            const docName = doc.name || doc;
            const isConverted = convertedComponents.has(docName);
            const isConverting = converting === docName;
            const isPushing = pushing === docName;
            
            return (
              <div key={idx} className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                <div className="flex items-center gap-3">
                  <FileText className="text-green-600" size={24} />
                  <div>
                    <div className="font-semibold">{docName.split('/').pop()}</div>
                    <div className="text-sm text-gray-500">{doc.fields?.length || 0} fields • Target Profile</div>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  {isConverted ? (
                    <>
                      <button onClick={() => viewConvertedXml(docName)} className="p-2 bg-jade-blue text-white rounded-lg hover:bg-jade-blue-dark" title="View XML">
                        <Eye size={18} />
                      </button>
                      <button onClick={() => downloadXml(docName)} className="p-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700" title="Download XML">
                        <Download size={18} />
                      </button>
                      <button 
                        onClick={() => pushToBoomi(docName)} 
                        disabled={isPushing}
                        className="p-2 bg-jade-gold text-jade-blue rounded-lg hover:bg-yellow-400 disabled:opacity-50" 
                        title="Push to Boomi"
                      >
                        {isPushing ? <Loader2 size={18} className="animate-spin" /> : <Upload size={18} />}
                      </button>
                      <div className="p-2 text-green-600"><CheckCircle size={18} /></div>
                    </>
                  ) : (
                    <button 
                      onClick={() => convertComponent(docName, 'profile')}
                      disabled={isConverting}
                      className="px-4 py-2 bg-jade-gold text-jade-blue rounded-lg hover:bg-yellow-400 font-semibold disabled:opacity-50"
                    >
                      {isConverting ? 'Converting...' : 'Convert'}
                    </button>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Step 4: Build Process */}
      <div className="bg-white rounded-lg shadow-md mb-6 overflow-hidden">
        <div className="bg-gray-50 px-6 py-4 flex items-center gap-4 border-b">
          <div className="w-10 h-10 bg-jade-blue text-white rounded-full flex items-center justify-center font-bold">4</div>
          <div>
            <h3 className="text-xl font-bold text-jade-blue">Build Process</h3>
            <p className="text-gray-600">Create Boomi process from flow services</p>
          </div>
        </div>
        <div className="p-6 space-y-6">
          {integrationServices.map((service: any, idx: number) => {
            const isConverted = convertedComponents.has(service.name);
            const isConverting = converting === service.name;
            const isPushing = pushing === service.name;
            
            return (
              <div key={idx} className="border rounded-lg overflow-hidden">
                <div className="flex items-center justify-between p-4 bg-gray-50">
                  <div className="flex items-center gap-3">
                    <GitMerge className="text-jade-blue" size={24} />
                    <div>
                      <div className="font-semibold">{service.name.split('/').pop()}</div>
                      <div className="text-sm text-gray-500">
                        {service.steps?.length || 0} steps • {service.type}
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    {isConverted ? (
                      <>
                        <button onClick={() => viewConvertedXml(service.name)} className="p-2 bg-jade-blue text-white rounded-lg hover:bg-jade-blue-dark" title="View XML">
                          <Eye size={18} />
                        </button>
                        <button onClick={() => downloadXml(service.name)} className="p-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700" title="Download XML">
                          <Download size={18} />
                        </button>
                        <button 
                          onClick={() => pushToBoomi(service.name)} 
                          disabled={isPushing}
                          className="p-2 bg-jade-gold text-jade-blue rounded-lg hover:bg-yellow-400 disabled:opacity-50" 
                          title="Push to Boomi"
                        >
                          {isPushing ? <Loader2 size={18} className="animate-spin" /> : <Upload size={18} />}
                        </button>
                        <div className="p-2 text-green-600"><CheckCircle size={18} /></div>
                      </>
                    ) : (
                      <button 
                        onClick={() => convertComponent(service.name, 'process')}
                        disabled={isConverting}
                        className="px-4 py-2 bg-jade-gold text-jade-blue rounded-lg hover:bg-yellow-400 font-semibold disabled:opacity-50"
                      >
                        {isConverting ? 'Converting...' : 'Convert to Boomi Process'}
                      </button>
                    )}
                  </div>
                </div>
                
                {/* Flow steps visualization */}
                {service.steps && service.steps.length > 0 && (
                  <div className="p-4 bg-white">
                    <div className="flex flex-wrap gap-2">
                      {service.steps.slice(0, 10).map((step: any, stepIdx: number) => (
                        <button
                          key={stepIdx}
                          onClick={() => showStepInfo(step)}
                          className={`px-3 py-1 rounded-full text-sm font-medium transition-colors ${
                            step.type === 'MAP' ? 'bg-blue-100 text-blue-800 hover:bg-blue-200' :
                            step.type === 'BRANCH' ? 'bg-yellow-100 text-yellow-800 hover:bg-yellow-200' :
                            step.type === 'LOOP' ? 'bg-purple-100 text-purple-800 hover:bg-purple-200' :
                            step.type === 'INVOKE' ? 'bg-green-100 text-green-800 hover:bg-green-200' :
                            step.type === 'SEQUENCE' ? 'bg-red-100 text-red-800 hover:bg-red-200' :
                            'bg-gray-100 text-gray-800 hover:bg-gray-200'
                          }`}
                        >
                          {step.type}
                        </button>
                      ))}
                      {service.steps.length > 10 && (
                        <span className="px-3 py-1 text-sm text-gray-500">+{service.steps.length - 10} more</span>
                      )}
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* XML View Modal */}
      {viewModal?.open && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl w-full max-w-4xl max-h-[80vh] flex flex-col">
            <div className="flex items-center justify-between p-4 border-b">
              <h3 className="text-lg font-bold">{viewModal.title}</h3>
              <button onClick={() => setViewModal(null)} className="p-2 hover:bg-gray-100 rounded">
                <X size={20} />
              </button>
            </div>
            <div className="flex-1 overflow-auto p-4">
              <pre className="text-sm bg-gray-50 p-4 rounded-lg overflow-x-auto whitespace-pre-wrap">
                {viewModal.content}
              </pre>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
