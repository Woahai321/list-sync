import { writeFileSync, existsSync, mkdirSync } from 'fs'
import { join } from 'path'

// https://nuxt.com/docs/api/configuration/nuxt-config
export default defineNuxtConfig({
  devtools: { enabled: true },

  // Hooks to generate missing tsconfig files
  hooks: {
    'build:before': () => {
      const nuxtDir = join(process.cwd(), '.nuxt')
      
      // Ensure .nuxt directory exists
      if (!existsSync(nuxtDir)) {
        mkdirSync(nuxtDir, { recursive: true })
      }

      // Create tsconfig.app.json
      const tsconfigApp = {
        extends: './tsconfig.json',
        compilerOptions: {
          composite: true,
          module: 'ESNext',
          moduleResolution: 'Bundler',
          lib: ['ESNext', 'DOM', 'DOM.Iterable'],
        },
      }
      writeFileSync(
        join(nuxtDir, 'tsconfig.app.json'),
        JSON.stringify(tsconfigApp, null, 2)
      )

      // Create tsconfig.node.json
      const tsconfigNode = {
        extends: './tsconfig.json',
        compilerOptions: {
          composite: true,
          module: 'ESNext',
          moduleResolution: 'Bundler',
          types: ['node'],
        },
      }
      writeFileSync(
        join(nuxtDir, 'tsconfig.node.json'),
        JSON.stringify(tsconfigNode, null, 2)
      )

      // Create tsconfig.shared.json
      const tsconfigShared = {
        extends: './tsconfig.json',
        compilerOptions: {
          composite: true,
          module: 'ESNext',
          moduleResolution: 'Bundler',
        },
      }
      writeFileSync(
        join(nuxtDir, 'tsconfig.shared.json'),
        JSON.stringify(tsconfigShared, null, 2)
      )

      console.log('✓ Generated missing tsconfig files in .nuxt/')
    },
  },

  // Modules
  modules: [
    '@pinia/nuxt',
    '@nuxtjs/tailwindcss',
    '@vueuse/nuxt',
    '@nuxtjs/color-mode',
    '@vee-validate/nuxt',
  ],

  // Dev server configuration
  devServer: {
    port: 3222,
    host: 'localhost',
  },

  // Nitro configuration (for API proxy - NO CORS!)
  nitro: {
    // Development proxy
    devProxy: {
      '/api': {
        target: 'http://localhost:4222',
        changeOrigin: true,
      },
    },
    
    // Production server configuration
    experimental: {
      wasm: true,
    },
    
    // Production proxy - works in built app too!
    routeRules: {
      '/api/**': {
        proxy: process.env.NUXT_PUBLIC_API_URL 
          ? `${process.env.NUXT_PUBLIC_API_URL}/api/**`
          : 'http://localhost:4222/api/**',
      },
    },
  },

  // Runtime config (public and private)
  runtimeConfig: {
    // Private keys (only available on server)
    // apiSecret: '',

    // Public keys (exposed to the client)
    public: {
      apiUrl: process.env.NUXT_PUBLIC_API_URL || 'http://localhost:4222',
      apiBase: process.env.NUXT_PUBLIC_API_BASE || '/api',
    },
  },


  // TypeScript configuration
  typescript: {
    strict: false,
    typeCheck: false, // Disabled for Docker compatibility
    shim: false,
  },

  // Auto-imports configuration
  imports: {
    dirs: [
      'composables/**',
      'stores',
      'utils/**',
    ],
  },

  // Component auto-import configuration
  components: [
    {
      path: '~/components',
      pathPrefix: false,
    },
  ],

  // Color mode configuration
  colorMode: {
    preference: 'dark',
    fallback: 'dark',
    classSuffix: '',
  },

  // Tailwind configuration
  tailwindcss: {
    cssPath: '~/assets/css/main.css',
    configPath: 'tailwind.config.js',
    exposeConfig: false,
    viewer: true,
  },

  // App configuration
  app: {
    head: {
      title: 'ListSync',
      titleTemplate: '%s | ListSync',
      meta: [
        { charset: 'utf-8' },
        { name: 'viewport', content: 'width=device-width, initial-scale=1' },
        { name: 'description', content: 'Modern web interface for ListSync - Sync your watchlists with your media server' },
      ],
      link: [
        { rel: 'icon', type: 'image/x-icon', href: '/favicon.ico' },
        // Titillium Web font
        { rel: 'preconnect', href: 'https://fonts.googleapis.com' },
        { rel: 'preconnect', href: 'https://fonts.gstatic.com', crossorigin: 'anonymous' },
        { rel: 'stylesheet', href: 'https://fonts.googleapis.com/css2?family=Titillium+Web:wght@200;300;400;600;700;900&display=swap' },
      ],
    },
  },

  // Vite configuration
  vite: {
    optimizeDeps: {
      include: ['date-fns', 'lucide-vue-next'],
    },
    vue: {
      script: {
        defineModel: true,
        propsDestructure: true,
      },
    },
  },
  
  // Disable vue-tsc checking
  experimental: {
    typedPages: false,
  },
})
