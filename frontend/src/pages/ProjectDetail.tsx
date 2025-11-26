import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { ArrowLeft, Package, FileCode, Database, Zap, Eye, Download, Upload, X, File, GitBranch } from 'lucide-react';

export default function ProjectDetail() {
  const { projectId } = useParams();
  const navigate = useNavigate();
  const [project, setProject] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [selectedService, setSelectedService] = useState<any>(null);
  const [sourceFiles, setSourceFiles] = useState<any>(null);
  const [loadingFiles, setLoadingFiles] = useState(false);
  const [convertedXml, setConvertedXml] = useState('');
  const [showConversionModal, setShowConversionModal] = useState(false);
  const [converting, setConverting] = useState(false);
  const [pushing, setPushing] = useState(false);
  const [activeTab, setActiveTab] = useState('node.ndf');

  useEffect(() => {
    loadProject();
  }, [projectId]);

  const loadProject = async () => {
    try {
      const response = await axios.get(`http://localhost:7201/api/projects/${projectId}`);
      setProject(response.data);
    } catch (error) {
      console.error('Error:', error);
    } finally {
      setLoading(false);
    }
  };

  const viewService = async (service: any) => {
    setSelectedService(service);
    setConvertedXml('');
    setShowConversionModal(false);
    setLoadingFiles(true);
    
    try {
      const response = await axios.get(
        `http://localhost:7201/api/conversions/view-source/${projectId}?service_name=${encodeURIComponent(service.name)}`
      );
      setSourceFiles(response.data.files);
      
      if (response.data.files['flow.xml']) setActiveTab('flow.xml');
      else if (response.data.files['node.ndf']) setActiveTab('node.ndf');
      else if (response.data.files['schema.ndf']) setActiveTab('schema.ndf');
      else setActiveTab('node.ndf');
      
    } catch (error) {
      console.error('Error loading files:', error);
      alert('Failed to load source files');
    } finally {
      setLoadingFiles(false);
    }
  };

  const convertService = async (service: any) => {
    setConverting(true);
    try {
      const response = await axios.post('http://localhost:7201/api/conversions/convert', {
        projectId: projectId,
        serviceName: service.name
      });

      setConvertedXml(response.data.boomiXml);
      setSelectedService(service);
      setShowConversionModal(true);
      
    } catch (error: any) {
      alert(`❌ Conversion failed: ${error.response?.data?.detail || error.message}`);
    } finally {
      setConverting(false);
    }
  };

  const downloadXml = () => {
    const blob = new Blob([convertedXml], { type: 'application/xml' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${selectedService.name.split('/').pop()}_boomi.xml`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const pushToBoomi = async () => {
    if (!confirm('Push this component to Boomi now?')) return;
    
    setPushing(true);
    try {
      const response = await axios.post('http://localhost:7201/api/conversions/push-to-boomi', {
        projectId: projectId,
        componentXml: convertedXml,
        componentName: selectedService.name
      });

      if (response.data.success) {
        alert(`✅ Successfully pushed to Boomi!\n\nComponent ID: ${response.data.componentId}`);
      } else {
        alert(`❌ Push failed: ${response.data.message}`);
      }
    } catch (error: any) {
      alert(`❌ Push error: ${error.message}`);
    } finally {
      setPushing(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-jade-blue"></div>
      </div>
    );
  }

  if (!project) {
    return <div className="p-6">Project not found</div>;
  }

  const services = project.parsedData?.services || [];
  const documents = project.parsedData?.documents || [];
  const stats = project.packageInfo?.services || {};

  return (
    <div className="p-6">
      <div className="flex items-center gap-4 mb-6">
        <button onClick={() => navigate('/projects')} className="p-2 hover:bg-gray-100 rounded">
          <ArrowLeft size={24} />
        </button>
        <div>
          <h1 className="text-3xl font-bold text-jade-blue">{project.packageName}</h1>
          <p className="text-gray-600">Uploaded: {new Date(project.uploadedAt).toLocaleString()}</p>
        </div>
      </div>

      <div className="grid grid-cols-4 gap-4 mb-6">
        <div className="bg-white p-6 rounded-lg shadow-lg border-l-4 border-jade-blue">
          <div className="flex items-center gap-3">
            <Package className="text-jade-blue" size={28} />
            <div>
              <div className="text-3xl font-bold text-jade-blue">{stats.total || 0}</div>
              <div className="text-sm text-gray-600 font-medium">Services</div>
            </div>
          </div>
        </div>
        <div className="bg-white p-6 rounded-lg shadow-lg border-l-4 border-jade-gold">
          <div className="flex items-center gap-3">
            <FileCode className="text-jade-gold" size={28} />
            <div>
              <div className="text-3xl font-bold text-jade-blue">{stats.flow || 0}</div>
              <div className="text-sm text-gray-600 font-medium">Flows</div>
            </div>
          </div>
        </div>
        <div className="bg-white p-6 rounded-lg shadow-lg border-l-4 border-purple-500">
          <div className="flex items-center gap-3">
            <Database className="text-purple-500" size={28} />
            <div>
              <div className="text-3xl font-bold text-jade-blue">{stats.adapter || 0}</div>
              <div className="text-sm text-gray-600 font-medium">Adapters</div>
            </div>
          </div>
        </div>
        <div className="bg-white p-6 rounded-lg shadow-lg border-l-4 border-green-500">
          <div className="flex items-center gap-3">
            <FileCode className="text-green-500" size={28} />
            <div>
              <div className="text-3xl font-bold text-jade-blue">{stats.document || 0}</div>
              <div className="text-sm text-gray-600 font-medium">Documents</div>
            </div>
          </div>
        </div>
      </div>

      <div className="mb-6">
        <button
          onClick={() => navigate(`/projects/${projectId}/integrations`)}
          className="bg-gradient-to-r from-jade-blue to-jade-blue-light text-white px-6 py-3 rounded-lg font-semibold flex items-center gap-2 hover:shadow-lg transition-all"
        >
          <GitBranch size={20} />
          View Integration Patterns & Implementation Steps
        </button>
      </div>

      <div className="bg-white rounded-lg shadow-lg mb-6">
        <div className="p-6 border-b border-gray-200">
          <h2 className="text-xl font-bold text-jade-blue">Services ({services.length})</h2>
        </div>
        <div className="p-4 space-y-2 max-h-[400px] overflow-auto">
          {services.map((service: any, i: number) => (
            <div key={i} className="flex items-center justify-between p-4 border rounded-lg hover:bg-jade-gray transition-all">
              <div>
                <div className="font-semibold text-jade-blue">{service.name}</div>
                <div className="text-sm text-gray-600">
                  {service.type} • {service.complexity} • {service.flowSteps?.length || 0} steps
                </div>
              </div>
              <div className="flex gap-2">
                <button
                  onClick={() => viewService(service)}
                  className="px-4 py-2 border-2 border-jade-blue text-jade-blue rounded-lg text-sm hover:bg-jade-blue hover:text-white transition-all font-medium flex items-center gap-2"
                >
                  <Eye size={16} />
                  View Source
                </button>
                <button
                  onClick={() => convertService(service)}
                  disabled={converting}
                  className="bg-jade-gold text-jade-blue-dark px-4 py-2 rounded-lg text-sm hover:bg-jade-gold-dark transition-all font-semibold flex items-center gap-2 disabled:opacity-50"
                >
                  <Zap size={16} />
                  {converting ? 'Converting...' : 'Convert'}
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>

      {documents.length > 0 && (
        <div className="bg-white rounded-lg shadow-lg">
          <div className="p-6 border-b border-gray-200">
            <h2 className="text-xl font-bold text-jade-blue">Documents ({documents.length})</h2>
          </div>
          <div className="p-4 space-y-2 max-h-[300px] overflow-auto">
            {documents.map((doc: any, i: number) => (
              <div key={i} className="flex items-center justify-between p-4 border rounded-lg hover:bg-jade-gray transition-all">
                <div>
                  <div className="font-semibold text-jade-blue">{doc.name}</div>
                  <div className="text-sm text-gray-600">{doc.fields?.length || 0} fields</div>
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={() => viewService(doc)}
                    className="px-4 py-2 border-2 border-jade-blue text-jade-blue rounded-lg text-sm hover:bg-jade-blue hover:text-white transition-all font-medium flex items-center gap-2"
                  >
                    <Eye size={16} />
                    View Source
                  </button>
                  <button
                    onClick={() => convertService(doc)}
                    disabled={converting}
                    className="bg-jade-gold text-jade-blue-dark px-4 py-2 rounded-lg text-sm hover:bg-jade-gold-dark transition-all font-semibold flex items-center gap-2"
                  >
                    <Zap size={16} />
                    Convert
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {selectedService && !showConversionModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50" onClick={() => { setSelectedService(null); setSourceFiles(null); }}>
          <div className="bg-white rounded-lg p-6 max-w-6xl w-full max-h-[90vh] overflow-auto shadow-2xl" onClick={(e) => e.stopPropagation()}>
            <div className="flex items-center justify-between mb-4 pb-4 border-b border-gray-200">
              <h2 className="text-2xl font-bold text-jade-blue">{selectedService.name}</h2>
              <button onClick={() => { setSelectedService(null); setSourceFiles(null); }} className="text-gray-500 hover:text-gray-700">
                <X size={24} />
              </button>
            </div>
            
            {loadingFiles ? (
              <div className="flex items-center justify-center py-12">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-jade-blue"></div>
              </div>
            ) : sourceFiles ? (
              <div>
                <div className="flex gap-2 mb-4 border-b border-gray-200">
                  {Object.keys(sourceFiles).map((filename) => (
                    <button
                      key={filename}
                      onClick={() => setActiveTab(filename)}
                      className={`px-4 py-3 text-sm font-semibold flex items-center gap-2 transition-all ${
                        activeTab === filename
                          ? 'border-b-2 border-jade-blue text-jade-blue'
                          : 'text-gray-600 hover:text-jade-blue'
                      }`}
                    >
                      <File size={16} />
                      {filename}
                    </button>
                  ))}
                </div>
                
                <div className="bg-gray-50 p-4 rounded-lg border border-gray-200">
                  <pre className="text-xs overflow-auto max-h-[500px] font-mono text-gray-800">
                    <code>{sourceFiles[activeTab] || 'No content'}</code>
                  </pre>
                </div>
              </div>
            ) : (
              <p className="text-gray-500 text-center py-8">No source files available</p>
            )}
            
            <div className="mt-6 flex gap-3 pt-4 border-t border-gray-200">
              <button
                onClick={() => convertService(selectedService)}
                className="bg-jade-gold text-jade-blue-dark px-6 py-3 rounded-lg hover:bg-jade-gold-dark transition-all font-semibold"
              >
                Convert to Boomi
              </button>
              <button
                onClick={() => { setSelectedService(null); setSourceFiles(null); }}
                className="border-2 border-gray-300 text-gray-700 px-6 py-3 rounded-lg hover:bg-gray-50 transition-all font-medium"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {showConversionModal && convertedXml && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50" onClick={() => setShowConversionModal(false)}>
          <div className="bg-white rounded-lg p-6 max-w-6xl w-full max-h-[90vh] overflow-auto shadow-2xl" onClick={(e) => e.stopPropagation()}>
            <div className="flex items-center justify-between mb-4 pb-4 border-b border-gray-200">
              <h2 className="text-2xl font-bold text-jade-blue">Boomi XML - {selectedService.name}</h2>
              <button onClick={() => setShowConversionModal(false)} className="text-gray-500 hover:text-gray-700">
                <X size={24} />
              </button>
            </div>
            
            <div className="mb-6">
              <pre className="bg-gray-50 p-4 rounded-lg text-xs overflow-auto max-h-96 border border-gray-200 font-mono text-gray-800">
                <code>{convertedXml}</code>
              </pre>
            </div>
            
            <div className="flex gap-3 pt-4 border-t border-gray-200">
              <button
                onClick={downloadXml}
                className="bg-jade-blue text-white px-6 py-3 rounded-lg hover:bg-jade-blue-dark transition-all font-semibold flex items-center gap-2 shadow-md"
              >
                <Download size={20} />
                Download XML
              </button>
              <button
                onClick={pushToBoomi}
                disabled={pushing}
                className="bg-jade-gold text-jade-blue-dark px-6 py-3 rounded-lg hover:bg-jade-gold-dark transition-all font-semibold flex items-center gap-2 disabled:opacity-50 shadow-md"
              >
                <Upload size={20} />
                {pushing ? 'Pushing...' : 'Push to Boomi'}
              </button>
              <button
                onClick={() => setShowConversionModal(false)}
                className="border-2 border-gray-300 text-gray-700 px-6 py-3 rounded-lg hover:bg-gray-50 transition-all font-medium"
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
