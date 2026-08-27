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
    proxy: {
      '/v1/agent-tests': {
        target: 'http://127.0.0.1:8766',
      },
      '/v1/agent-comparisons': {
        target: 'http://127.0.0.1:8766',
      },
      '/v1/agent-observation-pairs': {
        target: 'http://127.0.0.1:8766',
      },
    },
  },
})
