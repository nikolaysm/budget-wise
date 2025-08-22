/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // Proxy API calls to the backend without exposing the URL in the client
  async rewrites() {
    const API_BASE_URL = process.env.API_BASE_URL || 'http://localhost:8000';
    return [
      {
        source: '/api/:path*',
        destination: `${API_BASE_URL}/:path*`,
      },
    ];
  },
  // Modify the `images` domain list if you need external images
};

module.exports = nextConfig;