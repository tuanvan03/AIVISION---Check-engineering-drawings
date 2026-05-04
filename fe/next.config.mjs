/** @type {import('next').NextConfig} */
const nextConfig = {
  typescript: {
    ignoreBuildErrors: true,
  },
  images: {
    unoptimized: true,
  },
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: process.env.API_BASE_URL 
          ? `${process.env.API_BASE_URL}/api/:path*` 
          : 'http://127.0.0.1:8000/api/:path*', // Proxy to Backend
      },
    ]
  },
}

export default nextConfig
