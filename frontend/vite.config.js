import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import vuetify from 'vite-plugin-vuetify'
import path from "path-browserify"

export default defineConfig({
  plugins: [
    vue(),
    vuetify({ autoImport: true }),
  ],
  resolve: {
    alias: {
      "@": "/src",
      path: "path-browserify",
    }
  },
  build: {
    minify: false,
  },
  server: {
    port: 8080,
    open: true
  }
})
