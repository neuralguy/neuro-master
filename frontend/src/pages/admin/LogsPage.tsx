import { useState, useEffect, useRef } from 'react';
import { Wifi, WifiOff, Trash2, Pause, Play, Filter } from 'lucide-react';
import { clsx } from 'clsx';

import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { useWebSocket } from '@/hooks/useWebSocket';
import { formatTime } from '@/utils/format';
import type { LogEntry } from '@/types';

const LOG_LEVELS = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'];

const getLevelColor = (level: string) => {
  switch (level) {
    case 'DEBUG': return 'text-gray-500 bg-gray-100';
    case 'INFO': return 'text-blue-600 bg-blue-100';
    case 'SUCCESS': return 'text-green-600 bg-green-100';
    case 'WARNING': return 'text-yellow-600 bg-yellow-100';
    case 'ERROR': return 'text-red-600 bg-red-100';
    case 'CRITICAL': return 'text-red-800 bg-red-200';
    default: return 'text-gray-600 bg-gray-100';
  }
};

export const LogsPage = () => {
  const [isPaused, setIsPaused] = useState(false);
  const [filterLevels, setFilterLevels] = useState<string[]>(LOG_LEVELS);
  const [showFilters, setShowFilters] = useState(false);
  const logsEndRef = useRef<HTMLDivElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  const { isConnected, logs, clearLogs, connect, disconnect } = useWebSocket({
    autoConnect: true,
  });

  // Auto-scroll to bottom when new logs arrive (if not paused)
  useEffect(() => {
    if (!isPaused && logsEndRef.current) {
      logsEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [logs, isPaused]);

  const toggleLevel = (level: string) => {
    setFilterLevels((prev) =>
      prev.includes(level)
        ? prev.filter((l) => l !== level)
        : [...prev, level]
    );
  };

  const filteredLogs = logs.filter((log) => filterLevels.includes(log.level));

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <h1 className="text-xl font-bold text-tg-text">Логи</h1>
          <div className={clsx(
            'flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium',
            isConnected ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
          )}>
            {isConnected ? (
              <>
                <Wifi className="w-3 h-3" />
                Подключено
              </>
            ) : (
              <>
                <WifiOff className="w-3 h-3" />
                Отключено
              </>
            )}
          </div>
        </div>
        
        <div className="flex items-center gap-2">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setShowFilters(!showFilters)}
          >
            <Filter className="w-4 h-4" />
          </Button>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setIsPaused(!isPaused)}
          >
            {isPaused ? <Play className="w-4 h-4" /> : <Pause className="w-4 h-4" />}
          </Button>
          <Button
            variant="ghost"
            size="sm"
            onClick={clearLogs}
          >
            <Trash2 className="w-4 h-4" />
          </Button>
        </div>
      </div>

      {/* Filters */}
      {showFilters && (
        <Card padding="sm">
          <div className="flex flex-wrap gap-2">
            {LOG_LEVELS.map((level) => (
              <button
                key={level}
                onClick={() => toggleLevel(level)}
                className={clsx(
                  'px-3 py-1 rounded-lg text-xs font-medium transition-colors',
                  filterLevels.includes(level)
                    ? getLevelColor(level)
                    : 'bg-gray-100 text-gray-400'
                )}
              >
                {level}
              </button>
            ))}
          </div>
        </Card>
      )}

      {/* Connection Controls */}
      {!isConnected && (
        <Card className="text-center py-4">
          <p className="text-tg-hint mb-3">WebSocket отключен</p>
          <Button onClick={connect}>Подключиться</Button>
        </Card>
      )}

      {/* Logs Container */}
      <div
        ref={containerRef}
        className="bg-gray-900 rounded-xl p-3 h-[60vh] overflow-y-auto font-mono text-xs"
      >
        {filteredLogs.length === 0 ? (
          <div className="h-full flex items-center justify-center text-gray-500">
            {isConnected ? 'Ожидание логов...' : 'Нет подключения'}
          </div>
        ) : (
          <div className="space-y-1">
            {filteredLogs.map((log, index) => (
              <LogLine key={`${log.timestamp}-${index}`} log={log} />
            ))}
            <div ref={logsEndRef} />
          </div>
        )}
      </div>

      {/* Status Bar */}
      <div className="flex items-center justify-between text-xs text-tg-hint">
        <span>{filteredLogs.length} записей</span>
        {isPaused && <span className="text-yellow-600">⏸ Пауза</span>}
      </div>
    </div>
  );
};

interface LogLineProps {
  log: LogEntry;
}

const LogLine = ({ log }: LogLineProps) => {
  const [isExpanded, setIsExpanded] = useState(false);

  return (
    <div
      className="group hover:bg-gray-800 rounded px-2 py-1 cursor-pointer"
      onClick={() => setIsExpanded(!isExpanded)}
    >
      <div className="flex items-start gap-2">
        {/* Timestamp */}
        <span className="text-gray-500 whitespace-nowrap">
          {formatTime(log.timestamp)}
        </span>
        
        {/* Level */}
        <span className={clsx(
          'px-1.5 py-0.5 rounded text-[10px] font-medium whitespace-nowrap',
          getLevelColor(log.level)
        )}>
          {log.level}
        </span>
        
        {/* User ID */}
        {log.user_id && log.user_id > 0 && (
          <span className="text-purple-400 whitespace-nowrap">
            u:{log.user_id}
          </span>
        )}
        
        {/* Module */}
        <span className="text-cyan-400 whitespace-nowrap">
          {log.module.split('.').pop()}:{log.line}
        </span>
        
        {/* Message */}
        <span className="text-gray-300 break-all flex-1">
          {log.message}
        </span>
      </div>
      
      {/* Expanded Details */}
      {isExpanded && (
        <div className="mt-2 ml-4 pl-4 border-l-2 border-gray-700 text-gray-400 space-y-1">
          <p>Module: {log.module}</p>
          <p>Function: {log.function}</p>
          {log.request_id && log.request_id !== '-' && (
            <p>Request ID: {log.request_id}</p>
          )}
          {log.exception && (
            <pre className="mt-2 p-2 bg-red-900/30 rounded text-red-300 whitespace-pre-wrap">
              {log.exception}
            </pre>
          )}
        </div>
      )}
    </div>
  );
};
