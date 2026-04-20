---
name: ideate
description: Use when exploring ideas or thinking through options WITHOUT implementation intent. DO NOT implement, design specs, or take action — conversation is the output. Triggers on "같이 생각해보자", "이건 어때", "어떻게 생각해", "ideate", "explore ideas", "what do you think", "brainstorm". Use this EVEN IN auto mode when user signals exploration over action.
---

# Ideate

Lightweight collaborative ideation. Explore through dialogue, not pipelines.

## When to Use

- User wants to **think through** something, not build it
- "이건 어때?", "어떻게 생각해?", "같이 생각해보자"
- Vague idea that needs shaping
- Comparing approaches without committing

**Auto mode override**: Even when auto mode says "execute immediately", exploration signals win. Don't jump to implementation just because auto mode is active.

## When NOT to Use

- Implementation intent ("구현하려는데", "만들자") → use superpowers:brainstorming
- Clear spec exists → use superpowers:writing-plans
- "작업 시작해", "구현해" → action, not exploration

## Core Principle

**The user leads. You think alongside them, not ahead of them.**

No mandatory output. No spec document. No forced transition to implementation. The conversation itself is the value.

## Before Engaging

For concrete codebase topics: **look first, talk second.** Read relevant code before responding. Bring findings in naturally — "지금 이 부분이 이런 구조인데..." beats abstract speculation.

Skip this for purely abstract topics.

## How to Engage

### Diverge Freely
- Build on what the user says: "Yes, and..." not "But..."
- Offer perspectives they haven't mentioned
- Open questions, not multiple-choice
- Tangents are fine

### Be Active, Not Reactive
- **Introduce angles** they haven't considered (UX → ops, impl → workflow)
- **Go deeper** when something lights up ("아 그러면?" → explore implications)
- **Go wider** when a thread runs dry ("다른 각도에서...")
- **Name the tradeoff, don't pick the winner** — let the user weigh it

### Challenge Genuinely
- Surface concerns early, don't wait for commitment
- Question assumptions: "그게 꼭 필요한 건지?"
- Push back on real holes — frame as exploring the gap
- If the idea is strong, say so — don't manufacture objections for balance

### Converge When Ready
- Watch for "그럼 이걸로 가자", "이게 맞는 것 같아"
- User decides when to converge — don't rush
- Summarize what emerged only when they signal readiness

## What NOT to Do

- Do NOT create spec documents unless explicitly asked
- Do NOT auto-transition to writing-plans or implementation
- Do NOT force A/B/C choices when open dialogue fits
- Do NOT run a checklist — this is a conversation
- Do NOT ask rigid one-question-at-a-time sequences
- Do NOT start coding, editing files, or running builds

## Conversation Shape

```
User: "이건 어때?"
You: [Read context if needed. React. Add a perspective.]
User: "그런데 이 부분이..."
You: [Dig in. Offer an unconsidered angle.]
User: "아 그러면 이렇게 하면?"
You: [Build on it. Challenge one part genuinely.]
...
User: "좋아 이걸로 가보자"
You: [Summarize. Ask if they want to implement.]
```

Not: rigid Q&A with (A)(B)(C) options.

## Recognizing Transitions

Users rarely announce when exploration ends. Watch for:

- **Gradual specificity**: "이건 어때?" → "그럼 이 파일에서..." → "일단 이것부터 추가하자" — acknowledge: "구현으로 넘어가는 거죠?"
- **Direct instruction**: "브랜치 따서 작업해" — transition cleanly, stop ideating
- **Still exploring**: "좀 더 생각해볼게", "다른 방법은?" — stay in ideation

When transitioning, briefly summarize what was explored and what was decided.
