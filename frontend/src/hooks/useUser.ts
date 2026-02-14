import { useEffect } from 'react';
import { useUserStore } from '@/store/userStore';

export const useUser = () => {
  const { user, isLoading, error, fetchUser, updateBalance } = useUserStore();

  useEffect(() => {
    if (!user && !isLoading) {
      fetchUser();
    }
  }, []);

  return {
    user,
    isLoading,
    error,
    refetch: fetchUser,
    updateBalance,
  };
};
