// Customer types
export interface BoomiSettings {
  accountId: string;
  username: string;
  apiToken: string;
  baseUrl: string;
  defaultFolder: string;
}

export interface LLMSettings {
  provider: 'openai' | 'anthropic' | 'gemini' | 'ollama';
  apiKey: string;
  baseUrl: string;
  model: string;
  temperature: number;
}

export interface CustomerSettings {
  boomi: BoomiSettings;
  llm: LLMSettings;
}

export interface Customer {
  customerId: string;
  customerName: string;
  createdAt: string;
  updatedAt: string;
  settings: CustomerSettings;
  isActive: boolean;
}

// Project types
export interface FlowVerbStats {
  map: number;
  branch: number;
  loop: number;
  repeat: number;
  sequence: number;
  tryCatch: number;
  tryFinally: number;
  catch: number;
  finally: number;
  exit: number;
}

export interface ServiceStats {
  total: number;
  flow: number;
  adapter: number;
  java: number;
  map: number;
  document: number;
}

export interface PackageInfo {
  fileName: string;
  fileSize: number;
  services: ServiceStats;
  flowVerbStats: FlowVerbStats;
  wMPublicCallCount: number;
  customJavaCallCount: number;
}

export interface ServiceInvocation {
  package: string;
  service: string;
  count: number;
}

export interface ParsedService {
  type: 'FlowService' | 'JavaService' | 'AdapterService' | 'MapService' | 'DocumentType';
  name: string;
  path: string;
  flowVerbs?: FlowVerbStats;
  serviceInvocations: ServiceInvocation[];
  pipelineComplexity: 'low' | 'medium' | 'high';
  adapters: string[];
  inputSignature?: Record<string, unknown>;
  outputSignature?: Record<string, unknown>;
  rawXml?: string;
}

export interface ParsedDocument {
  name: string;
  path: string;
  fields: unknown[];
  nestedStructures: string[];
  isArray: boolean;
  dataType: string;
}

export interface ParsedManifest {
  packageName: string;
  version: string;
  dependencies: string[];
  startupServices: string[];
  shutdownServices: string[];
  requires: unknown[];
}

export interface ParsedData {
  manifest: ParsedManifest;
  services: ParsedService[];
  documents: ParsedDocument[];
  ediSchemas: unknown[];
}

export interface DependencyInfo {
  serviceName: string;
  dependsOn: string[];
  dependedBy: string[];
}

export interface ComplexityAnalysis {
  overall: 'low' | 'medium' | 'high';
  score: number;
  factors: Record<string, number>;
}

export interface MigrationWave {
  waveNumber: number;
  services: string[];
  estimatedHours: number;
  dependencies: string[];
}

export interface AnalysisResults {
  dependencies: DependencyInfo[];
  complexity: ComplexityAnalysis;
  estimatedHours: number;
  migrationWaves: MigrationWave[];
  automationPotential: string;
  wMPublicServices: Record<string, number>;
}

export interface Project {
  projectId: string;
  customerId: string;
  packageName: string;
  uploadedAt: string;
  status: 'uploaded' | 'parsing' | 'parsed' | 'analyzing' | 'analyzed' | 'failed';
  packageInfo: PackageInfo;
  parsedData?: ParsedData;
  analysis?: AnalysisResults;
  errorMessage?: string;
}

// Conversion types
export interface BoomiComponentInfo {
  componentId: string;
  componentUrl: string;
  folderPath: string;
  pushedAt?: string;
  pushedBy?: string;
}

export interface ValidationError {
  severity: 'error' | 'warning' | 'info';
  message: string;
  location: string;
}

export interface ManualReviewItem {
  type: string;
  name: string;
  reason: string;
}

export interface ValidationResult {
  isValid: boolean;
  automationLevel: string;
  errors: ValidationError[];
  warnings: ValidationError[];
  manualReviewItems: ManualReviewItem[];
  estimatedManualEffort: string;
}

export interface Conversion {
  conversionId: string;
  projectId: string;
  customerId: string;
  componentType: string;
  sourceType: string;
  sourceName: string;
  targetName: string;
  convertedAt: string;
  status: 'pending' | 'converting' | 'converted' | 'validated' | 'pushed' | 'failed';
  complexity: 'low' | 'medium' | 'high';
  automationLevel: string;
  boomiXml?: string;
  boomiComponent?: BoomiComponentInfo;
  validation?: ValidationResult;
  conversionNotes: string[];
  errorMessage?: string;
}

// File tree types
export interface FileTreeNode {
  name: string;
  path: string;
  type: 'file' | 'folder';
  children?: FileTreeNode[];
  size?: number;
  extension?: string;
}

// Mapping types
export interface FieldMapping {
  id: string;
  sourceField: string;
  sourceType: string;
  targetField: string;
  targetType: string;
  transformation: 'direct' | 'format' | 'concat' | 'lookup' | 'custom';
  transformationLogic?: string;
  isMapped: boolean;
  isValidated: boolean;
  notes: string;
}

export interface SchemaField {
  name: string;
  path: string;
  type: string;
  isArray: boolean;
  isRequired: boolean;
  children?: SchemaField[];
}

export interface Mapping {
  mappingId: string;
  projectId: string;
  sourceName: string;
  targetName: string;
  sourceSchema: SchemaField[];
  targetSchema: SchemaField[];
  fieldMappings: FieldMapping[];
  createdAt: string;
  updatedAt: string;
  mappingStatus: string;
}

// Log types
export interface LogEntry {
  id: string;
  timestamp: string;
  customerId?: string;
  projectId?: string;
  level: 'debug' | 'info' | 'warning' | 'error';
  category: string;
  action: string;
  message: string;
  metadata: Record<string, unknown>;
}

// AI types
export interface AIMessage {
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp?: string;
}

export interface AIResponse {
  message: string;
  suggestions: string[];
  codeSnippets: Array<{ language: string; code: string }>;
  relatedServices: string[];
}

// API Response types
export interface ConnectionTestResult {
  success: boolean;
  message: string;
  details?: Record<string, unknown>;
}
