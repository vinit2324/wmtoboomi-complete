import React, { useCallback, useEffect, useState } from 'react';
import ReactFlow, {
  Node,
  Edge,
  Controls,
  Background,
  useNodesState,
  useEdgesState,
  MarkerType,
  Position
} from 'reactflow';
import 'reactflow/dist/style.css';
import axios from 'axios';

interface DependencyGraphProps {
  projectId: string;
}

export default function DependencyGraph({ projectId }: DependencyGraphProps) {
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadDependencyGraph();
  }, [projectId]);

  const loadDependencyGraph = async () => {
    try {
      setLoading(true);
      
      // Get project data
      const response = await axios.get(`http://localhost:7201/api/projects/${projectId}`);
      const project = response.data;
      
      // Extract services and dependencies
      const services = project.parsedData?.services || [];
      const dependencies = project.parsedData?.dependencies || [];
      
      // Create nodes from services
      const graphNodes: Node[] = services.map((service: any, index: number) => {
        const angle = (index / services.length) * 2 * Math.PI;
        const radius = 250;
        
        return {
          id: service.name,
          type: getNodeType(service.type),
          data: { 
            label: service.name,
            type: service.type,
            complexity: service.complexity
          },
          position: {
            x: 400 + radius * Math.cos(angle),
            y: 300 + radius * Math.sin(angle)
          },
          style: getNodeStyle(service.type, service.complexity)
        };
      });
      
      // Create edges from dependencies
      const graphEdges: Edge[] = dependencies.map((dep: any, index: number) => ({
        id: `edge-${index}`,
        source: dep.from,
        target: dep.to,
        type: 'smoothstep',
        animated: true,
        markerEnd: {
          type: MarkerType.ArrowClosed,
          width: 20,
          height: 20
        },
        style: { stroke: '#00A86B' }
      }));
      
      setNodes(graphNodes);
      setEdges(graphEdges);
      setLoading(false);
      
    } catch (error) {
      console.error('Error loading dependency graph:', error);
      setLoading(false);
    }
  };

  const getNodeType = (serviceType: string): string => {
    return 'default'; // Can be extended to custom node types
  };

  const getNodeStyle = (serviceType: string, complexity?: string) => {
    const baseStyle = {
      padding: '10px 20px',
      borderRadius: '8px',
      border: '2px solid',
      background: 'white',
      fontSize: '12px',
      fontWeight: 500
    };

    // Color by service type
    if (serviceType === 'FlowService') {
      return {
        ...baseStyle,
        borderColor: '#00A86B',
        background: complexity === 'high' ? '#FFE8E8' : 
                   complexity === 'medium' ? '#FFF8E8' : '#E8F5F0'
      };
    } else if (serviceType === 'JavaService') {
      return {
        ...baseStyle,
        borderColor: '#FF6B6B',
        background: '#FFE8E8'
      };
    } else if (serviceType === 'AdapterService') {
      return {
        ...baseStyle,
        borderColor: '#4ECDC4',
        background: '#E8F9F8'
      };
    } else {
      return {
        ...baseStyle,
        borderColor: '#95A5A6',
        background: '#F0F0F0'
      };
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-[#00A86B] mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading dependency graph...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="h-[600px] border rounded-lg bg-gray-50">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        fitView
      >
        <Controls />
        <Background />
      </ReactFlow>
      
      <div className="p-4 border-t bg-white">
        <h3 className="font-semibold mb-2">Legend:</h3>
        <div className="flex gap-4 text-sm">
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded border-2 border-[#00A86B] bg-[#E8F5F0]"></div>
            <span>Flow Service (Low)</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded border-2 border-[#00A86B] bg-[#FFF8E8]"></div>
            <span>Flow Service (Medium)</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded border-2 border-[#00A86B] bg-[#FFE8E8]"></div>
            <span>Flow Service (High)</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded border-2 border-[#FF6B6B] bg-[#FFE8E8]"></div>
            <span>Java Service</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded border-2 border-[#4ECDC4] bg-[#E8F9F8]"></div>
            <span>Adapter Service</span>
          </div>
        </div>
      </div>
    </div>
  );
}
