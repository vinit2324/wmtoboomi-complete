import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { Customer, Project } from '../types';

interface AppState {
  // Current selections
  currentCustomer: Customer | null;
  currentProject: Project | null;
  
  // UI state
  sidebarOpen: boolean;
  
  // Actions
  setCurrentCustomer: (customer: Customer | null) => void;
  setCurrentProject: (project: Project | null) => void;
  toggleSidebar: () => void;
  setSidebarOpen: (open: boolean) => void;
}

export const useStore = create<AppState>()(
  persist(
    (set) => ({
      // Initial state
      currentCustomer: null,
      currentProject: null,
      sidebarOpen: true,
      
      // Actions
      setCurrentCustomer: (customer) => set({ currentCustomer: customer }),
      setCurrentProject: (project) => set({ currentProject: project }),
      toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),
      setSidebarOpen: (open) => set({ sidebarOpen: open }),
    }),
    {
      name: 'wmtoboomi-store',
      partialize: (state) => ({
        currentCustomer: state.currentCustomer,
        sidebarOpen: state.sidebarOpen,
      }),
    }
  )
);
