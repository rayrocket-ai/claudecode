import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend } from 'recharts';
import type { PlatformFollowers } from '../../types';
import { getPlatformColor, getPlatformName } from '../../utils/platformColors';
import { formatNumber } from '../../utils/formatters';

interface Props {
  platforms: PlatformFollowers[];
}

export default function EngagementPieChart({ platforms }: Props) {
  if (platforms.length === 0) {
    return <div className="h-64 flex items-center justify-center text-gray-400">No data available</div>;
  }

  const data = platforms.map((p) => ({
    name: getPlatformName(p.platform),
    value: p.followers,
    platform: p.platform,
  }));

  return (
    <ResponsiveContainer width="100%" height={300}>
      <PieChart>
        <Pie
          data={data}
          cx="50%"
          cy="50%"
          innerRadius={70}
          outerRadius={110}
          dataKey="value"
          nameKey="name"
          paddingAngle={3}
        >
          {data.map((entry) => (
            <Cell key={entry.platform} fill={getPlatformColor(entry.platform)} />
          ))}
        </Pie>
        <Tooltip
          formatter={(value: number) => formatNumber(value)}
          contentStyle={{ borderRadius: '8px', border: '1px solid #e2e8f0', fontSize: 13 }}
        />
        <Legend
          wrapperStyle={{ fontSize: 13 }}
          formatter={(value: string) => <span className="text-gray-600">{value}</span>}
        />
      </PieChart>
    </ResponsiveContainer>
  );
}
