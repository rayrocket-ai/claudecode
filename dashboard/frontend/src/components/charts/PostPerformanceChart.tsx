import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import type { PostMetric } from '../../types';
import { formatNumber } from '../../utils/formatters';

interface Props {
  posts: PostMetric[];
}

export default function PostPerformanceChart({ posts }: Props) {
  if (posts.length === 0) {
    return <div className="h-64 flex items-center justify-center text-gray-400">No data available</div>;
  }

  // Show top 10 posts by views
  const topPosts = [...posts]
    .sort((a, b) => b.views - a.views)
    .slice(0, 10)
    .map((p) => ({
      name: (p.post_title ?? 'Untitled').substring(0, 25) + ((p.post_title?.length ?? 0) > 25 ? '...' : ''),
      views: p.views,
      likes: p.likes,
      comments: p.comments,
    }));

  return (
    <ResponsiveContainer width="100%" height={300}>
      <BarChart data={topPosts} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
        <XAxis dataKey="name" tick={{ fontSize: 11, fill: '#94a3b8' }} angle={-20} textAnchor="end" height={60} />
        <YAxis tickFormatter={formatNumber} tick={{ fontSize: 12, fill: '#94a3b8' }} />
        <Tooltip
          formatter={(value: number) => formatNumber(value)}
          contentStyle={{ borderRadius: '8px', border: '1px solid #e2e8f0', fontSize: 13 }}
        />
        <Legend wrapperStyle={{ fontSize: 13 }} />
        <Bar dataKey="views" fill="#3B82F6" radius={[4, 4, 0, 0]} />
        <Bar dataKey="likes" fill="#8B5CF6" radius={[4, 4, 0, 0]} />
        <Bar dataKey="comments" fill="#EC4899" radius={[4, 4, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}
