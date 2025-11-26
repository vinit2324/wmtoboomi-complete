import { useQuery } from '@tanstack/react-query';
import { useParams, Link } from 'react-router-dom';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from 'recharts';
import {
  ArrowLeft,
  Loader2,
  TrendingUp,
  Clock,
  Layers,
  AlertTriangle,
} from 'lucide-react';
import { projectsApi } from '../utils/api';

const COLORS = ['#00A86B', '#00C878', '#47AF87', '#75C3A5', '#A3D7C3'];

export default function Analysis() {
  const { projectId } = useParams();

  const { data: project, isLoading } = useQuery({
    queryKey: ['project', projectId],
    queryFn: async () => {
      const response = await projectsApi.get(projectId!);
      return response.data;
    },
    enabled: !!projectId,
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="w-8 h-8 animate-spin text-jade-500" />
      </div>
    );
  }

  if (!project || !project.analysis) {
    return (
      <div className="card text-center py-12">
        <p className="text-gray-500">Analysis not available</p>
        <Link to={`/projects/${projectId}`} className="btn-primary mt-4">
          Back to Project
        </Link>
      </div>
    );
  }

  const { analysis, packageInfo } = project;
  const services = packageInfo?.services;
  const flowVerbs = packageInfo?.flowVerbStats;

  // Prepare chart data
  const serviceTypeData = services
    ? [
        { name: 'Flow', value: services.flow },
        { name: 'Java', value: services.java },
        { name: 'Adapter', value: services.adapter },
        { name: 'Map', value: services.map },
        { name: 'Document', value: services.document },
      ].filter((d) => d.value > 0)
    : [];

  const flowVerbData = flowVerbs
    ? [
        { name: 'MAP', value: flowVerbs.map },
        { name: 'BRANCH', value: flowVerbs.branch },
        { name: 'LOOP', value: flowVerbs.loop },
        { name: 'REPEAT', value: flowVerbs.repeat },
        { name: 'SEQUENCE', value: flowVerbs.sequence },
        { name: 'TRY/CATCH', value: flowVerbs.tryCatch },
        { name: 'EXIT', value: flowVerbs.exit },
      ].filter((d) => d.value > 0)
    : [];

  const wMPublicData = Object.entries(analysis.wMPublicServices || {})
    .slice(0, 10)
    .map(([name, count]) => ({
      name: name.split(':').pop() || name,
      fullName: name,
      count,
    }));

  const complexityColor = {
    low: 'text-green-600 bg-green-100',
    medium: 'text-yellow-600 bg-yellow-100',
    high: 'text-red-600 bg-red-100',
  }[analysis.complexity.overall];

  return (
    <div className="space-y-6 animate-fadeIn">
      {/* Header */}
      <div className="flex items-center">
        <Link
          to={`/projects/${projectId}`}
          className="mr-4 p-2 hover:bg-gray-100 rounded-lg text-gray-500"
        >
          <ArrowLeft className="w-5 h-5" />
        </Link>
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Analysis Dashboard</h1>
          <p className="text-gray-500">{project.packageName}</p>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500">Automation Potential</p>
              <p className="text-3xl font-bold text-jade-600">
                {analysis.automationPotential}
              </p>
            </div>
            <div className="p-3 bg-jade-100 rounded-lg">
              <TrendingUp className="w-6 h-6 text-jade-600" />
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500">Estimated Hours</p>
              <p className="text-3xl font-bold">{analysis.estimatedHours}</p>
            </div>
            <div className="p-3 bg-blue-100 rounded-lg">
              <Clock className="w-6 h-6 text-blue-600" />
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500">Complexity</p>
              <p className={`text-2xl font-bold capitalize ${complexityColor} px-3 py-1 rounded-lg inline-block`}>
                {analysis.complexity.overall}
              </p>
            </div>
            <div className="p-3 bg-yellow-100 rounded-lg">
              <Layers className="w-6 h-6 text-yellow-600" />
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500">Migration Waves</p>
              <p className="text-3xl font-bold">{analysis.migrationWaves.length}</p>
            </div>
            <div className="p-3 bg-purple-100 rounded-lg">
              <AlertTriangle className="w-6 h-6 text-purple-600" />
            </div>
          </div>
        </div>
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Service Types */}
        <div className="card">
          <h2 className="text-lg font-semibold mb-4">Service Distribution</h2>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={serviceTypeData}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={80}
                  paddingAngle={5}
                  dataKey="value"
                  label={({ name, value }) => `${name}: ${value}`}
                >
                  {serviceTypeData.map((_, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Flow Verbs */}
        <div className="card">
          <h2 className="text-lg font-semibold mb-4">Flow Verb Usage</h2>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={flowVerbData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" tick={{ fontSize: 12 }} />
                <YAxis />
                <Tooltip />
                <Bar dataKey="value" fill="#00A86B" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* wMPublic Services */}
      {wMPublicData.length > 0 && (
        <div className="card">
          <h2 className="text-lg font-semibold mb-4">Top wMPublic Services Used</h2>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={wMPublicData} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis type="number" />
                <YAxis dataKey="name" type="category" width={120} tick={{ fontSize: 11 }} />
                <Tooltip
                  formatter={(value, name, props) => [value, props.payload.fullName]}
                />
                <Bar dataKey="count" fill="#00C878" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {/* Migration Waves */}
      <div className="card">
        <h2 className="text-lg font-semibold mb-4">Migration Waves</h2>
        <div className="space-y-4">
          {analysis.migrationWaves.map((wave) => (
            <div
              key={wave.waveNumber}
              className="p-4 bg-gray-50 rounded-lg"
            >
              <div className="flex items-center justify-between mb-2">
                <h3 className="font-medium">Wave {wave.waveNumber}</h3>
                <div className="flex items-center gap-4 text-sm text-gray-500">
                  <span>{wave.services.length} services</span>
                  <span>{wave.estimatedHours} hours</span>
                </div>
              </div>
              <div className="flex flex-wrap gap-2">
                {wave.services.slice(0, 10).map((service) => (
                  <span
                    key={service}
                    className="px-2 py-1 bg-white border border-gray-200 rounded text-sm"
                  >
                    {service.split(':').pop()}
                  </span>
                ))}
                {wave.services.length > 10 && (
                  <span className="px-2 py-1 bg-jade-100 text-jade-700 rounded text-sm">
                    +{wave.services.length - 10} more
                  </span>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Complexity Factors */}
      <div className="card">
        <h2 className="text-lg font-semibold mb-4">Complexity Factors</h2>
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
          {Object.entries(analysis.complexity.factors).map(([factor, value]) => (
            <div key={factor} className="p-4 bg-gray-50 rounded-lg text-center">
              <p className="text-2xl font-bold">{value}</p>
              <p className="text-sm text-gray-500 capitalize">
                {factor.replace(/([A-Z])/g, ' $1').trim()}
              </p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
