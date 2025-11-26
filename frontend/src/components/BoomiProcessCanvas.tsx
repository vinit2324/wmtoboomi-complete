import React, { useCallback, useMemo } from 'react';
import ReactFlow, {
  Node,
  Edge,
  Controls,
  Background,
  useNodesState,
  useEdgesState,
  MarkerType,
  Handle,
  Position,
  MiniMap,
} from 'reactflow';
import 'reactflow/dist/style.css';
import { Eye, Zap, CheckCircle } from 'lucide-react';

interface FlowStep {
  type: string;
  name: string;
}

interface BoomiProcessCanvasProps {
  flowSteps: FlowStep[];
  serviceName: string;
  onViewStep: (step: FlowStep, index: number) => void;
  onConvertStep: (step: FlowStep, index: number) => void;
  convertedSteps: Set<number>;
}

// Custom Node Component
function BoomiShapeNode({ data }: { data: any }) {
  const isConverted = data.converted;
  
  return (
    <div className={`px-3 py-2 rounded-lg border-2 min-w-[180px] ${
      isConverted 
        ? 'bg-green-100 border-green-500' 
        : 'bg-white border-jade-blue'
    }`}>
      <Handle type="target" position={Position.Top} className="w-2 h-2" />
      
      <div className="flex items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <span className="text-sm">{data.icon}</span>
          <div>
            <div className="font-semibold text-xs text-jade-blue">{data.boomiShape}</div>
            <div className="text-[10px] text-gray-500 truncate max-w-[100px]">{data.stepName}</div>
          </div>
        </div>
        
        <div className="flex gap-1">
          <button
            onClick={(e) => { e.stopPropagation(); data.onView(); }}
            className="p-1 bg-jade-blue text-white rounded hover:bg-jade-blue-dark"
            title="View Details"
          >
            <Eye size={12} />
          </button>
          {!isConverted ? (
            <button
              onClick={(e) => { e.stopPropagation(); data.onConvert(); }}
              className="p-1 bg-jade-gold text-jade-blue-dark rounded hover:bg-jade-gold-dark"
              title="Convert"
            >
              <Zap size={12} />
            </button>
          ) : (
            <span className="p-1 bg-green-500 text-white rounded">
              <CheckCircle size={12} />
            </span>
          )}
        </div>
      </div>
      
      <Handle type="source" position={Position.Bottom} className="w-2 h-2" />
    </div>
  );
}

// Start/End Node Component
function StartEndNode({ data }: { data: any }) {
  return (
    <div className={`px-4 py-2 rounded-full font-bold text-white text-sm ${
      data.isStart ? 'bg-jade-blue' : 'bg-jade-blue'
    }`}>
      {data.isStart && <Handle type="source" position={Position.Bottom} className="w-2 h-2" />}
      {!data.isStart && <Handle type="target" position={Position.Top} className="w-2 h-2" />}
      <span>{data.label}</span>
    </div>
  );
}

const nodeTypes = {
  boomiShape: BoomiShapeNode,
  startEnd: StartEndNode,
};

