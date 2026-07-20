import { useState, useEffect } from 'react';
import TopBar from '../components/layout/TopBar';
import FollowerGrowthChart from '../components/charts/FollowerGrowthChart';
import EngagementPieChart from '../components/charts/EngagementPieChart';
import { getOverview, getGrowth, getEngagement } from '../api/analytics';
import { getPlatformColor, getPlatformName } from '../utils/platformColors';
import { formatNumber } from '../utils/formatters';
import type { OverviewData, GrowthData, EngagementData } from '../types';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';

export default function AnalyticsPage() {
  const [overview, setOverview] = useState<OverviewData | null>(null);
  const [growth, setGrowth] = useState<GrowthData | null>(null);
  const [engagement, setEngagement] = useState<EngagementData | null>(null);
  const [days, setDays] = useState(90);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      getOverview(),
      getGrowth({ days }),
      getEngagement({ days }),
    ])
      .then(([o, g, e]) => {
        setOverview(o);
        setGrowth(g);
        setEngagement(e);
      })
      .finally(() => setLoading(false));
  }, [days]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
      </div>
    );
  }

  // Build engagement chart data
  const engagementDateMap: Record<string, Record<string, number>> = {};
  if (engagement) {
    for (const platform of engagement.platforms) {
      for (const point of platform.data) {
        if (!engagementDateMap[point.date]) engagementDateMap[point.date] = {};
        engagementDateMap[point.date][platform.platform] = point.rate;
      }
    }
  }
  const engagementChartData = Object.entries(engagementDateMap)
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([date, vals]) => ({ date, ...vals }));

  return (
    <div>
      <TopBar title="Analytics" subtitle="Deep dive into your social media performance" />

      {/* Period Selector */}
      <div className="flex gap-2 mb-6">
        {[30, 60, 90, 180].map((d) => (
          <button
            key={d}
            onClick={() => setDays(d)}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              days === d
                ? 'bg-blue-600 text-white'
                : 'bg-white text-gray-600 border border-gray-200 hover:bg-gray-50'
            }`}
          >
            {d === 30 ? '30 Days' : d === 60 ? '60 Days' : d === 90 ? '90 Days' : '6 Months'}
          </button>
        ))}
      </div>

      {/* Platform Summary Cards */}
      <div className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-5 gap-4 mb-8">
        {overview?.platforms.map((p) => (
          <div
            key={p.platform}
            className="bg-white rounded-xl p-5 shadow-sm border border-gray-100"
          >
            <div className="flex items-center gap-2 mb-3">
              <div
                className="w-8 h-8 rounded-lg flex items-center justify-center text-white text-sm font-bold"
                style={{ backgroundColor: getPlatformColor(p.platform) }}
              >
                {getPlatformName(p.platform).charAt(0)}
              </div>
              <span className="text-sm font-medium text-gray-700">{getPlatformName(p.platform)}</span>
            </div>
            <p className="text-2xl font-bold text-gray-900">{formatNumber(p.followers)}</p>
            <p className={`text-sm mt-1 font-medium ${p.change_percent >= 0 ? 'text-emerald-500' : 'text-red-500'}`}>
              {p.change_percent >= 0 ? '+' : ''}{p.change_percent}%
            </p>
          </div>
        ))}
      </div>

      {/* Follower Growth */}
      <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100 mb-8">
        <h2 className="text-lg font-semibold text-gray-900 mb-1">Follower Growth Trends</h2>
        <p className="text-sm text-gray-500 mb-6">How your audience is growing over time</p>
        <FollowerGrowthChart data={growth} />
      </div>

      {/* Engagement Rate + Pie */}
      <div className="grid grid-cols-1 xl:grid-cols-2 gap-8">
        <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
          <h2 className="text-lg font-semibold text-gray-900 mb-1">Engagement Rate Over Time</h2>
          <p className="text-sm text-gray-500 mb-6">Average engagement by platform</p>
          {engagementChartData.length > 0 ? (
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={engagementChartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis dataKey="date" tick={{ fontSize: 11, fill: '#94a3b8' }} />
                <YAxis tick={{ fontSize: 12, fill: '#94a3b8' }} />
                <Tooltip contentStyle={{ borderRadius: '8px', border: '1px solid #e2e8f0', fontSize: 13 }} />
                <Legend formatter={(v: string) => getPlatformName(v)} wrapperStyle={{ fontSize: 13 }} />
                {engagement?.platforms.map((p) => (
                  <Line
                    key={p.platform}
                    type="monotone"
                    dataKey={p.platform}
                    stroke={getPlatformColor(p.platform)}
                    strokeWidth={2}
                    dot={false}
                  />
                ))}
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-64 flex items-center justify-center text-gray-400">No data</div>
          )}
        </div>

        <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
          <h2 className="text-lg font-semibold text-gray-900 mb-1">Audience Distribution</h2>
          <p className="text-sm text-gray-500 mb-6">Followers across platforms</p>
          <EngagementPieChart platforms={overview?.platforms ?? []} />
        </div>
      </div>
    </div>
  );
}
