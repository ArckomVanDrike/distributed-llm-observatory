export type AppRoute =
  | 'observatory'
  | 'consumer-probe'
  | 'agent-lab'
  | 'agent-lab-test'
  | 'agent-lab-starter'

const ROUTES: Record<string, AppRoute> = {
  '#/observatory': 'observatory',
  '#/consumer-probe': 'consumer-probe',
  '#/agent-lab': 'agent-lab',
  '#/agent-lab/test': 'agent-lab-test',
  '#/agent-lab/starter': 'agent-lab-starter',
}

export function resolveAppRoute(
  hash: string,
): AppRoute {
  return ROUTES[hash] ?? 'observatory'
}
