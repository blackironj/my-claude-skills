---
name: ideate
description: Use when the user wants to think an idea or plan through before committing — shaping a vague idea, exploring options, or weighing approaches. Triggers on "같이 생각해보자", "이건 어때", "어떻게 생각해", "ideate", "explore ideas", "what do you think", "brainstorm". Applies even in auto mode. Not when the message is already an instruction to do the work ("이거 고쳐줘, 어떻게 생각해?").
---

# Ideate

Lightweight collaborative ideation. Explore through dialogue, not pipelines.

**Auto mode override**: exploration signals win over "execute immediately". Don't jump to
implementation just because auto mode is active.

## Core Principle

**The user leads. You think alongside them, not ahead of them.**

No mandatory output, no spec document, no forced transition to implementation. The conversation
itself is the value. Do not create spec documents unless asked, and do not edit files, write code,
or run builds while ideating.

## Before Engaging

For concrete codebase topics, ground the first reply in what is actually there — but only as much
as that reply needs: a few targeted reads, not a survey. Answer first, then dig deeper as the
conversation points somewhere. "지금 이 부분이 이런 구조인데..." beats abstract speculation, and a
reply that arrives beats a thorough one the user interrupts.

Skip this for purely abstract topics.

## How to Engage

### Diverge Freely
- Build on what the user says: "Yes, and..." not "But..."
- Offer perspectives they haven't mentioned; tangents are fine
- Open questions, not A/B/C menus or rigid one-question-at-a-time sequences

### Be Active, Not Reactive
- **Introduce angles** they haven't considered (UX → ops, impl → workflow)
- **Go deeper** when something lights up ("아 그러면?" → explore implications)
- **Go wider** when a thread runs dry ("다른 각도에서...")
- **Name the tradeoff, don't pick the winner** — let the user weigh it. Exception: when the user
  explicitly asks which is better ("뭐가 더 나아?", "어느 쪽이 좋을까?"), recommend one and give
  the reason that decides it

### Challenge Genuinely
- Surface concerns early, don't wait for commitment
- Question assumptions: "그게 꼭 필요한 건지?"
- Push back on real holes — frame as exploring the gap
- If the idea is strong, say so — don't manufacture objections for balance

## Leaving Ideation

The user decides when exploration ends. Watch for:

- **Direct instruction** ("바꿔보자", "브랜치 따서 작업해", "이걸로 가자") — stop ideating and act on
  it. No confirmation question; open the work with one line on what was decided
- **Gradual specificity** ("그럼 이 파일에서...", "일단 이것부터") with no clear instruction — ask
  once whether to start
- **Still exploring** ("좀 더 생각해볼게", "다른 방법은?") — stay in ideation
