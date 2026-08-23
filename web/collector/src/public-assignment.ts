import {
  PUBLIC_PROMPT_BANK,
} from './generated/public-prompt-bank'

import type {
  CollectorProbe,
} from './domain'

type PublicPlatform =
  CollectorProbe['platform']

function hostnameForPlatform(
  platform: PublicPlatform,
): string {
  switch (platform) {
    case 'chatgpt':
      return 'chatgpt.com'
    case 'claude':
      return 'claude.ai'
    case 'gemini':
      return 'gemini.google.com'
  }
}

export function buildPublicAssignment(
  promptId: string,
  platform: PublicPlatform,
): CollectorProbe | null {
  const prompt = PUBLIC_PROMPT_BANK.find(
    (candidate) =>
      candidate.promptId === promptId,
  )

  if (prompt === undefined) {
    return null
  }

  return {
    platform,
    pageHostname:
      hostnameForPlatform(platform),
    benchmarkVersion:
      prompt.benchmarkVersion,
    promptId:
      prompt.promptId,
    promptText:
      prompt.promptText,
    scheduledAtUtc: null,
    measurementMode:
      'consumer-ui-manual-v0.1',
    responseCaptureEnabled: false,
  }
}
