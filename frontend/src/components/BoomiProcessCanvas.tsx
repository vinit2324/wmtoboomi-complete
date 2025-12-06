import React, { useMemo } from 'react';
import ReactFlow, {
  Node,
  Edge,
  Background,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
  Position,
} from 'reactflow';
import 'reactflow/dist/style.css';
import { Play, Square, Eye, Zap, Database, GitMerge, Shield } from 'lucide-react';

interface BoomiProcessCanvasProps {
  flowSteps: any[];
  serviceName: string;
  sourceDocuments?: any[];
  targetDocuments?: any[];
  adapters?: string[];
  onViewStep: (step: any, index: number) => void;
  onConvertStep: (step: any, index: number) => void;
  convertedSteps: Set<number>;
}

const BoomiShapeNode = ({ data }: { data: any }) => {
  const getShapeStyle = () => {
    const baseStyle = "px-4 py-3 rounded-lg border-2 shadow-md min-w-[180px] text-center";
    switch (data.shapeType) {
      case 'start': return `${baseStyle} bg-jade-blue text-white border-jade-blue`;
      case 'end': return `${baseStyle} bg-jade-blue text-white border-jade-blue`;
      case 'connector-source': return `${baseStyle} bg-purple-100 border-purple-400 text-purple-800`;
      case 'connector-target': return `${baseStyle} bg-indigo-100 border-indigo-400 text-indigo-800`;
      case 'map': return `${baseStyle} bg-amber-100 border-amber-400 text-amber-800`;
      case 'try-catch': return `${baseStyle} bg-red-100 border-red-400 text-red-800`;
      default: return `${baseStyle} bg-gray-100 border-gray-400 text-gray-800`;
    }
  };

  const getIcon = () => {
    switch (data.shapeType) {
      case 'start': return <Play size={16} className="inline mr-2" />;
      case 'end': return <Square size={16} className="inline mr-2" />;
      case 'connector-source':
      case 'connector-target': return <Database size={16} className="inline mr-2" />;
      case 'map': return <GitMerge size={16} className="inline mr-2" />;
      case 'try-catch': return <Shield size={16} className="inline mr-2" />;
      default: return null;
    }
  };

  return (
    <div className={getShapeStyle()}>
      <div className="font-semibold text-sm flex items-center justify-center">
        {getIcon()}{data.label}
      </div>
      {data.subLabel && <div className="text-xs opacity-75 mt-1">{data.subLabel}</div>}
      {data.showActions && (
        <div className="flex gap-1 mt-2 justify-center">
          <button onClick={(e) => { e.stopPropagation(); data.onView?.(); }} className="p-1 bg-white bg-opacity-50 rounded hover:bg-opacity-100" title="View"><Eye size={14} /></button>
          <button onClick={(e) => { e.stopPropagation(); data.onConvert?.(); }} className={`p-1 rounded ${data.isConverted ? 'bg-green-200' : 'bg-jade-gold'}`} title={data.isConverted ? 'Converted' : 'Convert'}><Zap size={14} /></button>
        </div>
      )}
    </div>
  );
};

const nodeTypes = { boomiShape: BoomiShapeNode };

