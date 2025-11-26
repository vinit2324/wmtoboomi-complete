import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Users,
  Plus,
  Edit2,
  Trash2,
  Check,
  X,
  Loader2,
  TestTube,
  Settings,
} from 'lucide-react';
import { customersApi } from '../utils/api';
import { useStore } from '../stores/useStore';
import type { Customer, CustomerSettings } from '../types';

const defaultSettings: CustomerSettings = {
  boomi: {
    accountId: '',
    username: '',
    apiToken: '',
    baseUrl: 'https://api.boomi.com/api/rest/v1',
    defaultFolder: 'Jade Global, Inc./MigrationPoC',
  },
  llm: {
    provider: 'openai',
    apiKey: '',
    baseUrl: '',
    model: 'gpt-4-turbo',
    temperature: 0.7,
  },
};

export default function Customers() {
  const queryClient = useQueryClient();
  const { setCurrentCustomer, currentCustomer } = useStore();
  const [showModal, setShowModal] = useState(false);
  const [editingCustomer, setEditingCustomer] = useState<Customer | null>(null);
  const [formData, setFormData] = useState({
    customerName: '',
    settings: defaultSettings,
  });
  const [testResults, setTestResults] = useState<{ boomi?: string; llm?: string }>({});

  const { data, isLoading } = useQuery({
    queryKey: ['customers'],
    queryFn: async () => {
      const response = await customersApi.list();
      return response.data;
    },
  });

  const createMutation = useMutation({
    mutationFn: (data: { customerName: string; settings: CustomerSettings }) =>
      customersApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['customers'] });
      closeModal();
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: unknown }) =>
      customersApi.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['customers'] });
      closeModal();
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => customersApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['customers'] });
    },
  });

  const customers = data?.customers || [];

  const openCreateModal = () => {
    setEditingCustomer(null);
    setFormData({ customerName: '', settings: defaultSettings });
    setTestResults({});
    setShowModal(true);
  };

  const openEditModal = (customer: Customer) => {
    setEditingCustomer(customer);
    setFormData({
      customerName: customer.customerName,
      settings: customer.settings,
    });
    setTestResults({});
    setShowModal(true);
  };

  const closeModal = () => {
    setShowModal(false);
    setEditingCustomer(null);
    setFormData({ customerName: '', settings: defaultSettings });
    setTestResults({});
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (editingCustomer) {
      updateMutation.mutate({ id: editingCustomer.customerId, data: formData });
    } else {
      createMutation.mutate(formData);
    }
  };

  const testBoomiConnection = async () => {
    if (!editingCustomer) return;
    try {
      const response = await customersApi.testBoomi(editingCustomer.customerId);
      setTestResults((prev) => ({
        ...prev,
        boomi: response.data.success ? '✅ Connected' : `❌ ${response.data.message}`,
      }));
    } catch (error) {
      setTestResults((prev) => ({ ...prev, boomi: '❌ Test failed' }));
    }
  };

  const testLlmConnection = async () => {
    if (!editingCustomer) return;
    try {
      const response = await customersApi.testLlm(editingCustomer.customerId);
      setTestResults((prev) => ({
        ...prev,
        llm: response.data.success ? '✅ Connected' : `❌ ${response.data.message}`,
      }));
    } catch (error) {
      setTestResults((prev) => ({ ...prev, llm: '❌ Test failed' }));
    }
  };

  return (
    <div className="space-y-6 animate-fadeIn">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Customers</h1>
          <p className="text-gray-500">Manage customer accounts and settings</p>
        </div>
        <button onClick={openCreateModal} className="btn-primary flex items-center">
          <Plus className="w-5 h-5 mr-2" />
          Add Customer
        </button>
      </div>

      {/* Customer List */}
      {isLoading ? (
        <div className="card flex items-center justify-center py-12">
          <Loader2 className="w-8 h-8 animate-spin text-jade-500" />
        </div>
      ) : customers.length === 0 ? (
        <div className="card text-center py-12">
          <Users className="w-16 h-16 mx-auto text-gray-300 mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No customers yet</h3>
          <p className="text-gray-500 mb-4">
            Add your first customer to start managing migrations
          </p>
          <button onClick={openCreateModal} className="btn-primary">
            <Plus className="w-5 h-5 mr-2 inline" />
            Add Customer
          </button>
        </div>
      ) : (
        <div className="grid gap-4">
          {customers.map((customer: Customer) => (
            <div
              key={customer.customerId}
              className={`card hover:shadow-md transition-shadow ${
                currentCustomer?.customerId === customer.customerId
                  ? 'ring-2 ring-jade-500'
                  : ''
              }`}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center">
                  <div className="w-12 h-12 bg-jade-100 rounded-lg flex items-center justify-center">
                    <Users className="w-6 h-6 text-jade-600" />
                  </div>
                  <div className="ml-4">
                    <h3 className="font-semibold text-lg">{customer.customerName}</h3>
                    <div className="flex items-center gap-4 text-sm text-gray-500">
                      <span>
                        Boomi: {customer.settings.boomi.accountId ? '✅ Configured' : '❌ Not set'}
                      </span>
                      <span>
                        LLM: {customer.settings.llm.apiKey ? '✅ Configured' : '❌ Not set'}
                      </span>
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  {currentCustomer?.customerId !== customer.customerId && (
                    <button
                      onClick={() => setCurrentCustomer(customer)}
                      className="btn-secondary text-sm"
                    >
                      Select
                    </button>
                  )}
                  <button
                    onClick={() => openEditModal(customer)}
                    className="p-2 text-gray-500 hover:bg-gray-100 rounded-lg"
                  >
                    <Settings className="w-5 h-5" />
                  </button>
                  <button
                    onClick={() => {
                      if (confirm('Delete this customer?')) {
                        deleteMutation.mutate(customer.customerId);
                      }
                    }}
                    className="p-2 text-red-500 hover:bg-red-50 rounded-lg"
                  >
                    <Trash2 className="w-5 h-5" />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl shadow-xl w-full max-w-2xl max-h-[90vh] overflow-y-auto m-4">
            <div className="p-6 border-b border-gray-200">
              <h2 className="text-xl font-semibold">
                {editingCustomer ? 'Edit Customer' : 'Add Customer'}
              </h2>
            </div>
            <form onSubmit={handleSubmit} className="p-6 space-y-6">
              {/* Customer Name */}
              <div>
                <label className="label">Customer Name</label>
                <input
                  type="text"
                  className="input"
                  value={formData.customerName}
                  onChange={(e) =>
                    setFormData({ ...formData, customerName: e.target.value })
                  }
                  required
                />
              </div>

              {/* Boomi Settings */}
              <div className="border rounded-lg p-4">
                <h3 className="font-medium mb-4 flex items-center justify-between">
                  Boomi Settings
                  {editingCustomer && (
                    <button
                      type="button"
                      onClick={testBoomiConnection}
                      className="btn-secondary text-sm"
                    >
                      <TestTube className="w-4 h-4 mr-1" />
                      Test
                    </button>
                  )}
                </h3>
                {testResults.boomi && (
                  <p className="text-sm mb-4">{testResults.boomi}</p>
                )}
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="label">Account ID</label>
                    <input
                      type="text"
                      className="input"
                      value={formData.settings.boomi.accountId}
                      onChange={(e) =>
                        setFormData({
                          ...formData,
                          settings: {
                            ...formData.settings,
                            boomi: { ...formData.settings.boomi, accountId: e.target.value },
                          },
                        })
                      }
                    />
                  </div>
                  <div>
                    <label className="label">Username</label>
                    <input
                      type="text"
                      className="input"
                      value={formData.settings.boomi.username}
                      onChange={(e) =>
                        setFormData({
                          ...formData,
                          settings: {
                            ...formData.settings,
                            boomi: { ...formData.settings.boomi, username: e.target.value },
                          },
                        })
                      }
                    />
                  </div>
                  <div className="col-span-2">
                    <label className="label">API Token</label>
                    <input
                      type="password"
                      className="input"
                      value={formData.settings.boomi.apiToken}
                      onChange={(e) =>
                        setFormData({
                          ...formData,
                          settings: {
                            ...formData.settings,
                            boomi: { ...formData.settings.boomi, apiToken: e.target.value },
                          },
                        })
                      }
                      placeholder="Enter to update..."
                    />
                  </div>
                </div>
              </div>

              {/* LLM Settings */}
              <div className="border rounded-lg p-4">
                <h3 className="font-medium mb-4 flex items-center justify-between">
                  LLM Settings
                  {editingCustomer && (
                    <button
                      type="button"
                      onClick={testLlmConnection}
                      className="btn-secondary text-sm"
                    >
                      <TestTube className="w-4 h-4 mr-1" />
                      Test
                    </button>
                  )}
                </h3>
                {testResults.llm && (
                  <p className="text-sm mb-4">{testResults.llm}</p>
                )}
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="label">Provider</label>
                    <select
                      className="input"
                      value={formData.settings.llm.provider}
                      onChange={(e) =>
                        setFormData({
                          ...formData,
                          settings: {
                            ...formData.settings,
                            llm: {
                              ...formData.settings.llm,
                              provider: e.target.value as 'openai' | 'anthropic' | 'gemini' | 'ollama',
                            },
                          },
                        })
                      }
                    >
                      <option value="openai">OpenAI</option>
                      <option value="anthropic">Anthropic (Claude)</option>
                      <option value="gemini">Google Gemini</option>
                      <option value="ollama">Ollama (Local)</option>
                    </select>
                  </div>
                  <div>
                    <label className="label">Model</label>
                    <input
                      type="text"
                      className="input"
                      value={formData.settings.llm.model}
                      onChange={(e) =>
                        setFormData({
                          ...formData,
                          settings: {
                            ...formData.settings,
                            llm: { ...formData.settings.llm, model: e.target.value },
                          },
                        })
                      }
                    />
                  </div>
                  <div className="col-span-2">
                    <label className="label">API Key</label>
                    <input
                      type="password"
                      className="input"
                      value={formData.settings.llm.apiKey}
                      onChange={(e) =>
                        setFormData({
                          ...formData,
                          settings: {
                            ...formData.settings,
                            llm: { ...formData.settings.llm, apiKey: e.target.value },
                          },
                        })
                      }
                      placeholder="Enter to update..."
                    />
                  </div>
                </div>
              </div>

              {/* Actions */}
              <div className="flex justify-end gap-3">
                <button type="button" onClick={closeModal} className="btn-secondary">
                  Cancel
                </button>
                <button
                  type="submit"
                  className="btn-primary"
                  disabled={createMutation.isPending || updateMutation.isPending}
                >
                  {createMutation.isPending || updateMutation.isPending ? (
                    <Loader2 className="w-5 h-5 animate-spin" />
                  ) : editingCustomer ? (
                    'Update'
                  ) : (
                    'Create'
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
