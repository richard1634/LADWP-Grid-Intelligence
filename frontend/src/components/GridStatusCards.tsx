import { Zap, TrendingUp, AlertTriangle, Clock } from 'lucide-react';
import { motion } from 'framer-motion';
import { MetricCard } from './ui/MetricCard';
import { Badge } from './ui/Badge';
import { LoadingCard } from './ui/Loading';
import type { GridStatus } from '../types';
import { formatNumber, formatCurrency, formatTime } from '../lib/utils';

interface GridStatusCardsProps {
  data: GridStatus | undefined;
  isLoading: boolean;
}

const stressConfig = {
  Normal: { color: 'bg-green-500', emoji: '🟢', variant: 'success' as const },
  Moderate: { color: 'bg-yellow-500', emoji: '🟡', variant: 'warning' as const },
  High: { color: 'bg-orange-500', emoji: '🟠', variant: 'warning' as const },
  Critical: { color: 'bg-red-500', emoji: '🔴', variant: 'error' as const },
};

export function GridStatusCards({ data, isLoading }: GridStatusCardsProps) {
  if (isLoading || !data) {
    return (
      <section className="space-y-4 sm:space-y-6">
        <h2 className="text-lg sm:text-xl md:text-2xl font-bold text-ladwp-blue">📊 Current Grid Status</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-6">
          {[...Array(4)].map((_, i) => (
            <LoadingCard key={i} />
          ))}
        </div>
      </section>
    );
  }

  const config = stressConfig[data.stress.level];

  return (
    <section className="space-y-6">
      <h2 className="text-2xl font-bold text-ladwp-blue">📊 Current Grid Status</h2>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-6">
        <MetricCard
          icon={Zap}
          label="System Demand"
          value={`${formatNumber(data.demand_mw)} MW`}
          trend={typeof data.demand_trend === 'number' ? data.demand_trend : 0}
          color="blue"
        />

        <MetricCard
          icon={TrendingUp}
          label="Avg. Energy Price"
          value={`${formatCurrency(data.avg_price_per_mwh)}/MWh`}
          delta={data.price_delta}
          deltaLabel="vs typical"
          color="emerald"
        />

        <MetricCard
          icon={AlertTriangle}
          label="Grid Stress Level"
          value={
            <span className="flex items-center gap-2">
              {config.emoji}
              {data.stress.level}
            </span>
          }
          badge={
            data.stress.factors.length > 0 ? (
              <Badge variant={config.variant}>
                {data.stress.factors.join(', ')}
              </Badge>
            ) : (
              <Badge variant="success">None</Badge>
            )
          }
          color={data.stress.level === 'Critical' ? 'red' : data.stress.level === 'High' ? 'orange' : 'slate'}
        />

        <MetricCard
          icon={Clock}
          label="Last Updated"
          value={formatTime(data.timestamp)}
          subtext="Pacific Time"
          color="slate"
        />
      </div>

      {/* Alert Banner */}
      {(data.stress.level === 'High' || data.stress.level === 'Critical') && (
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className={`p-4 rounded-lg border-l-4 ${
            data.stress.level === 'Critical'
              ? 'bg-red-50 border-red-500'
              : 'bg-orange-50 border-orange-500'
          }`}
        >
          <h3 className="font-bold text-lg flex items-center gap-2">
            ⚠️ GRID ALERT: {data.stress.level} Stress Detected
          </h3>
          <p className="mt-1">
            <strong>Factors:</strong> {data.stress.factors.join(', ')}
          </p>
          <p className="mt-2 text-sm">
            <strong>Recommended Action:</strong> Monitor operations closely, consider demand response
          </p>
        </motion.div>
      )}

      {data.stress.level === 'Normal' && (
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="p-4 rounded-lg border-l-4 bg-green-50 border-green-500"
        >
          <h3 className="font-bold text-lg flex items-center gap-2">
            ✅ Grid Operating Normally
          </h3>
          <p className="mt-1 text-sm">
            All systems operating within normal parameters. No immediate action required.
          </p>
        </motion.div>
      )}
    </section>
  );
}
