import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Search, Ban, CheckCircle, Coins, ChevronRight } from 'lucide-react';

import { Card } from '@/components/ui/Card';
import { Input } from '@/components/ui/Input';
import { Button } from '@/components/ui/Button';
import { Modal } from '@/components/ui/Modal';
import { Loader } from '@/components/ui/Loader';

import { adminApi } from '@/api/admin';
import { hapticFeedback, showAlert, showConfirm } from '@/utils/telegram';
import { formatDate, formatNumber } from '@/utils/format';
import type { AdminUser } from '@/types';

export const UsersPage = () => {
  const [search, setSearch] = useState('');
  const [selectedUser, setSelectedUser] = useState<AdminUser | null>(null);
  const [newBalance, setNewBalance] = useState('');
  const queryClient = useQueryClient();

  const { data, isLoading, refetch } = useQuery({
    queryKey: ['admin', 'users', search],
    queryFn: () => adminApi.getUsers(0, 100, search || undefined),
  });

  const updateUserMutation = useMutation({
    mutationFn: ({ userId, updates }: { userId: number; updates: any }) =>
      adminApi.updateUser(userId, updates),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'users'] });
      hapticFeedback.success();
      showAlert('Пользователь обновлён');
    },
    onError: (error: Error) => {
      hapticFeedback.error();
      showAlert(error.message);
    },
  });

  const handleBan = async (user: AdminUser) => {
    const action = user.is_banned ? 'разбанить' : 'забанить';
    const confirmed = await showConfirm(`Вы уверены, что хотите ${action} пользователя ${user.first_name}?`);
    
    if (confirmed) {
      updateUserMutation.mutate({
        userId: user.id,
        updates: { is_banned: !user.is_banned },
      });
    }
  };

  const handleSetBalance = () => {
    if (!selectedUser) return;
    
    const balance = parseInt(newBalance);
    if (isNaN(balance) || balance < 0) {
      showAlert('Введите корректное число');
      return;
    }

    updateUserMutation.mutate({
      userId: selectedUser.id,
      updates: { balance },
    });
    setSelectedUser(null);
    setNewBalance('');
  };

  if (isLoading) {
    return <Loader fullScreen text="Загрузка пользователей..." />;
  }

  const users = data?.items || [];

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold text-tg-text">Пользователи</h1>
        <span className="text-sm text-tg-hint">{data?.total || 0} всего</span>
      </div>

      {/* Search */}
      <Input
        placeholder="Поиск по имени, username, ID..."
        value={search}
        onChange={(e) => setSearch(e.target.value)}
        leftIcon={<Search className="w-5 h-5" />}
      />

      {/* Users List */}
      {users.length === 0 ? (
        <Card className="text-center py-8">
          <p className="text-tg-hint">Пользователи не найдены</p>
        </Card>
      ) : (
        <div className="space-y-2">
          {users.map((user) => (
            <Card
              key={user.id}
              className="cursor-pointer hover:shadow-md transition-shadow"
              onClick={() => {
                hapticFeedback.light();
                setSelectedUser(user);
                setNewBalance(user.balance.toString());
              }}
            >
              <div className="flex items-center gap-3">
                <div className={`w-10 h-10 rounded-full flex items-center justify-center text-white font-medium ${
                  user.is_banned ? 'bg-red-500' : user.is_admin ? 'bg-purple-500' : 'bg-blue-500'
                }`}>
                  {user.first_name[0]}
                </div>
                
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <p className="font-medium text-tg-text truncate">
                      {user.first_name} {user.last_name}
                    </p>
                    {user.is_admin && (
                      <span className="px-1.5 py-0.5 bg-purple-100 text-purple-700 text-xs rounded">
                        Admin
                      </span>
                    )}
                    {user.is_banned && (
                      <span className="px-1.5 py-0.5 bg-red-100 text-red-700 text-xs rounded">
                        Бан
                      </span>
                    )}
                  </div>
                  <p className="text-sm text-tg-hint truncate">
                    {user.username ? `@${user.username}` : `ID: ${user.telegram_id}`}
                  </p>
                </div>

                <div className="text-right">
                  <p className="font-medium text-tg-text">{formatNumber(user.balance)}</p>
                  <p className="text-xs text-tg-hint">токенов</p>
                </div>

                <ChevronRight className="w-5 h-5 text-tg-hint" />
              </div>
            </Card>
          ))}
        </div>
      )}

      {/* User Detail Modal */}
      <Modal
        isOpen={!!selectedUser}
        onClose={() => {
          setSelectedUser(null);
          setNewBalance('');
        }}
        title="Пользователь"
      >
        {selectedUser && (
          <div className="space-y-4">
            {/* User Info */}
            <div className="flex items-center gap-4">
              <div className={`w-16 h-16 rounded-full flex items-center justify-center text-white text-2xl font-medium ${
                selectedUser.is_banned ? 'bg-red-500' : 'bg-blue-500'
              }`}>
                {selectedUser.first_name[0]}
              </div>
              <div>
                <h3 className="text-lg font-semibold text-tg-text">
                  {selectedUser.first_name} {selectedUser.last_name}
                </h3>
                <p className="text-tg-hint">
                  {selectedUser.username ? `@${selectedUser.username}` : `ID: ${selectedUser.telegram_id}`}
                </p>
              </div>
            </div>

            {/* Stats */}
            <div className="grid grid-cols-2 gap-3">
              <Card padding="sm" className="bg-tg-secondary-bg">
                <p className="text-xs text-tg-hint">Баланс</p>
                <p className="text-lg font-bold text-tg-text">
                  {formatNumber(selectedUser.balance)}
                </p>
              </Card>
              <Card padding="sm" className="bg-tg-secondary-bg">
                <p className="text-xs text-tg-hint">Генераций</p>
                <p className="text-lg font-bold text-tg-text">
                  {formatNumber(selectedUser.total_generations)}
                </p>
              </Card>
            </div>

            {/* Info */}
            <div className="text-sm text-tg-hint space-y-1">
              <p>Telegram ID: <span className="text-tg-text">{selectedUser.telegram_id}</span></p>
              <p>Регистрация: <span className="text-tg-text">{formatDate(selectedUser.created_at)}</span></p>
            </div>

            {/* Change Balance */}
            <div className="space-y-2">
              <label className="text-sm font-medium text-tg-text">Изменить баланс</label>
              <div className="flex gap-2">
                <Input
                  type="number"
                  value={newBalance}
                  onChange={(e) => setNewBalance(e.target.value)}
                  placeholder="Новый баланс"
                  className="flex-1"
                />
                <Button
                  onClick={handleSetBalance}
                  isLoading={updateUserMutation.isPending}
                  leftIcon={<Coins className="w-4 h-4" />}
                >
                  Сохранить
                </Button>
              </div>
            </div>

            {/* Ban/Unban */}
            {!selectedUser.is_admin && (
              <Button
                variant={selectedUser.is_banned ? 'primary' : 'danger'}
                className="w-full"
                onClick={() => handleBan(selectedUser)}
                isLoading={updateUserMutation.isPending}
                leftIcon={selectedUser.is_banned ? <CheckCircle className="w-4 h-4" /> : <Ban className="w-4 h-4" />}
              >
                {selectedUser.is_banned ? 'Разбанить' : 'Забанить'}
              </Button>
            )}
          </div>
        )}
      </Modal>
    </div>
  );
};
