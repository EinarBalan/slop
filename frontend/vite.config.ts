import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Proxy API requests to Flask backend on port 3000
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5174,
    proxy: {
      '/feed': 'http://127.0.0.1:3000',
      '/reset': 'http://127.0.0.1:3000',
      '/generate': 'http://127.0.0.1:3000',
      '/interactions': 'http://127.0.0.1:3000'
    }
  }
})


