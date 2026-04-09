import { useState, useEffect } from 'react';
import { Users, Eye, FileText, TrendingUp } from 'lucide-react';
import TopBar from '../components/layout/TopBar';
import KPICard from '../components/cards/KPICard';
import FollowerGrowthChart from '../components/charts/FollowerGrowthChart';
import PostPerformanceChart from '../components/charts/PostPerformanceChart';
import EngagementPieChart from '../components/charts/EngagementPieChart';
import PostsTable from '../components/tables/PostsTable';
import { getOverview, getPosts, getGrowth } from '../api/analytics';
import { formatNumber } from '../utils/formatters';
import type { OverviewData, PostMetric, GrowthData } from '../types';

export default function DashboardPage() {
  const [overview, setOverview] = useState<OverviewData | null>(null);
  const [posts, setPosts] = useState<PostMetric[]>([]);
  const [growth, setGrowth] = useState<GrowthData | null>(null);
  const [growthDays, setGrowthDays] = useState(30);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      getOverview(),
      getPosts({ limit: 10, sort_by: 'views' }),
      getGrowth({ days: growthDays }),
    ])
      .then(([overviewData, postsData, growthData]) => {
        setOverview(overviewData);
        setPosts(postsData.posts);
        setGrowth(growthData);
      })
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    getGrowth({ days: growthDays }).then(setGrowth);
  }, [growthDays]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
      </div>
    );
  }

  return (
    <div>
      <TopBar title="Dashboard" subtitle="Overview of your social media performance" />

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-6 mb-8">
        <KPICard
          title="Total Followers"
          value={formatNumber(overview?.total_followers ?? 0)}
          change={overview?.followers_change_percent ?? 0}
          icon={Users}
          color="#3B82F6"
        />
        <KPICard
          title="Total Views"
          value={formatNumber(overview?.total_views ?? 0)}
          change={overview?.views_change_percent ?? 0}
          icon={Eye}
          color="#8B5CF6"
        />
        <KPICard
          title="Total Posts"
          value={String(overview?.total_posts ?? 0)}
          change={0}
          icon={FileText}
          color="#EC4899"
        />
        <KPICard
          title="Avg Engagement"
          value={`${(overview?.engagement_rate ?? 0).toFixed(1)}%`}
          change={overview?.engagement_change_percent ?? 0}
          icon={TrendingUp}
          color="#10B981"
        />
      </div>

      {/* Follower Growth Chart */}
      <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100 mb-8">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h2 className="text-lg font-semibold text-gray-900">Follower Growth</h2>
            <p className="text-sm text-gray-500">Track follower trends across platforms</p>
          </div>
          <div className="flex gap-2">
            {[7, 30, 90, 180].map((d) => (
              <button
                key={d}
                onClick={() => setGrowthDays(d)}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                  growthDays === d
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                }`}
              >
                {d === 7 ? '7D' : d === 30 ? '30D' : d === 90 ? '3M' : '6M'}
              </button>
            ))}
          </div>
        </div>
        <FollowerGrowthChart data={growth} />
      </div>

      {/* Bottom Row: Posts + Pie Chart */}
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-8">
        <div className="xl:col-span-2 bg-white rounded-xl p-6 shadow-sm border border-gray-100">
          <div className="mb-4">
            <h2 className="text-lg font-semibold text-gray-900">Top Performing Posts</h2>
            <p className="text-sm text-gray-500">Your best content by views</p>
          </div>
          <PostPerformanceChart posts={posts} />
        </div>

        <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
          <div className="mb-4">
            <h2 className="text-lg font-semibold text-gray-900">Followers by Platform</h2>
            <p className="text-sm text-gray-500">Distribution across networks</p>
          </div>
          <EngagementPieChart platforms={overview?.platforms ?? []} />
        </div>
      </div>

      {/* Recent Posts Table */}
      <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100 mt-8">
        <div className="mb-4">
          <h2 className="text-lg font-semibold text-gray-900">Recent Posts</h2>
          <p className="text-sm text-gray-500">Latest content across all platforms</p>
        </div>
        <PostsTable posts={posts} compact />
      </div>
    </div>
  );
}
