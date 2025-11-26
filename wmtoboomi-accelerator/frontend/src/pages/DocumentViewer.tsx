import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useParams, Link } from 'react-router-dom';
import Editor from '@monaco-editor/react';
import {
  ArrowLeft,
  Folder,
  FileCode,
  FileText,
  ChevronRight,
  ChevronDown,
  Loader2,
  Download,
  Search,
} from 'lucide-react';
import { projectsApi } from '../utils/api';
import type { FileTreeNode } from '../types';

interface TreeItemProps {
  node: FileTreeNode;
  depth: number;
  selectedPath: string;
  onSelect: (path: string) => void;
  expanded: Set<string>;
  onToggle: (path: string) => void;
}

function TreeItem({ node, depth, selectedPath, onSelect, expanded, onToggle }: TreeItemProps) {
  const isExpanded = expanded.has(node.path);
  const isSelected = selectedPath === node.path;
  const isFolder = node.type === 'folder';

  const handleClick = () => {
    if (isFolder) {
      onToggle(node.path);
    } else {
      onSelect(node.path);
    }
  };

  const getFileIcon = () => {
    if (isFolder) {
      return isExpanded ? (
        <ChevronDown className="w-4 h-4 text-gray-500" />
      ) : (
        <ChevronRight className="w-4 h-4 text-gray-500" />
      );
    }
    const ext = node.extension?.toLowerCase();
    if (ext === '.xml' || ext === '.ndf') {
      return <FileCode className="w-4 h-4 text-orange-500" />;
    }
    return <FileText className="w-4 h-4 text-gray-400" />;
  };

  return (
    <div>
      <div
        onClick={handleClick}
        className={`flex items-center px-2 py-1 cursor-pointer hover:bg-gray-100 rounded ${
          isSelected ? 'bg-jade-50 text-jade-700' : ''
        }`}
        style={{ paddingLeft: `${depth * 16 + 8}px` }}
      >
        {getFileIcon()}
        {isFolder && <Folder className="w-4 h-4 text-jade-500 ml-1" />}
        <span className="ml-2 text-sm truncate">{node.name}</span>
        {!isFolder && node.size && (
          <span className="ml-auto text-xs text-gray-400">
            {(node.size / 1024).toFixed(1)} KB
          </span>
        )}
      </div>
      {isFolder && isExpanded && node.children && (
        <div>
          {node.children.map((child) => (
            <TreeItem
              key={child.path}
              node={child}
              depth={depth + 1}
              selectedPath={selectedPath}
              onSelect={onSelect}
              expanded={expanded}
              onToggle={onToggle}
            />
          ))}
        </div>
      )}
    </div>
  );
}

export default function DocumentViewer() {
  const { projectId } = useParams();
  const [selectedPath, setSelectedPath] = useState('');
  const [expanded, setExpanded] = useState<Set<string>>(new Set());
  const [searchTerm, setSearchTerm] = useState('');

  const { data: fileTree, isLoading: treeLoading } = useQuery({
    queryKey: ['fileTree', projectId],
    queryFn: async () => {
      const response = await projectsApi.getFileTree(projectId!);
      return response.data;
    },
    enabled: !!projectId,
  });

  const { data: fileContent, isLoading: contentLoading } = useQuery({
    queryKey: ['fileContent', projectId, selectedPath],
    queryFn: async () => {
      const response = await projectsApi.getFileContent(projectId!, selectedPath);
      return response.data;
    },
    enabled: !!projectId && !!selectedPath,
  });

  const handleToggle = (path: string) => {
    setExpanded((prev) => {
      const next = new Set(prev);
      if (next.has(path)) {
        next.delete(path);
      } else {
        next.add(path);
      }
      return next;
    });
  };

  const getLanguage = (path: string) => {
    const ext = path.split('.').pop()?.toLowerCase();
    switch (ext) {
      case 'xml':
      case 'ndf':
        return 'xml';
      case 'java':
      case 'frag':
        return 'java';
      case 'json':
        return 'json';
      case 'properties':
        return 'properties';
      default:
        return 'plaintext';
    }
  };

  const highlightFlowVerbs = (content: string) => {
    // This would be enhanced with proper syntax highlighting
    return content;
  };

  return (
    <div className="h-[calc(100vh-10rem)] flex flex-col animate-fadeIn">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center">
          <Link
            to={`/projects/${projectId}`}
            className="mr-4 p-2 hover:bg-gray-100 rounded-lg text-gray-500"
          >
            <ArrowLeft className="w-5 h-5" />
          </Link>
          <div>
            <h1 className="text-xl font-bold text-gray-900">Document Viewer</h1>
            <p className="text-sm text-gray-500">
              Browse and view package files
            </p>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex gap-4 min-h-0">
        {/* File Tree */}
        <div className="w-80 bg-white rounded-lg border border-gray-200 flex flex-col">
          <div className="p-3 border-b border-gray-200">
            <div className="relative">
              <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
              <input
                type="text"
                placeholder="Search files..."
                className="input pl-9 text-sm"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
            </div>
          </div>
          <div className="flex-1 overflow-auto p-2">
            {treeLoading ? (
              <div className="flex items-center justify-center py-8">
                <Loader2 className="w-6 h-6 animate-spin text-jade-500" />
              </div>
            ) : fileTree ? (
              <TreeItem
                node={fileTree}
                depth={0}
                selectedPath={selectedPath}
                onSelect={setSelectedPath}
                expanded={expanded}
                onToggle={handleToggle}
              />
            ) : (
              <p className="text-center text-gray-500 py-4">No files found</p>
            )}
          </div>
        </div>

        {/* Content Viewer */}
        <div className="flex-1 bg-white rounded-lg border border-gray-200 flex flex-col min-h-0">
          {selectedPath ? (
            <>
              <div className="p-3 border-b border-gray-200 flex items-center justify-between">
                <div className="flex items-center">
                  <FileCode className="w-5 h-5 text-jade-500 mr-2" />
                  <span className="font-medium text-sm">{selectedPath}</span>
                </div>
                <div className="flex items-center gap-2">
                  {selectedPath.endsWith('.ndf') && (
                    <span className="badge badge-info">Binary XML (Converted)</span>
                  )}
                  {selectedPath.includes('flow.xml') && (
                    <span className="badge badge-jade">Flow Service</span>
                  )}
                </div>
              </div>
              <div className="flex-1 min-h-0">
                {contentLoading ? (
                  <div className="flex items-center justify-center h-full">
                    <Loader2 className="w-6 h-6 animate-spin text-jade-500" />
                  </div>
                ) : (
                  <Editor
                    height="100%"
                    language={getLanguage(selectedPath)}
                    value={fileContent || ''}
                    options={{
                      readOnly: true,
                      minimap: { enabled: false },
                      fontSize: 13,
                      fontFamily: 'JetBrains Mono, monospace',
                      wordWrap: 'on',
                      scrollBeyondLastLine: false,
                    }}
                    theme="vs-light"
                  />
                )}
              </div>
            </>
          ) : (
            <div className="flex-1 flex items-center justify-center text-gray-500">
              <div className="text-center">
                <FileCode className="w-16 h-16 mx-auto mb-4 opacity-50" />
                <p>Select a file to view its contents</p>
                <p className="text-sm mt-2">
                  node.ndf files are converted from binary XML
                </p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
