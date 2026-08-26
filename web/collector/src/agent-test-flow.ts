import {
  runAgentTest,
} from './agent-test-bridge'

import type {
  AgentTestBridgeResponse,
} from './agent-test-bridge'

import type {
  AgentTestPageState,
} from './agent-test-page'

export interface ExecuteAgentTestOptions {
  baseUrl: string
  fetchImpl: typeof fetch
  runAgentTestImpl?: (
    fetchImpl: typeof fetch,
    baseUrl: string,
  ) => Promise<AgentTestBridgeResponse>
  onStateChange(
    state: AgentTestPageState,
  ): void
}

export async function executeAgentTest(
  options: ExecuteAgentTestOptions,
): Promise<AgentTestBridgeResponse> {
  const run =
    options.runAgentTestImpl ?? runAgentTest

  options.onStateChange('running')

  try {
    const result = await run(
      options.fetchImpl,
      options.baseUrl,
    )

    options.onStateChange('success')

    return result
  } catch (error) {
    options.onStateChange('failed')
    throw error
  }
}
