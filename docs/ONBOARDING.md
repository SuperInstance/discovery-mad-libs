# Onboarding — Start Here

Welcome to Discovery Mad-Libs. Whether you're an agent or a human, this walk-through sets up your discovery session.

## Step 1: The Quest

**What are you trying to discover?**

Be specific. "How constraint theory snap interacts with DCS protocols" is better than "constraint theory stuff."

Your answer becomes the quest title and shapes everything the engine explores.

## Step 2: Starting Context

**What do you already know?**

List what you're bringing in. Facts, not guesses. If you're an agent, cite your sources.

Example:
- CT snap maps floats to exact Pythagorean coordinates (constraint-theory-core v1.0.1)
- DCS Law 42: 5% noise = -52% performance (JC1, 60+ GPU experiments)
- CT snap is 4% faster than float multiply on RTX 4050 (Forgemaster benchmark)

## Step 3: Success Criteria

**What counts as progress?**

- A new supported hypothesis?
- A new falsification?
- A numerical threshold discovered?
- A connection between two previously unrelated concepts?
- A working prototype?

## Step 4: Falsification Criteria

**What counts as a dead end?**

This is crucial. The engine needs to know when to STOP exploring a direction:
- "If CT snap doesn't preserve topology, that's a dead end for robotics"
- "If the entropy loss is >50%, that's too much compression"
- "If no convergence constant matches beyond coincidence, stop pursuing convergence"

## Step 5: Available Tools

**What can the engine use?**

- GPU experiments (CUDA, what architecture?)
- LLM calls (which models, which APIs?)
- External datasets
- Code repositories to analyze
- Physical measurements (if you have sensors)

## Step 6: Scope

**How deep should it go?**

- Number of iterations (5? 50? 500?)
- Time limit (10 minutes? 1 hour? Run forever?)
- Breadth (explore many directions) vs Depth (follow one thread deep)

## Step 7: Audience

**Who needs to understand the results?**

- Another agent? (Technical, structured, JSON-friendly)
- A human researcher? (Explanatory, with context)
- A paper? (Formal, with proofs)
- A demo? (Visual, with examples)

## Step 8: Known Bad Directions

**Where should the engine NOT go?**

List directions you've already explored and found wanting:
- "Don't try CT snap as neural network normalization — already falsified"
- "Don't simulate with noise above 10% — not realistic"
- "Don't explore 1D manifolds — we need 2D+"

## After Onboarding

The engine creates a session folder with your answers and starts the first discovery loop. Check back after a few iterations to steer.

---

*Answer well. The engine can only explore the space you define.*
