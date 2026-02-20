import { clsx } from 'clsx';
import { Coins } from 'lucide-react';
import { Card } from '@/components/ui/Card';
import type { AIModel } from '@/types';
import { hapticFeedback } from '@/utils/telegram';

interface ModelCardProps {
  model: AIModel;
  isSelected?: boolean;
  onClick?: () => void;
}

export const ModelCard = ({ model, isSelected, onClick }: ModelCardProps) => {
  const handleClick = () => {
    hapticFeedback.light();
    onClick?.();
  };

  return (
    <Card
      onClick={handleClick}
      className={clsx(
        'cursor-pointer transition-all',
        isSelected
          ? 'ring-2 ring-tg-button bg-blue-50'
          : 'hover:shadow-md'
      )}
    >
      <div className="flex items-start gap-3">
        <div className="w-12 h-12 bg-tg-secondary-bg rounded-xl flex items-center justify-center text-2xl">
          {model.icon || '🤖'}
        </div>
        <div className="flex-1 min-w-0">
          <h3 className="font-semibold text-tg-text truncate">{model.name}</h3>
          {model.description && (
            <p className="text-sm text-tg-hint mt-0.5 line-clamp-2">
              {model.description}
            </p>
          )}
          <div className="flex items-center gap-1 mt-2 text-sm text-tg-button">
            <Coins className="w-4 h-4" />
            <span className="font-medium">
              {model.price_display_mode === 'per_second' && model.price_per_second != null
                ? `${model.price_per_second}⭐/сек`
                : `${model.price_tokens}⭐`}
            </span>
          </div>
        </div>
      </div>
    </Card>
  );
};
