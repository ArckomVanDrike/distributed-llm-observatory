import {
  describe,
  expect,
  it,
} from 'vitest'

import {
  fetchAgentStarterQuestions,
  fetchAgentStarterRecommendation,
  parseAgentStarterQuestionSet,
  parseAgentStarterRecommendation,
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


it('parses a concrete Agent Starter recommendation', () => {
  const result =
    parseAgentStarterRecommendation({
      schema_version: '0.1',
      context: {
        catalog_snapshot: {
          snapshot_id:
            'agent-starter-catalog-v0-2',
        },
      },
      candidate_explanations: [
        {
          assessment: {
            architecture_id:
              'local-coding-agent',
            recommendation:
              'recommended',
          },
          concrete_stack: {
            architecture_id:
              'local-coding-agent',
            components: [
              {
                requirement: {
                  component_type: 'model',
                },
                matched_entries: [
                  {
                    identifier: 'model-a',
                    vendor: 'Vendor',
                    family: 'Family',
                    version: '1',
                  },
                ],
                constrained_entries: [],
                indeterminate_entries: [],
                not_recommended_entries: [],
                constraint_excluded_entries: [],
                selected_entry: {
                  identifier: 'model-a',
                  vendor: 'Vendor',
                  family: 'Family',
                  version: '1',
                },
              },
            ],
          },
          why: [
            'Fits the declared requirements.',
          ],
          why_not: [],
        },
      ],
      recommended_architecture_ids: [
        'local-coding-agent',
      ],
      alternative_architecture_ids: [],
      possible_but_not_recommended_architecture_ids: [],
      not_recommended_architecture_ids: [],
      blockers: [],
      unknown_evidence: [],
    })

  expect(result.catalogSnapshotId).toBe(
    'agent-starter-catalog-v0-2',
  )

  expect(
    result.recommendedArchitectureIds,
  ).toEqual([
    'local-coding-agent',
  ])

  expect(
    result.candidates[0]
      .components[0]
      .selectedEntry
      ?.identifier,
  ).toBe('model-a')
})


it('posts environment evidence to the recommendation endpoint', async () => {
  let requestUrl = ''
  let requestBody = ''

  await fetchAgentStarterRecommendation(
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
            context: {
              catalog_snapshot: {
                snapshot_id:
                  'agent-starter-catalog-v0-2',
              },
            },
            candidate_explanations: [],
            recommended_architecture_ids: [],
            alternative_architecture_ids: [],
            possible_but_not_recommended_architecture_ids: [],
            not_recommended_architecture_ids: [],
            blockers: [],
            unknown_evidence: [],
          }
        },
      }
    },
    {
      goal: 'coding',
      evidence: [],
      hardware_profile: {
        device_class: 'laptop',
        source: 'manual',
        total_memory_bytes:
          8 * 1024 ** 3,
        limitations: [],
      },
      execution_environment: {
        platform: 'linux',
        interface: 'native',
        available_runtimes: [
          'llama.cpp',
        ],
        accelerator_access: 'unknown',
        filesystem_access: 'unknown',
        limitations: [],
      },
    },
  )

  expect(requestUrl).toBe(
    '/v1/agent-starter/recommend',
  )

  const payload =
    JSON.parse(requestBody)

  expect(
    payload.hardware_profile
      .total_memory_bytes,
  ).toBe(8 * 1024 ** 3)

  expect(
    payload.execution_environment
      .available_runtimes,
  ).toEqual([
    'llama.cpp',
  ])
})
