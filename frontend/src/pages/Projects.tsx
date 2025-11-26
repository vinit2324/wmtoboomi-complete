import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { Package, Upload, ChevronRight, CheckCircle } from 'lucide-react';
import { useToast } from '../components/Toast';

export default function Projects() {
  const navigate = useNavigate();
  const { showToast } = useToast();
  const [projects, setProjects] = useState<any[]>([]);
  const [customers, setCustomers] = useState<any[]>([]);
  const [selectedCustomer, setSelectedCustomer] = useState('');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);

  useEffect(() => {
    loadProjects();
    loadCustomers();
  }, []);

  const loadProjects = async () => {
    try {
      const response = await axios.get('http://localhost:7201/api/projects');
      setProjects(response.data.projects || []);
    } catch (error) {
      console.error('Error:', error);
    }
  };

  const loadCustomers = async () => {
    try {
      const response = await axios.get('http://localhost:7201/api/customers');
      setCustomers(response.data.customers || []);
      if (response.data.customers?.length > 0) {
        setSelectedCustomer(response.data.customers[0].customerId);
      }
    } catch (error) {
      console.error('Error:', error);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setSelectedFile(e.target.files[0]);
    }
  };

  const handleUpload = async () => {
    if (!selectedFile || !selectedCustomer) {
      showToast('Please select a customer and file', 'warning');
      return;
    }

    setUploading(true);
    const formData = new FormData();
    formData.append('file', selectedFile);
    formData.append('customerId', selectedCustomer);

    try {
      await axios.post('http://localhost:7201/api/projects', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      showToast('Package uploaded and parsed successfully!', 'success');
      setSelectedFile(null);
      // Reset file input
      const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement;
      if (fileInput) fileInput.value = '';
      loadProjects();
    } catch (error: any) {
      showToast(`Upload failed: ${error.response?.data?.detail || error.message}`, 'error');
    } finally {
      setUploading(false);
    }
  };

  const getStatusBadge = (status: string) => {
    const styles = {
      parsed: 'bg-jade-blue text-white',
      parsing: 'bg-jade-gold text-jade-blue-dark',
      failed: 'bg-red-100 text-red-800',
      uploaded: 'bg-gray-100 text-gray-800'
    };
    return styles[status as keyof typeof styles] || styles.uploaded;
  };

  return (
    <div className="p-6">
      <div className="bg-white rounded-lg shadow-lg p-6 mb-6">
        <h2 className="text-2xl font-bold text-jade-blue mb-6">Upload webMethods Package</h2>
        
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-2">Select Customer</label>
            <select
              value={selectedCustomer}
              onChange={(e) => setSelectedCustomer(e.target.value)}
              className="w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:border-jade-blue focus:outline-none"
            >
              {customers.map((customer) => (
                <option key={customer.customerId} value={customer.customerId}>
                  {customer.customerName}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-2">Select Package ZIP</label>
            <input
              type="file"
              accept=".zip"
              onChange={handleFileChange}
              className="w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:border-jade-blue focus:outline-none"
            />
            {selectedFile && (
              <p className="text-sm text-gray-600 mt-2">
                Selected: {selectedFile.name} ({(selectedFile.size / 1024 / 1024).toFixed(2)} MB)
              </p>
            )}
          </div>

          <button
            onClick={handleUpload}
            disabled={uploading || !selectedFile}
            className="bg-jade-gold text-jade-blue-dark px-6 py-3 rounded-lg font-semibold hover:bg-jade-gold-dark transition-all disabled:opacity-50 flex items-center gap-2 shadow-md"
          >
            <Upload size={20} />
            {uploading ? 'Uploading & Parsing...' : 'Upload Package'}
          </button>
        </div>
      </div>

      <div className="bg-white rounded-lg shadow-lg">
        <div className="p-6 border-b border-gray-200">
          <h2 className="text-2xl font-bold text-jade-blue">Uploaded Packages</h2>
        </div>
        <div className="p-4">
          {projects.length === 0 ? (
            <div className="text-center py-12">
              <Package className="mx-auto text-gray-300 mb-4" size={64} />
              <p className="text-gray-500 text-lg">No projects yet</p>
              <p className="text-sm text-gray-400">Upload a webMethods package to get started</p>
            </div>
          ) : (
            <div className="space-y-3">
              {projects.map((project) => (
                <div
                  key={project.projectId}
                  className="flex items-center justify-between p-4 border-2 border-gray-200 rounded-lg hover:border-jade-blue hover:shadow-md transition-all cursor-pointer"
                  onClick={() => navigate(`/projects/${project.projectId}`)}
                >
                  <div className="flex items-center gap-4">
                    <Package className="text-jade-blue" size={32} />
                    <div>
                      <div className="font-semibold text-lg text-jade-blue">{project.packageName}</div>
                      <div className="text-sm text-gray-600">
                        Uploaded: {new Date(project.uploadedAt).toLocaleString()} • {project.packageInfo?.services?.total || 0} services
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className={`px-3 py-1 rounded-full text-sm font-semibold ${getStatusBadge(project.status)}`}>
                      {project.status}
                    </span>
                    <ChevronRight className="text-gray-400" size={24} />
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
