import { create } from 'zustand';
import type { User } from '@/types';
import { userApi } from '@/api/user';

interface UserState {
  user: User | null;
  isLoading: boolean;
  error: string | null;
  
  // Actions
  fetchUser: () => Promise<void>;
  updateBalance: (balance: number) => void;
  reset: () => void;
}

export const useUserStore = create<UserState>((set, get) => ({
  user: null,
  isLoading: true,
  error: null,

  fetchUser: async () => {
    // Prevent duplicate calls
    if (get().user) {
      set({ isLoading: false });
      return;
    }
    
    set({ isLoading: true, error: null });
    try {
      const user = await userApi.getMe();
      set({ user, isLoading: false });
    } catch (error) {
      const message = (error as Error).message || 'Auth failed';
      console.error('Failed to fetch user:', message);
      set({ error: message, isLoading: false });
    }
  },

  updateBalance: (balance: number) => {
    set((state) => ({
      user: state.user ? { ...state.user, balance } : null,
    }));
  },

  reset: () => {
    set({ user: null, isLoading: false, error: null });
  },
}));
