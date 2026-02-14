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

export const useUserStore = create<UserState>((set) => ({
  user: null,
  isLoading: false,
  error: null,

  fetchUser: async () => {
    set({ isLoading: true, error: null });
    try {
      const user = await userApi.getMe();
      set({ user, isLoading: false });
    } catch (error) {
      set({ error: (error as Error).message, isLoading: false });
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
