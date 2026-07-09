import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 1111,
    proxy: {
      '/api': {
        target: 'http://localhost:2222',
        changeOrigin: true,
      },
    },
  },
})
