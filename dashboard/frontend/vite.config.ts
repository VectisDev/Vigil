import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  // EN: Inject build version at compile time for deploy verification.
  // ES: Inyectar versión de build en tiempo de compilación para verificar deploys.
  define: {
    __BUILD_VERSION__: JSON.stringify(
      process.env.VITE_BUILD_VERSION || new Date().toISOString()
    ),
  },
})