export default function BoomiProcessCanvas({
  flowSteps,
  serviceName,
  onViewStep,
  onConvertStep,
  convertedSteps
}: BoomiProcessCanvasProps) {
  
  // Map webMethods step to Boomi shape info
  const getBoomiShapeInfo = (stepType: string) => {
    switch (stepType) {
      case 'MAP':
        return { icon: '🔄', boomiShape: 'Map Shape', color: '#E8F5F0' };
      case 'BRANCH':
        return { icon: '🔀', boomiShape: 'Decision Shape', color: '#FFF3E0' };
      case 'LOOP':
        return { icon: '🔁', boomiShape: 'ForEach Shape', color: '#E3F2FD' };
      case 'INVOKE':
        return { icon: '🔌', boomiShape: 'Connector Shape', color: '#F3E5F5' };
      case 'SEQUENCE':
        return { icon: '📦', boomiShape: 'Try/Catch Shape', color: '#FFF8E1' };
      case 'EXIT':
        return { icon: '🛑', boomiShape: 'Stop Shape', color: '#FFEBEE' };
      default:
        return { icon: '⚡', boomiShape: 'Business Rules', color: '#FAFAFA' };
    }
  };
  
  // Calculate height based on number of steps
  const canvasHeight = Math.max(400, Math.min(800, (flowSteps.length + 2) * 70));
  
  // Generate nodes from flow steps
  const initialNodes: Node[] = useMemo(() => {
    const nodes: Node[] = [];
    let yPos = 30;
    const spacing = 65;
    
    // Start shape
    nodes.push({
      id: 'start',
      type: 'startEnd',
      data: { label: '▶ Start', isStart: true },
      position: { x: 250, y: yPos },
    });
    yPos += spacing;
    
    // Flow step shapes
    flowSteps.forEach((step, idx) => {
      const shapeInfo = getBoomiShapeInfo(step.type);
      const isConverted = convertedSteps.has(idx);
      
      nodes.push({
        id: `step-${idx}`,
        type: 'boomiShape',
        data: {
          ...shapeInfo,
          stepName: step.name || `Step ${idx + 1}`,
          stepType: step.type,
          stepIndex: idx,
          converted: isConverted,
          onView: () => onViewStep(step, idx),
          onConvert: () => onConvertStep(step, idx),
        },
        position: { x: 200, y: yPos },
      });
      yPos += spacing;
    });
    
    // End shape
    nodes.push({
      id: 'end',
      type: 'startEnd',
      data: { label: '⏹ End', isStart: false },
      position: { x: 250, y: yPos },
    });
    
    return nodes;
  }, [flowSteps, convertedSteps, onViewStep, onConvertStep]);
  
  // Generate edges (connections)
  const initialEdges: Edge[] = useMemo(() => {
    const edges: Edge[] = [];
    
    if (flowSteps.length > 0) {
      edges.push({
        id: 'e-start-step0',
        source: 'start',
        target: 'step-0',
        animated: true,
        style: { stroke: '#FDB913', strokeWidth: 2 },
        markerEnd: { type: MarkerType.ArrowClosed, color: '#FDB913' }
      });
      
      for (let i = 0; i < flowSteps.length - 1; i++) {
        edges.push({
          id: `e-step${i}-step${i + 1}`,
          source: `step-${i}`,
          target: `step-${i + 1}`,
          animated: true,
          style: { stroke: '#003B5C', strokeWidth: 2 },
          markerEnd: { type: MarkerType.ArrowClosed, color: '#003B5C' }
        });
      }
      
      edges.push({
        id: `e-step${flowSteps.length - 1}-end`,
        source: `step-${flowSteps.length - 1}`,
        target: 'end',
        animated: true,
        style: { stroke: '#FDB913', strokeWidth: 2 },
        markerEnd: { type: MarkerType.ArrowClosed, color: '#FDB913' }
      });
    } else {
      edges.push({
        id: 'e-start-end',
        source: 'start',
        target: 'end',
        animated: true,
        style: { stroke: '#003B5C', strokeWidth: 2 },
        markerEnd: { type: MarkerType.ArrowClosed, color: '#003B5C' }
      });
    }
    
    return edges;
  }, [flowSteps]);
  
  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);
  
  return (
    <div 
      className="border-2 border-jade-blue rounded-lg bg-gray-50"
      style={{ height: `${canvasHeight}px` }}
    >
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        nodeTypes={nodeTypes}
        fitView
        fitViewOptions={{ padding: 0.3, minZoom: 0.3, maxZoom: 1.5 }}
        minZoom={0.2}
        maxZoom={2}
        defaultViewport={{ x: 0, y: 0, zoom: 0.8 }}
        attributionPosition="bottom-left"
      >
        <Controls showInteractive={false} />
        <MiniMap 
          nodeColor={() => '#003B5C'}
          maskColor="rgba(0, 59, 92, 0.1)"
          className="bg-white border border-gray-300"
        />
        <Background color="#003B5C" gap={20} size={1} />
      </ReactFlow>
    </div>
  );
}
