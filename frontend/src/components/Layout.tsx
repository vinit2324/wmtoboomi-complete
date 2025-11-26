import React, { useState, useEffect } from 'react';
import { Outlet, NavLink } from 'react-router-dom';
import { LayoutDashboard, Users, Package, Bot, FileText, ChevronDown } from 'lucide-react';
import axios from 'axios';

const navItems = [
  { to: '/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/customers', icon: Users, label: 'Customers' },
  { to: '/projects', icon: Package, label: 'Projects' },
  { to: '/ai', icon: Bot, label: 'AI Assistant' },
  { to: '/logs', icon: FileText, label: 'Activity Logs' },
];

export default function Layout() {
  const [customers, setCustomers] = useState<any[]>([]);
  const [selectedCustomer, setSelectedCustomer] = useState<string>('all');
  const [dropdownOpen, setDropdownOpen] = useState(false);

  useEffect(() => {
    loadCustomers();
  }, []);

  const loadCustomers = async () => {
    try {
      const response = await axios.get('http://localhost:7201/api/customers');
      setCustomers(response.data.customers || []);
    } catch (error) {
      console.error('Error loading customers:', error);
    }
  };

  const getSelectedCustomerName = () => {
    if (selectedCustomer === 'all') return 'All Customers';
    const customer = customers.find(c => c.customerId === selectedCustomer);
    return customer?.customerName || 'Select Customer';
  };

  return (
    <div className="min-h-screen bg-jade-gray flex flex-col">
      {/* Header */}
      <header className="h-16 bg-jade-blue text-white flex items-center justify-between px-6 shadow-lg relative z-50">
        <div className="flex items-center gap-4">
          <img src="/jade-logo1.png" alt="Jade Global" className="h-12" />
          <div className="h-8 w-px bg-white opacity-30"></div>
          <h1 className="text-xl font-semibold">webMethods to Boomi Migration Accelerator</h1>
        </div>
        
        <div className="flex items-center gap-4">
          <span className="text-jade-gold font-medium">Active Customer</span>
          
          {/* Custom Dropdown */}
          <div className="relative">
            <button
              onClick={() => setDropdownOpen(!dropdownOpen)}
              className="bg-jade-blue-dark text-white px-4 py-2 rounded border border-jade-blue-light flex items-center gap-2 min-w-[200px] justify-between hover:bg-opacity-80 transition-colors"
            >
              <span className="truncate">{getSelectedCustomerName()}</span>
              <ChevronDown size={18} className={`transition-transform ${dropdownOpen ? 'rotate-180' : ''}`} />
            </button>
            
            {dropdownOpen && (
              <>
                {/* Backdrop */}
                <div 
                  className="fixed inset-0 z-40" 
                  onClick={() => setDropdownOpen(false)}
                />
                
                {/* Dropdown Menu */}
                <div className="absolute right-0 mt-2 w-64 bg-white rounded-lg shadow-xl border border-gray-200 z-50 overflow-hidden">
                  <div className="p-2 border-b bg-gray-50">
                    <div className="text-xs font-semibold text-gray-500 uppercase">Select Customer</div>
                  </div>
                  
                  <div className="max-h-64 overflow-y-auto">
                    {/* All Customers Option */}
                    <button
                      onClick={() => {
                        setSelectedCustomer('all');
                        setDropdownOpen(false);
                      }}
                      className={`w-full px-4 py-3 text-left hover:bg-jade-blue hover:text-white transition-colors flex items-center justify-between ${
                        selectedCustomer === 'all' ? 'bg-jade-blue text-white' : 'text-gray-700'
                      }`}
                    >
                      <span>All Customers</span>
                      {selectedCustomer === 'all' && <span className="text-jade-gold">✓</span>}
                    </button>
                    
                    {/* Individual Customers */}
                    {customers.length === 0 ? (
                      <div className="px-4 py-3 text-gray-500 text-sm">
                        No customers yet. Add one in Customers page.
                      </div>
                    ) : (
                      customers.map((customer) => (
                        <button
                          key={customer.customerId}
                          onClick={() => {
                            setSelectedCustomer(customer.customerId);
                            setDropdownOpen(false);
                          }}
                          className={`w-full px-4 py-3 text-left hover:bg-jade-blue hover:text-white transition-colors flex items-center justify-between ${
                            selectedCustomer === customer.customerId ? 'bg-jade-blue text-white' : 'text-gray-700'
                          }`}
                        >
                          <div>
                            <div className="font-medium">{customer.customerName}</div>
                            <div className={`text-xs ${selectedCustomer === customer.customerId ? 'text-jade-gold' : 'text-gray-500'}`}>
                              {customer.settings?.boomi?.accountId ? 'Boomi configured' : 'No Boomi config'}
                            </div>
                          </div>
                          {selectedCustomer === customer.customerId && <span className="text-jade-gold">✓</span>}
                        </button>
                      ))
                    )}
                  </div>
                  
                  {/* Footer */}
                  <div className="p-2 border-t bg-gray-50">
                    <NavLink
                      to="/customers"
                      onClick={() => setDropdownOpen(false)}
                      className="block w-full px-3 py-2 text-center text-sm text-jade-blue hover:bg-jade-blue hover:text-white rounded transition-colors"
                    >
                      + Manage Customers
                    </NavLink>
                  </div>
                </div>
              </>
            )}
          </div>
        </div>
      </header>

      <div className="flex flex-1">
        {/* Sidebar */}
        <aside className="w-60 bg-white shadow-lg">
          <nav className="p-4 space-y-2">
            {navItems.map(({ to, icon: Icon, label }) => (
              <NavLink
                key={to}
                to={to}
                className={({ isActive }) =>
                  `flex items-center gap-3 px-4 py-3 rounded-lg transition-all ${
                    isActive
                      ? 'bg-jade-blue text-white shadow-md'
                      : 'text-gray-700 hover:bg-jade-gray'
                  }`
                }
              >
                <Icon size={20} />
                <span className="font-medium">{label}</span>
              </NavLink>
            ))}
          </nav>
          
          {/* Selected Customer Info in Sidebar */}
          {selectedCustomer !== 'all' && (
            <div className="mx-4 p-3 bg-jade-gold bg-opacity-20 rounded-lg border border-jade-gold">
              <div className="text-xs font-semibold text-jade-blue-dark mb-1">Active Customer</div>
              <div className="text-sm font-medium text-jade-blue">{getSelectedCustomerName()}</div>
            </div>
          )}
        </aside>

        {/* Main Content */}
        <main className="flex-1 overflow-auto flex flex-col">
          <div className="flex-1">
            <Outlet context={{ selectedCustomer, customers }} />
          </div>
          
          {/* Footer */}
          <footer className="bg-jade-blue text-white py-4 px-6">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-xs text-jade-gold font-semibold">ENTERPRISE EDITION</div>
                <div className="text-sm font-medium">Delivering Innovation, Driving Impact™</div>
              </div>
              <div className="text-sm opacity-80">
                © 2025 Jade Global, Inc. All rights reserved.
              </div>
            </div>
          </footer>
        </main>
      </div>
    </div>
  );
}
