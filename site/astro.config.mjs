import { defineConfig } from 'astro/config'
import tailwind from '@astrojs/tailwind'

export default defineConfig({
  site: 'https://cibrandocampo.github.io',
  base: '/synology-photos-video-enhancer',
  output: 'static',
  trailingSlash: 'ignore',
  integrations: [tailwind()],
})
