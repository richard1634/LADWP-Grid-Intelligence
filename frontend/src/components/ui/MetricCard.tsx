import { motion } from 'framer-motion';
import { ArrowUp, ArrowDown, type LucideIcon } from 'lucide-react';
import { Card } from './Card';
import { cn } from '../../lib/utils';

interface MetricCardProps {
  icon: LucideIcon;
  label: string;
  value: string | React.ReactNode;
  trend?: number;
  delta?: number;
  deltaLabel?: string;
  badge?: React.ReactNode;
  subtext?: string;
  color?: 'blue' | 'emerald' | 'red' | 'slate' | 'orange';
}

const colorMap = {
  blue: 'text-blue-600 bg-blue-50',
  emerald: 'text-emerald-600 bg-emerald-50',
  red: 'text-red-600 bg-red-50',
  slate: 'text-slate-600 bg-slate-50',
  orange: 'text-orange-600 bg-orange-50',
};

export function MetricCard({
  icon: Icon,
  label,
  value,
  trend,
  delta,
  deltaLabel,
  badge,
  subtext,
  color = 'blue',
}: MetricCardProps) {
  return (
    <Card hover className="relative overflow-hidden">
      <div className="flex items-start justify-between">
        <div className={cn('p-3 rounded-lg', colorMap[color])}>
          <Icon className="w-6 h-6" />
        </div>
        {badge && <div className="ml-2">{badge}</div>}
      </div>

      <div className="mt-4">
        <p className="text-sm font-medium text-gray-600">{label}</p>
        <p className="text-3xl font-bold text-gray-900 mt-2">{value}</p>

        {delta !== undefined && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="flex items-center mt-2 text-sm"
          >
            {delta > 0 ? (
              <ArrowUp className="w-4 h-4 text-red-500 mr-1" />
            ) : delta < 0 ? (
              <ArrowDown className="w-4 h-4 text-green-500 mr-1" />
            ) : null}
            <span className={cn(
              'font-medium',
              delta > 0 ? 'text-red-600' : delta < 0 ? 'text-green-600' : 'text-gray-600'
            )}>
              {delta > 0 ? '+' : ''}{delta.toFixed(2)} {deltaLabel}
            </span>
          </motion.div>
        )}

        {trend !== undefined && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="flex items-center mt-2 text-sm"
          >
            {trend > 0 ? (
              <ArrowUp className="w-4 h-4 text-orange-500 mr-1" />
            ) : trend < 0 ? (
              <ArrowDown className="w-4 h-4 text-blue-500 mr-1" />
            ) : null}
            <span className="text-gray-600 font-medium">
              {typeof trend === 'number' ? (trend > 0 ? 'Increasing' : trend < 0 ? 'Decreasing' : 'Stable') : trend}
            </span>
          </motion.div>
        )}

        {subtext && <p className="text-xs text-gray-500 mt-1">{subtext}</p>}
      </div>
    </Card>
  );
}
