import type { PostMetric } from '../../types';
import { getPlatformColor, getPlatformName } from '../../utils/platformColors';
import { formatNumber, timeAgo } from '../../utils/formatters';

interface Props {
  posts: PostMetric[];
  compact?: boolean;
}

export default function PostsTable({ posts, compact = false }: Props) {
  if (posts.length === 0) {
    return (
      <div className="text-center py-12 text-gray-400">
        <p className="text-lg">No posts yet</p>
        <p className="text-sm mt-1">Connect your social accounts to see post analytics</p>
      </div>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full">
        <thead>
          <tr className="border-b border-gray-100">
            <th className="text-left py-3 px-4 text-xs font-semibold text-gray-500 uppercase tracking-wider">Post</th>
            <th className="text-left py-3 px-4 text-xs font-semibold text-gray-500 uppercase tracking-wider">Platform</th>
            {!compact && <th className="text-left py-3 px-4 text-xs font-semibold text-gray-500 uppercase tracking-wider">Type</th>}
            <th className="text-right py-3 px-4 text-xs font-semibold text-gray-500 uppercase tracking-wider">Views</th>
            <th className="text-right py-3 px-4 text-xs font-semibold text-gray-500 uppercase tracking-wider">Likes</th>
            <th className="text-right py-3 px-4 text-xs font-semibold text-gray-500 uppercase tracking-wider">Comments</th>
            {!compact && <th className="text-right py-3 px-4 text-xs font-semibold text-gray-500 uppercase tracking-wider">Shares</th>}
            <th className="text-right py-3 px-4 text-xs font-semibold text-gray-500 uppercase tracking-wider">Engagement</th>
            {!compact && <th className="text-right py-3 px-4 text-xs font-semibold text-gray-500 uppercase tracking-wider">Published</th>}
          </tr>
        </thead>
        <tbody>
          {posts.map((post) => (
            <tr key={post.id} className="border-b border-gray-50 hover:bg-gray-50/50 transition-colors">
              <td className="py-3 px-4">
                <p className="text-sm font-medium text-gray-900 truncate max-w-xs">
                  {post.post_title ?? 'Untitled Post'}
                </p>
              </td>
              <td className="py-3 px-4">
                <span
                  className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium text-white"
                  style={{ backgroundColor: getPlatformColor(post.platform) }}
                >
                  {getPlatformName(post.platform)}
                </span>
              </td>
              {!compact && (
                <td className="py-3 px-4">
                  <span className="text-sm text-gray-500 capitalize">{post.post_type}</span>
                </td>
              )}
              <td className="py-3 px-4 text-right text-sm text-gray-700 font-medium">{formatNumber(post.views)}</td>
              <td className="py-3 px-4 text-right text-sm text-gray-700">{formatNumber(post.likes)}</td>
              <td className="py-3 px-4 text-right text-sm text-gray-700">{formatNumber(post.comments)}</td>
              {!compact && <td className="py-3 px-4 text-right text-sm text-gray-700">{formatNumber(post.shares)}</td>}
              <td className="py-3 px-4 text-right">
                <span className="text-sm font-semibold text-blue-600">{post.engagement_rate.toFixed(1)}%</span>
              </td>
              {!compact && <td className="py-3 px-4 text-right text-sm text-gray-500">{timeAgo(post.published_at)}</td>}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
