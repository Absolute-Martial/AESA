/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone',
  
  // Ignore ESLint errors during build (already checked in CI)
  eslint: {
    ignoreDuringBuilds: true,
  },
  
  // Ignore TypeScript errors during build (already checked in CI)
  typescript: {
    ignoreBuildErrors: true,
  },
  
  // API rewrites to backend
  async rewrites() {
    const backendUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
    
    return [
      {
        source: '/api/:path*',
        destination: `${backendUrl}/api/:path*`,
      },
      {
        source: '/graphql',
        destination: `${backendUrl}/graphql`,
      },
      {
        source: '/health',
        destination: `${backendUrl}/health`,
      },
      {
        source: '/ws/:path*',
        destination: `${backendUrl}/ws/:path*`,
      },
    ];
  },
};

module.exports = nextConfig;
