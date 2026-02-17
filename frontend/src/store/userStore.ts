import { create } from 'zustand';
import type { User } from '@/types';
import { userApi } from '@/api/user';

interface UserState {
  user: User | null;
  isLoading: boolean;
  error: string | null;
  
  fetchUser: () => Promise<void>;
  updateBalance: (balance: number) => void;
  reset: () => void;
}

export const useUserStore = create<UserState>((set, get) => ({
  user: null,
  isLoading: false,
  error: null,

  fetchUser: async () => {
    if (get().user || get().isLoading) {
      return;
    }

    set({ isLoading: true, error: null });
    try {
      console.log('[userStore] Fetching user...');
      const user = await userApi.getMe();
      console.log('[userStore] User fetched:', user.telegram_id);
      set({ user, isLoading: false });
    } catch (error) {
      const message = (error as Error).message || 'Auth failed';
      console.error('[userStore] fetchUser failed:', message);
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

