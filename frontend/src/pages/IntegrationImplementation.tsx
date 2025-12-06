import React, { useState, useEffect, useMemo } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { 
  ArrowLeft, 
  CheckCircle, 
  Circle, 
  Download, 
  Upload, 
  Eye, 
  Code, 
  FileText, 
  Server, 
  Database, 
  GitMerge,
  Globe,
  Zap,
  AlertTriangle,
  Info,
  ChevronDown,
  ChevronRight,
  ExternalLink,
  Clipboard,
  BookOpen,
  Copy
} from 'lucide-react';

const Toast = ({ message, type, onClose }: { message: string; type: 'success' | 'error' | 'info'; onClose: () => void }) => {
  useEffect(() => {
    const timer = setTimeout(onClose, 3000);
    return () => clearTimeout(timer);
  }, [onClose]);

  const bgColor = type === 'success' ? 'bg-green-500' : type === 'error' ? 'bg-red-500' : 'bg-blue-500';
  
  return (
    <div className={`fixed bottom-4 right-4 ${bgColor} text-white px-6 py-3 rounded-lg shadow-lg z-50 flex items-center gap-2`}>
      {type === 'success' && <CheckCircle size={20} />}
      {type === 'error' && <AlertTriangle size={20} />}
      {type === 'info' && <Info size={20} />}
      {message}
    </div>
  );
};

function detectPackageType(project: any): string {
  if (!project?.parsedData) return 'GENERAL';
  const parsedData = project.parsedData;
  if (project.packageType) return project.packageType;
  const restResources = parsedData.restResources || [];
  const restOperations = parsedData.restOperations || [];
  const restEndpoints = parsedData.restEndpoints || [];
  if (restResources.length > 0 || restOperations.length > 0 || restEndpoints.length > 0) {
    return 'REST_API';
  }
  const allContent = JSON.stringify(parsedData).toLowerCase();
  if (allContent.includes('restv2') || allContent.includes('pub.client:http') || 
      allContent.includes('application/json') || allContent.includes('httpconnection')) {
    return 'REST_API';
  }
  if (allContent.includes('wm.b2b.edi') || allContent.includes('edi850') || 
      allContent.includes('x12') || allContent.includes('edifact')) {
    return 'B2B_EDI';
  }
  return 'GENERAL';
}

