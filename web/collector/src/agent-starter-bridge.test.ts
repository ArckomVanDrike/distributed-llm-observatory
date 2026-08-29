import {
  describe,
  expect,
  it,
} from 'vitest'

import {
  fetchAgentStarterQuestions,
  parseAgentStarterQuestionSet,
} from './agent-starter-bridge'

describe('Agent Starter questionnaire bridge', () => {
  it('parses a valid question set', () => {
    const result =
      parseAgentStarterQuestionSet({
        schema_version: '0.1',
        goal: 'coding',
        questions: [
          {
            schema_version: '0.1',
            key: 'offline_required',
            goal: 'coding',
            prompt:
              'Must the agent be able to operate offline?',
            kind: 'boolean',
            reason:
              'Offline operation can exclude remote architectures.',
          },
        ],
      })

    expect(result.goal).toBe('coding')
    expect(result.questions).toHaveLength(1)
    expect(result.questions[0].key).toBe(
      'offline_required',
    )
  })

  it('posts the complete intake to the bridge', async () => {
    let requestUrl = ''
    let requestBody = ''

    const result =
      await fetchAgentStarterQuestions(
        async (
          input,
          init,
        ) => {
          requestUrl = input
          requestBody = init.body

          return {
            ok: true,
            status: 200,
            async json() {
              return {
                schema_version: '0.1',
                goal: 'coding',
                questions: [],
              }
            },
          }
        },
        {
          goal: 'coding',
          evidence: [
            {
              key: 'offline_required',
              source: 'declared',
              value: true,
            },
          ],
          hardware_profile: null,
          execution_environment: null,
        },
      )

    expect(requestUrl).toBe(
      '/v1/agent-starter/questions',
    )

    expect(
      JSON.parse(requestBody),
    ).toEqual({
      goal: 'coding',
      evidence: [
        {
          key: 'offline_required',
          source: 'declared',
          value: true,
        },
      ],
      hardware_profile: null,
      execution_environment: null,
    })

    expect(result.questions).toEqual([])
  })

  it('rejects malformed questionnaire responses', () => {
    expect(() => {
      parseAgentStarterQuestionSet({
        schema_version: '0.1',
        goal: 'coding',
        questions: [
          {
            key: 'offline_required',
          },
        ],
      })
    }).toThrow(
      'Invalid Agent Starter question.',
    )
  })

  it('surfaces HTTP errors', async () => {
    await expect(
      fetchAgentStarterQuestions(
        async () => ({
          ok: false,
          status: 400,
          async json() {
            return {}
          },
        }),
        {
          goal: 'coding',
          evidence: [],
          hardware_profile: null,
          execution_environment: null,
        },
      ),
    ).rejects.toThrow(
      'HTTP 400',
    )
  })
})
