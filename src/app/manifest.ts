import type { MetadataRoute } from 'next';

export default function manifest(): MetadataRoute.Manifest {
  return {
    name: 'Hippo — Your Health Companion',
    short_name: 'Hippo',
    description: 'Track your health, watch explainers, and chat with Hippo AI.',
    start_url: '/',
    display: 'standalone',
    background_color: '#fdf2f7',
    theme_color: '#fab9d1',
    orientation: 'portrait',
    categories: ['health', 'medical', 'lifestyle'],
    icons: [
      { src: '/icons/icon-192.png', sizes: '192x192', type: 'image/png' },
      { src: '/icons/icon-512.png', sizes: '512x512', type: 'image/png' },
      {
        src: '/icons/icon-maskable-512.png',
        sizes: '512x512',
        type: 'image/png',
        purpose: 'maskable',
      },
    ],
  };
}