export default function BoomiProcessCanvas({
  flowSteps, serviceName, sourceDocuments = [], targetDocuments = [], adapters = [],
  onViewStep, onConvertStep, convertedSteps
}: BoomiProcessCanvasProps) {
  
  const { nodes, edges } = useMemo(() => {
    const generatedNodes: Node[] = [];
    const generatedEdges: Edge[] = [];
    const centerX = 400;
    let currentY = 50;
    const ySpacing = 90;
    
    // Start
    generatedNodes.push({
      id: 'start', type: 'boomiShape',
      position: { x: centerX - 60, y: currentY },
      data: { label: 'Start', shapeType: 'start' },
      sourcePosition: Position.Bottom, targetPosition: Position.Top,
    });
    currentY += ySpacing;
    let lastNodeId = 'start';
    
    const sourceAdapter = adapters[0] || 'Source';
    const targetAdapter = adapters.length > 1 ? adapters[1] : (adapters[0] === 'Salesforce' ? 'Database' : adapters[0] || 'Target');
    
    // Try/Catch
    generatedNodes.push({
      id: 'try-catch', type: 'boomiShape',
      position: { x: centerX - 90, y: currentY },
      data: { label: 'Try/Catch', subLabel: 'Error Handling', shapeType: 'try-catch', showActions: true, isConverted: convertedSteps.has(-1),
        onView: () => onViewStep({ type: 'SEQUENCE', name: 'Try/Catch' }, -1),
        onConvert: () => onConvertStep({ type: 'SEQUENCE', name: 'Try/Catch' }, -1)
      },
      sourcePosition: Position.Bottom, targetPosition: Position.Top,
    });
    generatedEdges.push({ id: `${lastNodeId}-try-catch`, source: lastNodeId, target: 'try-catch', animated: true, style: { stroke: '#0F4C75' } });
    currentY += ySpacing;
    lastNodeId = 'try-catch';
    
    // Source Connector
    generatedNodes.push({
      id: 'source-connector', type: 'boomiShape',
      position: { x: centerX - 90, y: currentY },
      data: { label: `${sourceAdapter} Connector`, subLabel: 'Get Source Data', shapeType: 'connector-source', showActions: true, isConverted: convertedSteps.has(0),
        onView: () => onViewStep({ type: 'INVOKE', name: `${sourceAdapter} Query` }, 0),
        onConvert: () => onConvertStep({ type: 'INVOKE', name: `${sourceAdapter} Query` }, 0)
      },
      sourcePosition: Position.Bottom, targetPosition: Position.Top,
    });
    generatedEdges.push({ id: `${lastNodeId}-source`, source: lastNodeId, target: 'source-connector', animated: true, style: { stroke: '#0F4C75' } });
    currentY += ySpacing;
    lastNodeId = 'source-connector';
    
    // Map
    const sourceName = sourceDocuments[0]?.name?.split('/').pop() || 'Source';
    const targetName = targetDocuments[0]?.name?.split('/').pop() || 'Target';
    generatedNodes.push({
      id: 'map', type: 'boomiShape',
      position: { x: centerX - 90, y: currentY },
      data: { label: 'Map Shape', subLabel: `${sourceName} → ${targetName}`, shapeType: 'map', showActions: true, isConverted: convertedSteps.has(1),
        onView: () => onViewStep({ type: 'MAP', name: 'Data Transformation' }, 1),
        onConvert: () => onConvertStep({ type: 'MAP', name: 'Data Transformation' }, 1)
      },
      sourcePosition: Position.Bottom, targetPosition: Position.Top,
    });
    generatedEdges.push({ id: `${lastNodeId}-map`, source: lastNodeId, target: 'map', animated: true, style: { stroke: '#0F4C75' } });
    currentY += ySpacing;
    lastNodeId = 'map';
    
    // Target Connector
    generatedNodes.push({
      id: 'target-connector', type: 'boomiShape',
      position: { x: centerX - 90, y: currentY },
      data: { label: `${targetAdapter} Connector`, subLabel: 'Send Target Data', shapeType: 'connector-target', showActions: true, isConverted: convertedSteps.has(2),
        onView: () => onViewStep({ type: 'INVOKE', name: `${targetAdapter} Send` }, 2),
        onConvert: () => onConvertStep({ type: 'INVOKE', name: `${targetAdapter} Send` }, 2)
      },
      sourcePosition: Position.Bottom, targetPosition: Position.Top,
    });
    generatedEdges.push({ id: `${lastNodeId}-target`, source: lastNodeId, target: 'target-connector', animated: true, style: { stroke: '#0F4C75' } });
    currentY += ySpacing;
    lastNodeId = 'target-connector';
    
    // End
    generatedNodes.push({
      id: 'end', type: 'boomiShape',
      position: { x: centerX - 60, y: currentY },
      data: { label: 'End', shapeType: 'end' },
      sourcePosition: Position.Bottom, targetPosition: Position.Top,
    });
    generatedEdges.push({ id: `${lastNodeId}-end`, source: lastNodeId, target: 'end', animated: true, style: { stroke: '#0F4C75' } });
    
    return { nodes: generatedNodes, edges: generatedEdges };
  }, [flowSteps, sourceDocuments, targetDocuments, adapters, convertedSteps, onViewStep, onConvertStep]);

  const [nodesState, , onNodesChange] = useNodesState(nodes);
  const [edgesState, , onEdgesChange] = useEdgesState(edges);

  return (
    <div className="h-[500px] bg-white rounded-lg border-2 border-gray-200 overflow-hidden">
      <ReactFlow nodes={nodesState} edges={edgesState} onNodesChange={onNodesChange} onEdgesChange={onEdgesChange} nodeTypes={nodeTypes} fitView attributionPosition="bottom-left">
        <Background color="#e5e7eb" gap={16} />
        <Controls />
        <MiniMap nodeColor={(node) => {
          switch (node.data?.shapeType) {
            case 'start': case 'end': return '#0F4C75';
            case 'connector-source': return '#9333ea';
            case 'connector-target': return '#6366f1';
            case 'map': return '#f59e0b';
            case 'try-catch': return '#ef4444';
            default: return '#6b7280';
          }
        }} />
      </ReactFlow>
    </div>
  );
}
