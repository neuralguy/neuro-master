import { useQuery } from '@tanstack/react-query';
import { Users, CreditCard, Sparkles, TrendingUp, Coins, Ban } from 'lucide-react';

import { Card } from '@/components/ui/Card';
import { Loader } from '@/components/ui/Loader';
import { adminApi } from '@/api/admin';
import { formatNumber, formatMoney } from '@/utils/format';

interface StatCardProps {
  icon: React.ReactNode;
  label: string;
  value: string | number;
  subValue?: string;
  color: string;
}

const StatCard = ({ icon, label, value, subValue, color }: StatCardProps) => (
  <Card>
    <div className="flex items-center gap-3">
      <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${color}`}>
        {icon}
      </div>
      <div>
        <p className="text-sm text-tg-hint">{label}</p>
        <p className="text-xl font-bold text-tg-text">{value}</p>
        {subValue && <p className="text-xs text-tg-hint">{subValue}</p>}
      </div>
    </div>
  </Card>
);

export const DashboardPage = () => {
  const { data: stats, isLoading } = useQuery({
    queryKey: ['admin', 'stats'],
    queryFn: adminApi.getStats,
    refetchInterval: 30000, // Refresh every 30 seconds
  });

  if (isLoading) {
    return <Loader fullScreen text="Загрузка статистики..." />;
  }

  if (!stats) {
    return (
      <Card className="text-center py-8">
        <p className="text-tg-hint">Не удалось загрузить статистику</p>
      </Card>
    );
  }

  const successRate = stats.generations.total > 0
    ? Math.round((stats.generations.success / stats.generations.total) * 100)
    : 0;

  return (
    <div className="space-y-4">
      <h1 className="text-xl font-bold text-tg-text">Дашборд</h1>

      {/* Users Stats */}
      <div className="space-y-2">
        <h2 className="text-sm font-medium text-tg-hint px-1">Пользователи</h2>
        <div className="grid grid-cols-2 gap-3">
          <StatCard
            icon={<Users className="w-6 h-6 text-blue-600" />}
            label="Всего"
            value={formatNumber(stats.users.total_users)}
            color="bg-blue-100"
          />
          <StatCard
            icon={<Ban className="w-6 h-6 text-red-600" />}
            label="Забанено"
            value={formatNumber(stats.users.banned_users)}
            color="bg-red-100"
          />
          <StatCard
            icon={<Coins className="w-6 h-6 text-yellow-600" />}
            label="Общий баланс"
            value={formatNumber(stats.users.total_balance)}
            subValue="токенов"
            color="bg-yellow-100"
          />
        </div>
      </div>

      {/* Payments Stats */}
      <div className="space-y-2">
        <h2 className="text-sm font-medium text-tg-hint px-1">Платежи</h2>
        <div className="grid grid-cols-2 gap-3">
          <StatCard
            icon={<CreditCard className="w-6 h-6 text-green-600" />}
            label="Успешных"
            value={formatNumber(stats.payments.total_payments)}
            color="bg-green-100"
          />
          <StatCard
            icon={<TrendingUp className="w-6 h-6 text-emerald-600" />}
            label="Сумма"
            value={formatMoney(stats.payments.total_amount)}
            color="bg-emerald-100"
          />
        </div>
      </div>

      {/* Generations Stats */}
      <div className="space-y-2">
        <h2 className="text-sm font-medium text-tg-hint px-1">Генерации</h2>
        <div className="grid grid-cols-2 gap-3">
          <StatCard
            icon={<Sparkles className="w-6 h-6 text-purple-600" />}
            label="Всего"
            value={formatNumber(stats.generations.total)}
            subValue={`${successRate}% успешных`}
            color="bg-purple-100"
          />
          <StatCard
            icon={<Coins className="w-6 h-6 text-orange-600" />}
            label="Потрачено"
            value={formatNumber(stats.generations.tokens_spent)}
            subValue="токенов"
            color="bg-orange-100"
          />
        </div>
        
        {/* Generation Status Breakdown */}
        <Card>
          <div className="flex items-center justify-between text-sm">
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-green-500" />
              <span>Успешно</span>
            </div>
            <span className="font-medium">{formatNumber(stats.generations.success)}</span>
          </div>
          <div className="flex items-center justify-between text-sm mt-2">
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-yellow-500" />
              <span>В процессе</span>
            </div>
            <span className="font-medium">{formatNumber(stats.generations.pending)}</span>
          </div>
          <div className="flex items-center justify-between text-sm mt-2">
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-red-500" />
              <span>Ошибки</span>
            </div>
            <span className="font-medium">{formatNumber(stats.generations.failed)}</span>
          </div>
        </Card>
      </div>
    </div>
  );
};
