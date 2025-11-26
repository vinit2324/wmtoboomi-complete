import { Outlet, NavLink, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import {
  LayoutDashboard,
  Users,
  FolderOpen,
  GitCompare,
  Bot,
  FileText,
  ChevronLeft,
  ChevronRight,
  Settings,
  LogOut,
} from 'lucide-react';
import { useStore } from '../stores/useStore';
import { customersApi } from '../utils/api';
import type { Customer } from '../types';

const navItems = [
  { path: '/', icon: LayoutDashboard, label: 'Dashboard' },
  { path: '/customers', icon: Users, label: 'Customers' },
  { path: '/projects', icon: FolderOpen, label: 'Projects' },
  { path: '/ai', icon: Bot, label: 'AI Assistant' },
  { path: '/logs', icon: FileText, label: 'Activity Logs' },
];

export default function Layout() {
  const navigate = useNavigate();
  const { sidebarOpen, toggleSidebar, currentCustomer, setCurrentCustomer } = useStore();

  const { data: customersData } = useQuery({
    queryKey: ['customers'],
    queryFn: async () => {
      const response = await customersApi.list();
      return response.data;
    },
  });

  const customers = customersData?.customers || [];

  return (
    <div className="min-h-screen flex">
      {/* Sidebar */}
      <aside
        className={`bg-white border-r border-gray-200 flex flex-col transition-all duration-300 ${
          sidebarOpen ? 'w-64' : 'w-20'
        }`}
      >
        {/* Logo */}
        <div className="h-16 flex items-center px-4 border-b border-gray-200">
          <img
            src="/jade-logo1.png"
            alt="Jade Global"
            className="h-10 w-auto"
            onError={(e) => {
              e.currentTarget.style.display = 'none';
            }}
          />
          {sidebarOpen && (
            <span className="ml-3 font-semibold text-jade-600 text-sm">
              Jade Global
            </span>
          )}
        </div>

        {/* Customer Selector */}
        {sidebarOpen && (
          <div className="p-4 border-b border-gray-200">
            <label className="label">Active Customer</label>
            <select
              className="input text-sm"
              value={currentCustomer?.customerId || ''}
              onChange={(e) => {
                const customer = customers.find(
                  (c: Customer) => c.customerId === e.target.value
                );
                setCurrentCustomer(customer || null);
              }}
            >
              <option value="">Select customer...</option>
              {customers.map((customer: Customer) => (
                <option key={customer.customerId} value={customer.customerId}>
                  {customer.customerName}
                </option>
              ))}
            </select>
          </div>
        )}

        {/* Navigation */}
        <nav className="flex-1 py-4">
          {navItems.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              className={({ isActive }) =>
                `flex items-center px-4 py-3 mx-2 rounded-lg transition-colors ${
                  isActive
                    ? 'bg-jade-50 text-jade-600'
                    : 'text-gray-600 hover:bg-gray-50'
                }`
              }
            >
              <item.icon className="w-5 h-5 flex-shrink-0" />
              {sidebarOpen && <span className="ml-3">{item.label}</span>}
            </NavLink>
          ))}
        </nav>

        {/* Toggle Button */}
        <div className="p-4 border-t border-gray-200">
          <button
            onClick={toggleSidebar}
            className="w-full flex items-center justify-center p-2 text-gray-500 hover:bg-gray-100 rounded-lg"
          >
            {sidebarOpen ? (
              <>
                <ChevronLeft className="w-5 h-5" />
                <span className="ml-2">Collapse</span>
              </>
            ) : (
              <ChevronRight className="w-5 h-5" />
            )}
          </button>
        </div>
      </aside>

      {/* Main Content */}
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <header className="h-16 bg-jade-500 flex items-center justify-between px-6 text-white">
          <h1 className="text-lg font-semibold">
            webMethods to Boomi Migration Accelerator
          </h1>
          <div className="flex items-center gap-4">
            {currentCustomer && (
              <span className="text-sm bg-jade-600 px-3 py-1 rounded-full">
                {currentCustomer.customerName}
              </span>
            )}
          </div>
        </header>

        {/* Page Content */}
        <main className="flex-1 p-6 bg-gray-50 overflow-auto">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
