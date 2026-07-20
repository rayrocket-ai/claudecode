import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import type { GrowthData } from '../../types';
import { getPlatformColor, getPlatformName } from '../../utils/platformColors';
import { formatNumber, formatShortDate } from '../../utils/formatters';

interface Props {
  data: GrowthData | null;
}

export default function FollowerGrowthChart({ data }: Props) {
  if (!data || data.platforms.length === 0) {
    return <div className="h-80 flex items-center justify-center text-gray-400">No data available</div>;
  }

  // Merge all platforms into unified date-keyed records
  const dateMap: Record<string, Record<string, number>> = {};
  for (const platform of data.platforms) {
    for (const point of platform.data) {
      if (!dateMap[point.date]) dateMap[point.date] = {};
      dateMap[point.date][platform.platform] = point.followers;
    }
  }

  const chartData = Object.entries(dateMap)
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([date, vals]) => ({ date, ...vals }));

  return (
    <ResponsiveContainer width="100%" height={350}>
      <LineChart data={chartData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
        <XAxis
          dataKey="date"
          tickFormatter={formatShortDate}
          tick={{ fontSize: 12, fill: '#94a3b8' }}
          interval="preserveStartEnd"
        />
        <YAxis
          tickFormatter={formatNumber}
          tick={{ fontSize: 12, fill: '#94a3b8' }}
          width={60}
        />
        <Tooltip
          formatter={(value: number, name: string) => [formatNumber(value), getPlatformName(name)]}
          labelFormatter={formatShortDate}
          contentStyle={{ borderRadius: '8px', border: '1px solid #e2e8f0', fontSize: 13 }}
        />
        <Legend
          formatter={(value: string) => getPlatformName(value)}
          wrapperStyle={{ fontSize: 13 }}
        />
        {data.platforms.map((p) => (
          <Line
            key={p.platform}
            type="monotone"
            dataKey={p.platform}
            stroke={getPlatformColor(p.platform)}
            strokeWidth={2.5}
            dot={false}
            activeDot={{ r: 4 }}
          />
        ))}
      </LineChart>
    </ResponsiveContainer>
  );
}
