import { useState, useEffect } from 'react';
import TopBar from '../components/layout/TopBar';
import PostsTable from '../components/tables/PostsTable';
import { getPosts } from '../api/analytics';
import type { PostMetric } from '../types';

const PLATFORMS = ['all', 'facebook', 'instagram', 'twitter', 'youtube', 'tiktok'];
const SORT_OPTIONS = [
  { value: 'published_at', label: 'Newest' },
  { value: 'views', label: 'Most Views' },
  { value: 'likes', label: 'Most Likes' },
  { value: 'engagement_rate', label: 'Highest Engagement' },
];

export default function PostsPage() {
  const [posts, setPosts] = useState<PostMetric[]>([]);
  const [total, setTotal] = useState(0);
  const [platform, setPlatform] = useState('all');
  const [sortBy, setSortBy] = useState('published_at');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    getPosts({
      platform: platform === 'all' ? undefined : platform,
      sort_by: sortBy,
      limit: 100,
    })
      .then((data) => {
        setPosts(data.posts);
        setTotal(data.total);
      })
      .finally(() => setLoading(false));
  }, [platform, sortBy]);

  return (
    <div>
      <TopBar title="Posts Analytics" subtitle={`${total} posts across all platforms`} />

      {/* Filters */}
      <div className="bg-white rounded-xl p-4 shadow-sm border border-gray-100 mb-6">
        <div className="flex flex-wrap gap-4 items-center">
          <div>
            <label className="block text-xs font-medium text-gray-500 mb-1">Platform</label>
            <select
              value={platform}
              onChange={(e) => setPlatform(e.target.value)}
              className="px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {PLATFORMS.map((p) => (
                <option key={p} value={p}>
                  {p === 'all' ? 'All Platforms' : p.charAt(0).toUpperCase() + p.slice(1)}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-xs font-medium text-gray-500 mb-1">Sort By</label>
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
              className="px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {SORT_OPTIONS.map((opt) => (
                <option key={opt.value} value={opt.value}>{opt.label}</option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Posts Table */}
      <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
        {loading ? (
          <div className="flex items-center justify-center py-12">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
          </div>
        ) : (
          <PostsTable posts={posts} />
        )}
      </div>
    </div>
  );
}
