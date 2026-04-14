# Discovery Mad-Libs ⚙️

> A standalone discovery engine for agents and humans. Walk in, answer questions, watch it explore. Rewind if it goes off track. Let it run if it's onto something.

## What Is This?

A structured system for iterative discovery — research, world-building, experimentation, ideation, anything. You (human or agent) define the quest. The engine runs autonomous discovery loops using LLMs and (optionally) GPU experiments. You review the output. If it's good, let it run. If it went wrong, rewind to where it diverged and steer it back.

## Quick Start

### For Agents
```
1. Read docs/ONBOARDING.md
2. Answer the essential questions → creates a session
3. Engine starts generating discoveries
4. Check in. Steer if needed. Let it run if it's good.
```

### For Humans
```
1. Read docs/ONBOARDING.md  
2. Run: python3 engine/discovery.py --interactive
3. Answer questions, pick a template, start exploring
4. Come back anytime to review, rewind, or redirect
```

## Templates (Mad-Libs for Discovery)

Templates are structured prompts that shape the exploration:

| Template | Use For |
|----------|---------|
| `iterative-research` | Scientific research with experiment generation (default) |
| `world-building` | Fiction world construction, lore, geography, cultures |
| `code-exploration` | Discovering patterns in a codebase |
| `problem-decomposition` | Breaking a hard problem into solvable parts |
| `creative-ideation` | Free-form idea generation and connection |
| `falsification-engine` | Rapidly test and kill hypotheses |

### Custom Templates

Any template is a mad-libs JSON file:
```json
{
  "name": "my-template",
  "fields": ["topic", "constraints", "goal"],
  "system_prompt": "You are researching {topic} under these constraints: {constraints}. Goal: {goal}.",
  "discovery_prompt": "Given what we know so far, what should we test next?",
  "evaluation_prompt": "Is this discovery {supported} or {falsified}? What constraint does it add?",
  "output_format": "markdown"
}
```

## Sessions

Each discovery session is timestamped:

```
sessions/
  2026-04-14_135800_convergence-research/
    SESSION.md          ← The quest definition
    discoveries/
      001-density-test.md
      002-topology-check.md
      003-entropy-comparison.md
      ...
    BRANCHPOINTS.md     ← Where you can rewind to
    STATUS.md           ← Current state: running/paused/off-track
```

### Rewinding

Read the discoveries in order. Find where it went wrong? That's a branch point. The engine creates a new branch from there:

```python
python3 engine/discovery.py --rewind-to 003 --redirect "You assumed X but actually Y"
```

The engine keeps the old branch (it might have useful bits) and starts fresh from the branch point with your correction.

## Architecture

```
┌──────────────┐
│  ONBOARDING  │ ← Essential questions define the quest
└──────┬───────┘
       │
┌──────▼───────┐
│   TEMPLATE   │ ← Mad-libs shapes the exploration style
└──────┬───────┘
       │
┌──────▼───────┐
│   ENGINE     │ ← LLM generates, GPU verifies, LLM evaluates
│  (loop)      │
└──────┬───────┘
       │
┌──────▼───────┐
│ DISCOVERIES  │ ← Timestamped, readable, rewindable
└──────┬───────┘
       │
┌──────▼───────┐
│   REVIEWER   │ ← You (agent or human) steer the direction
└──────────────┘
```

## The Essential Questions

Every discovery session starts with these. Answer them well and the engine explores the right space:

1. **What are you trying to discover?** (The quest)
2. **What do you already know?** (Starting context)
3. **What counts as progress?** (Success criteria)
4. **What counts as a dead end?** (Falsification criteria)
5. **What tools do you have?** (GPU, APIs, datasets, etc.)
6. **What's the scope?** (Time limit, depth limit, breadth limit)
7. **Who's the audience?** (Who needs to understand the discoveries)
8. **What should the engine avoid?** (Known bad directions)

## Status: Active Development

Built by Forgemaster ⚒️ for the Cocapn fleet. Designed to work with:
- Constraint theory research
- JC1's DCS experiments
- Any discovery task an agent or human brings

---

*The mad-libs engine: fill in the blanks, watch it explore, steer when needed.*
