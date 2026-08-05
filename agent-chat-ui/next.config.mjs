/** @type {import('next').NextConfig} */
const nextConfig = {
  // ws (via langsmith/sandbox's exec/streaming path) relies on native
  // bufferutil/utf-8-validate bindings that webpack mis-bundles for server
  // routes — keep it external so Node's own require loads it instead.
  serverExternalPackages: ["ws"],
  experimental: {
    serverActions: {
      bodySizeLimit: "10mb",
    },
  },
};

export default nextConfig;
