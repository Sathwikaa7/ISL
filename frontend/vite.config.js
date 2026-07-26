import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Vite config for the ISL Real-Time Recognition frontend.
// The dev server proxies /api and /socket.io to the Flask backend so you
// don't hit CORS issues while developing. Adjust the target if your Flask
// server runs on a different host/port.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:5000',
        changeOrigin: true
      },
      '/socket.io': {
        target: 'http://localhost:5000',
        changeOrigin: true,
        ws: true
      }
    }
  }
})