function extractBaseUrl(parsedData: any): string {
  const globalVars = parsedData.globalVariables || [];
  for (const gv of globalVars) {
    if (gv.name?.toLowerCase().includes('url') || gv.name?.toLowerCase().includes('base')) {
      if (gv.value && gv.value.startsWith('http')) {
        return gv.value;
      }
    }
  }
  const services = parsedData.services || [];
  for (const svc of services) {
    const code = (svc.code || '') + (svc.javaCode || '');
    const urlMatch = code.match(/https?:\/\/[a-zA-Z0-9.-]+(?:\/[a-zA-Z0-9.\/_-]*)?/);
    if (urlMatch) {
      return urlMatch[0].replace(/['"]/g, '');
    }
  }
  return 'https://api.example.com';
}

function extractEnvironmentExtensions(parsedData: any): string[] {
  const globalVars = parsedData.globalVariables || [];
  const envExts: string[] = [];
  
  for (const gv of globalVars) {
    const name = gv.name || gv.key || '';
    if (name) {
      // Convert to environment extension format
      const extName = name.toUpperCase().replace(/[^A-Z0-9]/g, '_');
      envExts.push(extName);
    }
  }
  
  // If no global vars found, return empty (no hardcoded defaults)
  return envExts;
}

function extractPackageName(project: any): string {
  const pkgName = project?.packageName || 'Integration';
  // Remove common prefixes like CPRI_DIG_API001_
  const cleanName = pkgName.replace(/^[A-Z]+_[A-Z]+_[A-Z0-9]+_/, '');
  return cleanName.replace(/\s+/g, '_');
}

function getShortName(fullPath: string): string {
  return fullPath?.split('/').pop()?.split('.').pop() || fullPath || '';
}

// Check if a service is a subprocess (not a main REST endpoint)
function isSubprocess(svc: any): boolean {
  const name = getShortName(svc.name || '').toLowerCase();
  const fullName = (svc.name || '').toLowerCase();
  
  // Patterns that indicate a subprocess
  return name.startsWith('process') ||
         fullName.includes('processflows') ||
         fullName.includes('subprocess') ||
         fullName.includes('subflow') ||
         fullName.includes('/sub/');
}

// Check if a service is a main flow (REST endpoint)
function isMainFlow(svc: any): boolean {
  const name = getShortName(svc.name || '').toLowerCase();
  const fullName = (svc.name || '').toLowerCase();
  
  // Must be in mainFlows folder OR have REST-like naming AND not be a subprocess
  const inMainFlows = fullName.includes('mainflows');
  const hasRestNaming = name.startsWith('find') || 
                        name.startsWith('get') || 
                        name.startsWith('create') || 
                        name.startsWith('update') || 
                        name.startsWith('delete') ||
                        name.startsWith('search') ||
                        name.startsWith('list');
  
  return (inMainFlows || hasRestNaming) && !isSubprocess(svc);
}

function getImplementationSteps(packageType: string, project: any, integration: any) {
  const parsedData = project?.parsedData || {};
  const services = parsedData.services || [];
  const documents = parsedData.documents || [];
  const globalVars = parsedData.globalVariables || [];
  
  const flowServices = services.filter((s: any) => s.type === 'FlowService');
  const javaServices = services.filter((s: any) => s.type === 'JavaService');
  
  // Separate MAIN flows from SUBPROCESSES
  const mainFlows = flowServices.filter((s: any) => isMainFlow(s));
  const subprocessFlows = flowServices.filter((s: any) => isSubprocess(s));
  const otherFlows = flowServices.filter((s: any) => !isMainFlow(s) && !isSubprocess(s));
  
  // Use main flows, or fall back to non-subprocess flows
  const effectiveMainFlows = mainFlows.length > 0 ? mainFlows : otherFlows;
  
  // Java services that are utility/URI builders
  const utilityJavaServices = javaServices.filter((s: any) => {
    const name = getShortName(s.name || '').toLowerCase();
    return name.includes('generateuri') || name.includes('buildurl') || 
           name.includes('builduri') || name.includes('utility') ||
           name.includes('helper');
  });
  
  const baseUrl = extractBaseUrl(parsedData);
  const packageName = extractPackageName(project);
  const envExtensions = extractEnvironmentExtensions(parsedData);
  const connectionName = `${packageName}_HTTP_Connection`;
  
  if (packageType === 'REST_API') {
    // HTTP Operations - ONLY for MAIN flows, NOT subprocesses
    const httpOperationsMap = new Map<string, any>();
    effectiveMainFlows.forEach((svc: any) => {
      const svcShortName = getShortName(svc.name);
      const opName = `${svcShortName}_Operation`;
      
      if (!httpOperationsMap.has(opName)) {
        // Detect HTTP method from service name
        let method = 'GET';
        const nameLower = svcShortName.toLowerCase();
        if (nameLower.includes('create') || nameLower.includes('add') || nameLower.includes('post')) {
          method = 'POST';
        } else if (nameLower.includes('update') || nameLower.includes('put')) {
          method = 'PUT';
        } else if (nameLower.includes('delete')) {
          method = 'DELETE';
        }
        
        httpOperationsMap.set(opName, {
          name: opName,
          type: 'httpOperation',
          description: `HTTP ${method} operation for ${svcShortName}`,
          serviceName: svc.name,
          method: method
        });
      }
    });
    const httpOperations = Array.from(httpOperationsMap.values());
    
    // REQUEST PROFILES - from main flows AND subprocesses (they all can have input signatures)
    const requestProfilesMap = new Map<string, any>();
    [...effectiveMainFlows, ...subprocessFlows].forEach((svc: any) => {
      const svcShortName = getShortName(svc.name);
      const profileName = `${svcShortName}_Request`;
      
      let fieldCount = 0;
      if (svc.inputSignature && typeof svc.inputSignature === 'object') {
        fieldCount = Object.keys(svc.inputSignature).length;
      } else if (svc.inputs && Array.isArray(svc.inputs)) {
        fieldCount = svc.inputs.length;
      }
      
      if (!requestProfilesMap.has(profileName) && fieldCount > 0) {
        requestProfilesMap.set(profileName, {
          name: profileName,
          type: 'jsonProfile',
          description: `Request profile for ${svcShortName}`,
          fieldCount: fieldCount,
          serviceName: svc.name,
          isRequest: true
        });
      }
    });
    
    // Also check documents for input signatures
    documents.forEach((doc: any) => {
      const docName = doc.name || '';
      if (docName.toLowerCase().includes('inputsignature') || docName.toLowerCase().includes('input')) {
        const parentService = docName.split('/').slice(-2, -1)[0] || getShortName(docName);
        const profileName = `${parentService}_Request`;
        const fieldCount = doc.fields?.length || doc.fieldCount || 0;
        
        if (!requestProfilesMap.has(profileName) && fieldCount > 0) {
          requestProfilesMap.set(profileName, {
            name: profileName,
            type: 'jsonProfile',
            description: `Request profile for ${parentService}`,
            fieldCount: fieldCount,
            serviceName: docName,
            isRequest: true
          });
        }
      }
    });
    const requestProfiles = Array.from(requestProfilesMap.values());
    
    // RESPONSE PROFILES - from flows with output signatures
    const responseProfilesMap = new Map<string, any>();
    [...effectiveMainFlows, ...subprocessFlows].forEach((svc: any) => {
      const svcShortName = getShortName(svc.name);
      const profileName = `${svcShortName}_Response`;
      
      let fieldCount = 0;
      if (svc.outputSignature && typeof svc.outputSignature === 'object') {
        fieldCount = Object.keys(svc.outputSignature).length;
      } else if (svc.outputs && Array.isArray(svc.outputs)) {
        fieldCount = svc.outputs.length;
      }
      
      if (!responseProfilesMap.has(profileName) && fieldCount > 0) {
        responseProfilesMap.set(profileName, {
          name: profileName,
          type: 'jsonProfile',
          description: `Response profile for ${svcShortName}`,
          fieldCount: fieldCount,
          serviceName: svc.name,
          isRequest: false
        });
      }
    });
    
    // Also check documents for output signatures
    documents.forEach((doc: any) => {
      const docName = doc.name || '';
      if (docName.toLowerCase().includes('outputsignature') || docName.toLowerCase().includes('output')) {
        const parentService = docName.split('/').slice(-2, -1)[0] || getShortName(docName);
        const profileName = `${parentService}_Response`;
        const fieldCount = doc.fields?.length || doc.fieldCount || 0;
        
        if (!responseProfilesMap.has(profileName) && fieldCount > 0) {
          responseProfilesMap.set(profileName, {
            name: profileName,
            type: 'jsonProfile',
            description: `Response profile for ${parentService}`,
            fieldCount: fieldCount,
            serviceName: docName,
            isRequest: false
          });
        }
      }
    });
    const responseProfiles = Array.from(responseProfilesMap.values());
    
    // GROOVY SCRIPTS - from utility Java services
    const groovyScripts = utilityJavaServices.map((svc: any) => {
      const svcShortName = getShortName(svc.name);
      return {
        name: svcShortName,
        type: 'groovyScript',
        description: 'Groovy script converted from Java service',
        serviceName: svc.name
      };
    });
    
    // BOOMI PROCESSES - ALL flows (main + subprocess)
    const allProcesses = [...effectiveMainFlows, ...subprocessFlows].map((svc: any) => {
      const shortName = getShortName(svc.name);
      const isSub = isSubprocess(svc);
      return {
        name: shortName,
        type: 'process',
        description: `${svc.steps?.length || 0} steps • ${isSub ? 'Subprocess' : 'Main Flow'}`,
        serviceName: svc.name,
        steps: svc.steps || [],
        isSubprocess: isSub
      };
    });
    
    return [
      {
        stepNumber: 1,
        category: 'Create HTTP Connection',
        title: 'HTTP Connection',
        description: 'Set up HTTP connection for REST API calls',
        icon: Globe,
        iconColor: 'text-blue-600',
        automationLevel: 'AUTO',
        connectionName: connectionName,
        items: [{
          name: connectionName,
          type: 'httpConnection',
          description: `Base URL: ${baseUrl}`,
          url: baseUrl
        }]
      },
      {
        stepNumber: 2,
        category: 'Create HTTP Operations',
        title: 'HTTP Operations',
        description: `Define HTTP operations for REST endpoints (${httpOperations.length} operations)`,
        icon: Server,
        iconColor: 'text-purple-600',
        automationLevel: 'AUTO',
        items: httpOperations
      },
      {
        stepNumber: 3,
        category: 'Create Request Profiles',
        title: 'JSON Request Profiles',
        description: `Define request structures (${requestProfiles.length} profiles)`,
        icon: FileText,
        iconColor: 'text-blue-600',
        automationLevel: 'AUTO',
        items: requestProfiles
      },
      {
        stepNumber: 4,
        category: 'Create Response Profiles',
        title: 'JSON Response Profiles',
        description: `Define response structures (${responseProfiles.length} profiles)`,
        icon: FileText,
        iconColor: 'text-green-600',
        automationLevel: 'AUTO',
        items: responseProfiles
      },
      {
        stepNumber: 5,
        category: 'Create Groovy Scripts',
        title: 'Groovy Scripts',
        description: `Convert Java services to Groovy (${groovyScripts.length} scripts)`,
        icon: Code,
        iconColor: 'text-orange-600',
        automationLevel: 'SEMI',
        isGroovyScript: true,
        items: groovyScripts
      },
      {
        stepNumber: 6,
        category: 'Build Boomi Processes',
        title: 'Boomi Processes',
        description: `Create Boomi processes from flow services (${allProcesses.length} processes)`,
        icon: GitMerge,
        iconColor: 'text-jade-blue',
        automationLevel: 'SEMI',
        isImplementationGuide: true,
        connectionName: connectionName,
        envExtensions: envExtensions,
        items: allProcesses
      }
    ];
  }
  
  // Default for non-REST packages
  return [
    {
      stepNumber: 1,
      category: 'Create Connectors',
      title: 'Connector',
      description: 'Set up connection for integration',
      icon: Database,
      iconColor: 'text-blue-600',
      automationLevel: 'MANUAL',
      items: [{ name: 'Connection', type: 'connection', description: 'Integration connector' }]
    },
    {
      stepNumber: 2,
      category: 'Build Process',
      title: 'Boomi Processes',
      description: 'Create Boomi processes',
      icon: GitMerge,
      iconColor: 'text-jade-blue',
      automationLevel: 'SEMI',
      items: flowServices.map((svc: any) => ({
        name: getShortName(svc.name),
        type: 'process',
        description: `${svc.steps?.length || 0} steps`,
        serviceName: svc.name
      }))
    }
  ];
}

const ImplementationGuide = ({ process, allSteps, project }: { process: any; allSteps: any[]; project: any }) => {
  const [expanded, setExpanded] = useState(true);
  const processName = process.name;
  const nameLower = processName.toLowerCase();
  const isSub = process.isSubprocess;
  
  // Determine flow type for visual representation
  const isMainFindFlow = nameLower.includes('find') && !nameLower.includes('byid');
  const isByIdFlow = nameLower.includes('byid') || nameLower.includes('storeid');
  
  // Get connection info
  const connectionStep = allSteps.find(s => s.category.includes('Connection'));
  const connectionName = connectionStep?.connectionName || connectionStep?.items[0]?.name || 'HTTP Connection';
  
  // Get matching operation (only for main flows, not subprocesses)
  const httpOperations = allSteps.find(s => s.category.includes('HTTP Operations'))?.items || [];
  const matchingOperation = httpOperations.find((op: any) => 
    op.name.toLowerCase().replace('_operation', '') === processName.toLowerCase()
  );
  
  // Get matching request profile
  const requestProfiles = allSteps.find(s => s.category.includes('Request'))?.items || [];
  const matchingReqProfile = requestProfiles.find((p: any) => 
    p.name.toLowerCase().replace('_request', '') === processName.toLowerCase()
  );
  
  // Get matching response profile
  const responseProfiles = allSteps.find(s => s.category.includes('Response'))?.items || [];
  const matchingResProfile = responseProfiles.find((p: any) => 
    p.name.toLowerCase().replace('_response', '') === processName.toLowerCase()
  );
  
  // Get environment extensions
  const processStep = allSteps.find(s => s.isImplementationGuide);
  const envExtensions = processStep?.envExtensions || [];
  
  // Get groovy scripts for this flow
  const groovyScripts = allSteps.find(s => s.isGroovyScript)?.items || [];
  
  return (
    <div className="bg-gray-50 rounded-lg p-4 mb-3">
      <button onClick={() => setExpanded(!expanded)} className="flex items-center justify-between w-full text-left">
        <div className="flex items-center gap-3">
          <BookOpen className="text-jade-blue" size={20} />
          <div>
            <div className="font-semibold text-jade-blue flex items-center gap-2">
              {processName}
              {isSub && (
                <span className="text-xs px-2 py-0.5 bg-yellow-100 text-yellow-800 rounded">Subprocess</span>
              )}
              {!isSub && (
                <span className="text-xs px-2 py-0.5 bg-green-100 text-green-800 rounded">Main Flow</span>
              )}
            </div>
            <div className="text-sm text-gray-500">Implementation Guide</div>
          </div>
        </div>
        {expanded ? <ChevronDown size={20} /> : <ChevronRight size={20} />}
      </button>
      
      {expanded && (
        <div className="mt-4 space-y-4">
          {/* Process Flow Visualization */}
          <div className="bg-white p-4 rounded-lg border">
            <h4 className="font-semibold mb-3 flex items-center gap-2">
              <GitMerge size={16} className="text-jade-blue" />
              Process Flow
            </h4>
            
            {isSub ? (
              // Subprocess flow
              <div className="text-sm">
                <div className="bg-yellow-50 p-2 rounded mb-2 text-yellow-800 text-xs">
                  <strong>Subprocess:</strong> Called by main flows for shared processing logic
                </div>
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="px-2 py-1 bg-green-100 text-green-800 rounded">Start</span>
                  <span>→</span>
                  <span className="px-2 py-1 bg-blue-100 text-blue-800 rounded">Parse Request</span>
                  <span>→</span>
                  <span className="px-2 py-1 bg-yellow-100 text-yellow-800 rounded">Validate</span>
                  <span>→</span>
                  <span className="px-2 py-1 bg-purple-100 text-purple-800 rounded">Process Logic</span>
                  <span>→</span>
                  <span className="px-2 py-1 bg-red-100 text-red-800 rounded">Stop</span>
                </div>
              </div>
            ) : isMainFindFlow ? (
              // Main flow with decision routing
              <div className="text-sm space-y-2">
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="px-2 py-1 bg-green-100 text-green-800 rounded">Start</span>
                  <span>→</span>
                  <span className="px-2 py-1 bg-blue-100 text-blue-800 rounded">Set Properties</span>
                  <span>→</span>
                  <span className="px-2 py-1 bg-yellow-100 text-yellow-800 rounded">Decision (Route)</span>
                </div>
                <div className="ml-4 pl-4 border-l-2 border-gray-200 space-y-1">
                  {groovyScripts.filter((s: any) => s.name.toLowerCase().includes('coordinates')).map((s: any) => (
                    <div key={s.name} className="flex items-center gap-2">
                      <span className="text-gray-400">├─</span>
                      <span className="text-xs text-gray-500">Coordinates:</span>
                      <span className="px-2 py-1 bg-orange-100 text-orange-800 rounded text-xs">Groovy: {s.name}</span>
                    </div>
                  ))}
                  {groovyScripts.filter((s: any) => s.name.toLowerCase().includes('zip')).map((s: any) => (
                    <div key={s.name} className="flex items-center gap-2">
                      <span className="text-gray-400">├─</span>
                      <span className="text-xs text-gray-500">Zip/City:</span>
                      <span className="px-2 py-1 bg-orange-100 text-orange-800 rounded text-xs">Groovy: {s.name}</span>
                    </div>
                  ))}
                  {groovyScripts.filter((s: any) => s.name.toLowerCase().includes('country')).map((s: any) => (
                    <div key={s.name} className="flex items-center gap-2">
                      <span className="text-gray-400">└─</span>
                      <span className="text-xs text-gray-500">Country:</span>
                      <span className="px-2 py-1 bg-orange-100 text-orange-800 rounded text-xs">Groovy: {s.name}</span>
                    </div>
                  ))}
                </div>
                <div className="flex items-center gap-2 flex-wrap">
                  <span>→</span>
                  <span className="px-2 py-1 bg-purple-100 text-purple-800 rounded">HTTP GET</span>
                  <span>→</span>
                  <span className="px-2 py-1 bg-gray-100 text-gray-800 rounded">Try/Catch</span>
                  <span>→</span>
                  <span className="px-2 py-1 bg-blue-100 text-blue-800 rounded">Map Response</span>
                  <span>→</span>
                  <span className="px-2 py-1 bg-red-100 text-red-800 rounded">Stop</span>
                </div>
              </div>
            ) : isByIdFlow ? (
              // ByID flow - simpler
              <div className="text-sm">
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="px-2 py-1 bg-green-100 text-green-800 rounded">Start</span>
                  <span>→</span>
                  <span className="px-2 py-1 bg-blue-100 text-blue-800 rounded">Set Properties</span>
                  <span>→</span>
                  {groovyScripts.filter((s: any) => s.name.toLowerCase().includes('storeid') || s.name.toLowerCase().includes('byid')).map((s: any) => (
                    <React.Fragment key={s.name}>
                      <span className="px-2 py-1 bg-orange-100 text-orange-800 rounded">Groovy: {s.name}</span>
                      <span>→</span>
                    </React.Fragment>
                  ))}
                  <span className="px-2 py-1 bg-purple-100 text-purple-800 rounded">HTTP GET</span>
                  <span>→</span>
                  <span className="px-2 py-1 bg-gray-100 text-gray-800 rounded">Try/Catch</span>
                  <span>→</span>
                  <span className="px-2 py-1 bg-red-100 text-red-800 rounded">Stop</span>
                </div>
              </div>
            ) : (
              // Generic flow
              <div className="text-sm">
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="px-2 py-1 bg-green-100 text-green-800 rounded">Start</span>
                  <span>→</span>
                  <span className="px-2 py-1 bg-blue-100 text-blue-800 rounded">Set Properties</span>
                  <span>→</span>
                  <span className="px-2 py-1 bg-purple-100 text-purple-800 rounded">HTTP Request</span>
                  <span>→</span>
                  <span className="px-2 py-1 bg-gray-100 text-gray-800 rounded">Try/Catch</span>
                  <span>→</span>
                  <span className="px-2 py-1 bg-red-100 text-red-800 rounded">Stop</span>
                </div>
              </div>
            )}
          </div>
          
          {/* Components to Use - ONLY for main flows, not subprocesses */}
          {!isSub && (
            <div className="bg-white p-4 rounded-lg border">
              <h4 className="font-semibold mb-3 flex items-center gap-2">
                <Clipboard size={16} className="text-jade-blue" />
                Components to Use
              </h4>
              <div className="grid grid-cols-2 gap-3 text-sm">
                <div className="p-2 bg-gray-50 rounded">
                  <div className="text-xs text-gray-500">HTTP Connection</div>
                  <div className="font-medium">{connectionName}</div>
                </div>
                <div className="p-2 bg-gray-50 rounded">
                  <div className="text-xs text-gray-500">HTTP Operation</div>
                  <div className="font-medium">{matchingOperation?.name || `${processName}_Operation`}</div>
                </div>
                <div className="p-2 bg-gray-50 rounded">
                  <div className="text-xs text-gray-500">Request Profile</div>
                  <div className="font-medium">{matchingReqProfile?.name || `${processName}_Request`}</div>
                </div>
                <div className="p-2 bg-gray-50 rounded">
                  <div className="text-xs text-gray-500">Response Profile</div>
                  <div className="font-medium">{matchingResProfile?.name || `${processName}_Response`}</div>
                </div>
              </div>
            </div>
          )}
          
          {/* Step-by-Step Implementation */}
          <div className="bg-white p-4 rounded-lg border">
            <h4 className="font-semibold mb-3 flex items-center gap-2">
              <Zap size={16} className="text-jade-blue" />
              Step-by-Step Implementation
            </h4>
            <ol className="list-decimal list-inside space-y-2 text-sm">
              <li><strong>Create Process:</strong> New → Process → Name: "{processName}_Process"</li>
              <li><strong>Add Start Shape:</strong> Drag Start shape to canvas</li>
              {!isSub && <li><strong>Add Set Properties:</strong> Load Environment Extensions</li>}
              {isMainFindFlow && <li><strong>Add Decision Shape:</strong> Route based on input parameters</li>}
              {!isSub && <li><strong>Add Data Process:</strong> Groovy script for URI/data transformation</li>}
              {!isSub && <li><strong>Add HTTP Connector:</strong> Use {connectionName} and {matchingOperation?.name || `${processName}_Operation`}</li>}
              <li><strong>Add Try/Catch:</strong> Error handling (404, 500)</li>
              <li><strong>Add Stop Shape:</strong> Return response</li>
            </ol>
          </div>
          
          {/* Dependencies & Notes */}
          <div className="bg-white p-4 rounded-lg border">
            <h4 className="font-semibold mb-3 flex items-center gap-2">
              <AlertTriangle size={16} className="text-yellow-600" />
              Dependencies & Notes
            </h4>
            <ul className="list-disc list-inside space-y-1 text-sm text-gray-700">
              {envExtensions.length > 0 && (
                <li><strong>Environment Extensions:</strong> {envExtensions.join(', ')}</li>
              )}
              {envExtensions.length === 0 && (
                <li><strong>Environment Extensions:</strong> Configure as needed from Global Variables</li>
              )}
              <li><strong>pub.client:http:</strong> → Boomi HTTP Client Connector</li>
              <li><strong>Java Services:</strong> → Groovy scripts (Data Process shapes)</li>
              <li><strong>Global Variables:</strong> → Boomi Environment Extensions</li>
            </ul>
          </div>
        </div>
      )}
    </div>
  );
};

const GroovyCodeViewer = ({ code, name, onClose, showToast }: { code: string; name: string; onClose: () => void; showToast: (msg: string, type: 'success' | 'error' | 'info') => void }) => {
  const copyToClipboard = () => {
    navigator.clipboard.writeText(code);
    showToast('Groovy code copied to clipboard!', 'success');
  };
  const downloadCode = () => {
    const blob = new Blob([code], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${name.replace(/[^a-zA-Z0-9]/g, '_')}.groovy`;
    a.click();
    URL.revokeObjectURL(url);
  };
  
  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[80vh] overflow-hidden">
        <div className="flex items-center justify-between p-4 border-b bg-gray-50">
          <div className="flex items-center gap-2">
            <Code className="text-orange-600" size={20} />
            <h3 className="text-lg font-semibold">{name} - Groovy Script</h3>
          </div>
          <button onClick={onClose} className="p-2 hover:bg-gray-200 rounded-full">✕</button>
        </div>
        <div className="p-4 bg-blue-50 border-b">
          <div className="flex items-center gap-2 text-blue-800 text-sm">
            <Info size={16} />
            <span><strong>How to use:</strong> Copy this code and paste into a Boomi Data Process shape's Custom Scripting configuration.</span>
          </div>
        </div>
        <div className="p-4 overflow-auto max-h-[50vh]">
          <pre className="text-sm bg-gray-900 text-green-400 p-4 rounded-lg overflow-x-auto font-mono">{code}</pre>
        </div>
        <div className="flex justify-end gap-2 p-4 border-t bg-gray-50">
          <button onClick={copyToClipboard} className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center gap-2">
            <Copy size={16} /> Copy to Clipboard
          </button>
          <button onClick={downloadCode} className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 flex items-center gap-2">
            <Download size={16} /> Download .groovy
          </button>
          <button onClick={onClose} className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300">Close</button>
        </div>
      </div>
    </div>
  );
};

export default function IntegrationImplementation() {
  const { projectId, integrationName } = useParams();
  const navigate = useNavigate();
  const [project, setProject] = useState<any>(null);
  const [integration, setIntegration] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [converting, setConverting] = useState<string | null>(null);
  const [pushing, setPushing] = useState<string | null>(null);
  const [conversions, setConversions] = useState<Map<string, any>>(new Map());
  const [convertedComponents, setConvertedComponents] = useState<Set<string>>(new Set());
  const [toast, setToast] = useState<{ message: string; type: 'success' | 'error' | 'info' } | null>(null);
  const [viewingXml, setViewingXml] = useState<{ name: string; xml: string } | null>(null);
  const [viewingGroovy, setViewingGroovy] = useState<{ name: string; code: string } | null>(null);
  
  useEffect(() => { loadData(); }, [projectId, integrationName]);
  
  const loadData = async () => {
    try {
      const projectRes = await axios.get(`http://localhost:7201/api/projects/${projectId}`);
      const integrations = projectRes.data.parsedData?.integrations || 
        [{ name: decodeURIComponent(integrationName || 'Integration'), services: projectRes.data.parsedData?.services || [] }];
      const foundIntegration = integrations.find((i: any) => i.name === decodeURIComponent(integrationName || '')) || integrations[0];
      setIntegration(foundIntegration);
      setProject(projectRes.data);
    } catch (error) {
      console.error('Error:', error);
    } finally {
      setLoading(false);
    }
  };
  
  const showToast = (message: string, type: 'success' | 'error' | 'info') => { setToast({ message, type }); };
  
  const packageType = useMemo(() => detectPackageType(project), [project]);
  const implementationSteps = useMemo(() => getImplementationSteps(packageType, project, integration), [packageType, project, integration]);
  const totalComponents = useMemo(() => implementationSteps.reduce((sum, step) => sum + (step.isImplementationGuide ? 0 : step.items.length), 0), [implementationSteps]);
  
  const convertComponent = async (componentName: string, componentType: string, item: any, isGroovyScript: boolean = false) => {
    setConverting(componentName);
    try {
      const response = await axios.post('http://localhost:7201/api/conversions/convert', {
        projectId: projectId,
        serviceName: item.serviceName || componentName,
        componentType: componentType,
        packageType: packageType,
        displayName: componentName,
        isRequest: item.isRequest,
        url: item.url,
        returnGroovyOnly: isGroovyScript
      });
      if (response.data.boomiXml || response.data.groovyCode) {
        setConversions(prev => new Map(prev).set(componentName, response.data));
        setConvertedComponents(prev => new Set(prev).add(componentName));
        showToast(`Converted ${componentName} successfully!`, 'success');
      }
    } catch (error: any) {
      showToast(`Conversion failed: ${error.response?.data?.detail || error.message}`, 'error');
    } finally {
      setConverting(null);
    }
  };
  
  const viewXml = (componentName: string) => {
    const conversion = conversions.get(componentName);
    if (conversion?.boomiXml) setViewingXml({ name: componentName, xml: conversion.boomiXml });
  };
  
  const viewGroovyCode = (componentName: string) => {
    const conversion = conversions.get(componentName);
    if (conversion?.groovyCode) {
      setViewingGroovy({ name: componentName, code: conversion.groovyCode });
    } else if (conversion?.boomiXml) {
      const match = conversion.boomiXml.match(/<!\[CDATA\[([\s\S]*?)\]\]>/);
      if (match) setViewingGroovy({ name: componentName, code: match[1] });
      else setViewingXml({ name: componentName, xml: conversion.boomiXml });
    }
  };
  
  const downloadXml = (componentName: string) => {
    const conversion = conversions.get(componentName);
    if (conversion?.boomiXml) {
      const blob = new Blob([conversion.boomiXml], { type: 'application/xml' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${componentName.replace(/[^a-zA-Z0-9]/g, '_')}_boomi.xml`;
      a.click();
      URL.revokeObjectURL(url);
    }
  };
  
  const pushToBoomi = async (componentName: string) => {
    const conversion = conversions.get(componentName);
    if (!conversion?.boomiXml) return;
    setPushing(componentName);
    try {
      const response = await axios.post('http://localhost:7201/api/conversions/push-to-boomi', {
        projectId: projectId,
        componentXml: conversion.boomiXml,
        componentName: componentName
      });
      if (response.data.success) showToast(`Pushed ${componentName} to Boomi!`, 'success');
      else showToast(`Push failed: ${response.data.message}`, 'error');
    } catch (error: any) {
      showToast(`Push error: ${error.message}`, 'error');
    } finally {
      setPushing(null);
    }
  };
  
  const convertAllComponents = async () => {
    for (const step of implementationSteps) {
      if (step.isImplementationGuide) continue;
      for (const item of step.items) {
        if (!convertedComponents.has(item.name)) {
          await convertComponent(item.name, item.type, item, step.isGroovyScript);
          await new Promise(resolve => setTimeout(resolve, 500));
        }
      }
    }
    showToast('All components converted!', 'success');
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
      {toast && <Toast message={toast.message} type={toast.type} onClose={() => setToast(null)} />}
      
      <div className="flex items-center gap-4 mb-6">
        <button onClick={() => navigate(`/projects/${projectId}/integrations`)} className="p-2 hover:bg-gray-100 rounded-full transition-colors">
          <ArrowLeft size={24} />
        </button>
        <div>
          <h1 className="text-3xl font-bold text-jade-blue">{integration?.name || 'Integration'}</h1>
          <p className="text-gray-600">Visual Boomi Implementation Guide</p>
          <span className={`inline-block mt-1 px-3 py-1 rounded-full text-sm font-medium ${
            packageType === 'REST_API' ? 'bg-blue-100 text-blue-800' : 'bg-gray-100 text-gray-800'
          }`}>
            {packageType.replace('_', ' ')} Package
          </span>
        </div>
      </div>
      
      <div className="bg-gradient-to-r from-jade-blue to-jade-blue-light text-white rounded-lg p-6 mb-6">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-semibold">Implementation Progress</h2>
          <span className="text-3xl font-bold">{totalComponents > 0 ? Math.round((convertedComponents.size / totalComponents) * 100) : 0}%</span>
        </div>
        <div className="w-full bg-white/20 rounded-full h-3 mb-2">
          <div className="bg-yellow-400 h-3 rounded-full transition-all duration-500" style={{ width: `${totalComponents > 0 ? (convertedComponents.size / totalComponents) * 100 : 0}%` }} />
        </div>
        <p className="text-sm opacity-90">{convertedComponents.size} of {totalComponents} components converted</p>
        <button onClick={convertAllComponents} className="mt-4 px-4 py-2 bg-yellow-400 text-jade-blue font-semibold rounded-lg hover:bg-yellow-300 transition-colors">
          Convert All to Boomi
        </button>
      </div>
      
      {implementationSteps.map((step) => {
        const IconComponent = step.icon;
        const isProcessStep = step.isImplementationGuide;
        const isGroovyStep = step.isGroovyScript;
        
        return (
          <div key={step.stepNumber} className="bg-white rounded-lg shadow-md mb-6 overflow-hidden">
            <div className="bg-gray-50 px-6 py-4 flex items-center gap-4 border-b">
              <div className="w-10 h-10 bg-jade-blue text-white rounded-full flex items-center justify-center font-bold">{step.stepNumber}</div>
              <div className="flex-1">
                <h3 className="text-xl font-bold text-jade-blue">{step.category}</h3>
                <p className="text-gray-600">{step.description}</p>
              </div>
              <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                step.automationLevel === 'AUTO' ? 'bg-green-100 text-green-800' :
                step.automationLevel === 'SEMI' ? 'bg-yellow-100 text-yellow-800' : 'bg-gray-100 text-gray-800'
              }`}>
                {step.automationLevel}
              </span>
            </div>
            
            <div className="p-6 space-y-3">
              {isProcessStep ? (
                step.items.map((item: any, idx: number) => (
                  <ImplementationGuide key={idx} process={item} allSteps={implementationSteps} project={project} />
                ))
              ) : (
                step.items.map((item: any, idx: number) => {
                  const isConverted = convertedComponents.has(item.name);
                  const isConverting = converting === item.name;
                  const isPushing = pushing === item.name;
                  
                  return (
                    <div key={idx} className="flex items-center justify-between p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors">
                      <div className="flex items-center gap-3">
                        <IconComponent className={step.iconColor} size={24} />
                        <div>
                          <div className="font-semibold">{item.name}</div>
                          <div className="text-sm text-gray-500">
                            {item.fieldCount !== undefined && item.fieldCount > 0 && `${item.fieldCount} fields • `}
                            {item.description}
                          </div>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        {isConverted ? (
                          <>
                            <button onClick={() => isGroovyStep ? viewGroovyCode(item.name) : viewXml(item.name)} className="p-2 text-blue-600 hover:bg-blue-50 rounded-full" title={isGroovyStep ? "View Groovy" : "View XML"}>
                              {isGroovyStep ? <Code size={18} /> : <Eye size={18} />}
                            </button>
                            <button onClick={() => downloadXml(item.name)} className="p-2 text-green-600 hover:bg-green-50 rounded-full" title="Download">
                              <Download size={18} />
                            </button>
                            {!isGroovyStep && (
                              <button onClick={() => pushToBoomi(item.name)} disabled={isPushing} className="p-2 text-purple-600 hover:bg-purple-50 rounded-full disabled:opacity-50" title="Push to Boomi">
                                {isPushing ? <div className="animate-spin rounded-full h-5 w-5 border-2 border-purple-600 border-t-transparent" /> : <Upload size={18} />}
                              </button>
                            )}
                            <CheckCircle className="text-green-500" size={20} />
                          </>
                        ) : (
                          <button onClick={() => convertComponent(item.name, item.type, item, isGroovyStep)} disabled={isConverting} className="px-4 py-2 bg-yellow-400 text-jade-blue font-semibold rounded-lg hover:bg-yellow-300 transition-colors disabled:opacity-50 flex items-center gap-2">
                            {isConverting ? (<><div className="animate-spin rounded-full h-4 w-4 border-2 border-jade-blue border-t-transparent" />Converting...</>) : (<><Zap size={16} />Convert</>)}
                          </button>
                        )}
                      </div>
                    </div>
                  );
                })
              )}
            </div>
          </div>
        );
      })}
      
      {viewingXml && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[80vh] overflow-hidden">
            <div className="flex items-center justify-between p-4 border-b">
              <h3 className="text-lg font-semibold">{viewingXml.name} - Boomi XML</h3>
              <button onClick={() => setViewingXml(null)} className="p-2 hover:bg-gray-100 rounded-full">✕</button>
            </div>
            <div className="p-4 overflow-auto max-h-[60vh]">
              <pre className="text-sm bg-gray-50 p-4 rounded-lg overflow-x-auto">{viewingXml.xml}</pre>
            </div>
            <div className="flex justify-end gap-2 p-4 border-t">
              <button onClick={() => { navigator.clipboard.writeText(viewingXml.xml); showToast('Copied!', 'success'); }} className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200">Copy</button>
              <button onClick={() => setViewingXml(null)} className="px-4 py-2 bg-jade-blue text-white rounded-lg hover:bg-jade-blue-dark">Close</button>
            </div>
          </div>
        </div>
      )}
      
      {viewingGroovy && <GroovyCodeViewer code={viewingGroovy.code} name={viewingGroovy.name} onClose={() => setViewingGroovy(null)} showToast={showToast} />}
    </div>
  );
}
