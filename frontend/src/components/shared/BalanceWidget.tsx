import { Wallet, Plus } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { useUser } from '@/hooks/useUser';
import { formatTokens } from '@/utils/format';

export const BalanceWidget = () => {
  const navigate = useNavigate();
  const { user } = useUser();

  return (
    <Card className="bg-gradient-to-r from-blue-500 to-blue-600 text-white">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 bg-white/20 rounded-xl flex items-center justify-center">
            <Wallet className="w-6 h-6" />
          </div>
          <div>
            <p className="text-sm text-white/70">Баланс</p>
            <p className="text-2xl font-bold">
              {user ? formatTokens(user.balance) : '...'}
            </p>
          </div>
        </div>
        <Button
          variant="secondary"
          size="sm"
          onClick={() => navigate('/balance')}
          className="bg-white/20 hover:bg-white/30 text-white"
          leftIcon={<Plus className="w-4 h-4" />}
        >
          Пополнить
        </Button>
      </div>
    </Card>
  );
};
