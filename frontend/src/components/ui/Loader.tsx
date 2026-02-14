import { clsx } from 'clsx';
import { Loader2 } from 'lucide-react';

interface LoaderProps {
  size?: 'sm' | 'md' | 'lg';
  className?: string;
  fullScreen?: boolean;
  text?: string;
}

export const Loader = ({ size = 'md', className, fullScreen = false, text }: LoaderProps) => {
  const sizes = {
    sm: 'w-4 h-4',
    md: 'w-8 h-8',
    lg: 'w-12 h-12',
  };

  const loader = (
    <div className={clsx('flex flex-col items-center justify-center gap-2', className)}>
      <Loader2 className={clsx('animate-spin text-tg-button', sizes[size])} />
      {text && <p className="text-sm text-tg-hint">{text}</p>}
    </div>
  );

  if (fullScreen) {
    return (
      <div className="fixed inset-0 flex items-center justify-center bg-tg-bg z-50">
        {loader}
      </div>
    );
  }

  return loader;
};
