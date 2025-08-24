const nextConfig = {
  // reactStrictMode: true,
  output: 'standalone',
  compiler: {
    removeConsole:
      process.env.NODE_ENV === "production" ? { exclude: ["error"] } : false,
  },
  // Proxy API calls to the backend without exposing the URL in the client
  async rewrites() {
    const API_BASE_URL = process.env.API_BASE_URL || 'http://localhost:8000';
    // Use fallback rewrites so Next's own API routes under pages/api take precedence
    return {
      beforeFiles: [],
      afterFiles: [],
      fallback: [
        {
          source: '/api/:path*',
          destination: `${API_BASE_URL}/:path*`,
        },
      ],
    };
  },
  // Modify the `images` domain list if you need external images
};

export default nextConfig;