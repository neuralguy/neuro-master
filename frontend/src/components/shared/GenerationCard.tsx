import { Clock, Check, X, Loader2, Download } from 'lucide-react';
import { clsx } from 'clsx';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import type { Generation } from '@/types';
import { formatDateTime, getStatusColor, getStatusText } from '@/utils/format';

interface GenerationCardProps {
  generation: Generation;
  onView?: () => void;
}

export const GenerationCard = ({ generation, onView }: GenerationCardProps) => {
  const statusIcons = {
    pending: Clock,
    processing: Loader2,
    success: Check,
    failed: X,
    cancelled: X,
  };

  const StatusIcon = statusIcons[generation.status];
  const isProcessing = generation.status === 'processing' || generation.status === 'pending';

  return (
    <Card className="overflow-hidden">
      {/* Preview */}
      <div className="aspect-square bg-tg-secondary-bg relative">
        {generation.result_file_url ? (
          generation.generation_type === 'video' ? (
            <video
              src={generation.result_file_url}
              className="w-full h-full object-cover"
              controls
            />
          ) : (
            <img
              src={generation.result_file_url}
              alt={generation.prompt || 'Generated'}
              className="w-full h-full object-cover"
            />
          )
        ) : (
          <div className="w-full h-full flex items-center justify-center">
            {isProcessing ? (
              <div className="text-center">
                <Loader2 className="w-8 h-8 animate-spin text-tg-button mx-auto" />
                <p className="text-sm text-tg-hint mt-2">Генерация...</p>
              </div>
            ) : (
              <p className="text-sm text-tg-hint">Нет превью</p>
            )}
          </div>
        )}
        
        {/* Status badge */}
        <div
          className={clsx(
            'absolute top-2 right-2 px-2 py-1 rounded-lg text-xs font-medium flex items-center gap-1',
            getStatusColor(generation.status)
          )}
        >
          <StatusIcon className={clsx('w-3 h-3', isProcessing && 'animate-spin')} />
          {getStatusText(generation.status)}
        </div>
      </div>

      {/* Info */}
      <div className="p-3">
        <p className="text-sm text-tg-text line-clamp-2">
          {generation.prompt || 'Без описания'}
        </p>
        <div className="flex items-center justify-between mt-2">
          <span className="text-xs text-tg-hint">
            {formatDateTime(generation.created_at)}
          </span>
          <span className="text-xs text-tg-hint">
            {generation.model_name || generation.model_code}
          </span>
        </div>
        
        {generation.result_file_url && (
          <div className="mt-3">
            <Button
              variant="outline"
              size="sm"
              className="w-full"
              onClick={onView}
              leftIcon={<Download className="w-4 h-4" />}
            >
              Скачать
            </Button>
          </div>
        )}
      </div>
    </Card>
  );
};
