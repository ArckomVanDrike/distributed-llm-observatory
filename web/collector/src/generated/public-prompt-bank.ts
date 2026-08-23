// Generated from benchmark/prompts.
// Do not edit manually.

export const PUBLIC_PROMPT_BANK = [
  {
    "promptId": "coding-001",
    "benchmarkVersion": "0.1",
    "category": "coding",
    "promptText": "Write a Python function named deduplicate_preserve_order(values) that returns a new list with duplicate elements removed while preserving the order of first occurrence. Do not modify the input list. Include the function implementation and a brief explanation of its time complexity."
  },
  {
    "promptId": "instruction-following-001",
    "benchmarkVersion": "0.1",
    "category": "instruction_following",
    "promptText": "Respond with exactly three lines. Line 1 must contain only the word ALPHA. Line 2 must contain only the integer 42. Line 3 must contain only the lowercase word omega. Do not add punctuation, markdown, explanations, or blank lines."
  },
  {
    "promptId": "knowledge-001",
    "benchmarkVersion": "0.1",
    "category": "knowledge",
    "promptText": "Explain the difference between RAM and persistent storage in a computer. Your answer should mention volatility, typical purpose, and what normally happens to stored information when power is removed."
  },
  {
    "promptId": "mathematics-001",
    "benchmarkVersion": "0.1",
    "category": "mathematics",
    "promptText": "Solve for x: 3(x - 4) + 2 = 2x + 7. Show the algebraic steps and give the final value of x."
  },
  {
    "promptId": "reasoning-001",
    "benchmarkVersion": "0.1",
    "category": "reasoning",
    "promptText": "A farmer has 17 sheep. All but 9 run away. How many sheep remain?"
  },
  {
    "promptId": "technical-001",
    "benchmarkVersion": "0.1",
    "category": "technical",
    "promptText": "A web client can resolve a server's DNS name and successfully establish a TCP connection to port 443, but the TLS handshake fails immediately because the server certificate is expired. Explain which networking stages have already succeeded, which stage is failing, and why replacing DNS records would not normally fix this specific problem."
  },
  {
    "promptId": "writing-001",
    "benchmarkVersion": "0.1",
    "category": "writing",
    "promptText": "Write a professional email of no more than 120 words informing a project team that a software release has been postponed by two days because final regression testing is not complete. The tone should be calm and factual, state the new release timing, and avoid blaming any person or team."
  }
] as const
