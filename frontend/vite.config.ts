import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Proxy API requests to Flask backend on port 3000
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5174,
    proxy: {
      '/feed': {
        target: 'http://127.0.0.1:3000',
        changeOrigin: true,
      },
      '/reset': {
        target: 'http://127.0.0.1:3000',
        changeOrigin: true,
      },
      '/generate': {
        target: 'http://127.0.0.1:3000',
        changeOrigin: true,
      },
      '/interactions': {
        target: 'http://127.0.0.1:3000',
        changeOrigin: true,
      },
      '/auth': {
        target: 'http://127.0.0.1:3000',
        changeOrigin: true,
      },
      '/experiments': {
        target: 'http://127.0.0.1:3000',
        changeOrigin: true,
      },
    }
  }
})


