import {
  fileURLToPath,
} from 'node:url'

import {
  defineConfig,
} from 'vite'

const webRoot = fileURLToPath(
  new URL('..', import.meta.url),
)

export default defineConfig({
  server: {
    fs: {
      allow: [
        webRoot,
      ],
    },
  },
})
