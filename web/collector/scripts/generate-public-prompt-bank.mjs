import {
  mkdir,
  readdir,
  readFile,
  writeFile,
} from 'node:fs/promises'
import path from 'node:path'

const collectorRoot = process.cwd()
const promptRoot = path.resolve(
  collectorRoot,
  '../../benchmark/prompts',
)

const outputPath = path.resolve(
  collectorRoot,
  'src/generated/public-prompt-bank.ts',
)

const entries = await readdir(
  promptRoot,
  {
    recursive: true,
    withFileTypes: true,
  },
)

const promptPaths = entries
  .filter(
    (entry) =>
      entry.isFile()
      && entry.name.endsWith('.json'),
  )
  .map((entry) =>
    path.join(
      entry.parentPath ?? entry.path,
      entry.name,
    ),
  )
  .sort()

const prompts = []

for (const promptPath of promptPaths) {
  const raw = await readFile(
    promptPath,
    'utf8',
  )

  const value = JSON.parse(raw)

  if (value.enabled !== true) {
    continue
  }

  for (
    const field of [
      'prompt_id',
      'benchmark_version',
      'category',
      'prompt',
    ]
  ) {
    if (
      typeof value[field] !== 'string'
      || value[field].length === 0
    ) {
      throw new Error(
        `Invalid prompt field ${field}: ${promptPath}`,
      )
    }
  }

  prompts.push({
    promptId: value.prompt_id,
    benchmarkVersion:
      value.benchmark_version,
    category: value.category,
    promptText: value.prompt,
  })
}

prompts.sort(
  (left, right) =>
    left.promptId.localeCompare(right.promptId),
)

await mkdir(
  path.dirname(outputPath),
  {
    recursive: true,
  },
)

const source = `// Generated from benchmark/prompts.
// Do not edit manually.

export const PUBLIC_PROMPT_BANK = ${JSON.stringify(
  prompts,
  null,
  2,
)} as const
`

await writeFile(
  outputPath,
  source,
  'utf8',
)

console.log(
  `Generated ${prompts.length} public prompts.`,
)
