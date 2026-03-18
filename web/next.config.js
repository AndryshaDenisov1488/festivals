/** @type {import('next').NextConfig} */
const basePath = process.env.NEXT_PUBLIC_BASE_PATH || ''
const nextConfig = {
  output: 'standalone',
  basePath: basePath || undefined,
  assetPrefix: basePath ? `${basePath}/` : undefined
}

module.exports = nextConfig
