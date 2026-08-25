# PROMPT.md — Master Build Prompt for AI IDE

Paste the block below into your AI IDE (Claude Code, Cursor, etc.) as the initial instruction, with `REQUIREMENTS.md`, `ARCHITECTURE.md`, and `AGENT.md` present in the project root.

---

```
You are building a complete project called Cortex, defined by three documents in this
repository's root: REQUIREMENTS.md, ARCHITECTURE.md, and AGENT.md.

Read all three files fully before writing any code. AGENT.md is your primary operating
manual — it defines the build order (Stage 1 through Stage 8), the tech stack, and the
"Definition of Done" checklist. REQUIREMENTS.md defines what must be true of the finished
product. ARCHITECTURE.md defines how the system is structured and why.

Your job is to work through AGENT.md's Stage 1 → Stage 8 build order autonomously,
end to end, without stopping to ask for confirmation between stages, until every item
in AGENT.md section 3 ("Definition of Done") is satisfied.

Follow this loop:

1. Identify the next incomplete stage from AGENT.md §2, in order. Do not skip a stage
   or jump ahead — each stage assumes the previous one is working.
2. Implement that stage fully, following AGENT.md's "Operating Rules" (§0) and the
   relevant ARCHITECTURE.md section for that component.
3. Test what you just built (unit test, standalone script, or integration test as
   appropriate to the stage) before moving on. If something fails, fix it in this
   same loop iteration — do not move to the next stage with known-broken code.
4. Commit your work with a clear message describing the stage completed.
5. Re-read AGENT.md section 3 ("Definition of Done"). Check off (in a running
   PROGRESS.md file you maintain) which criteria are now satisfied.
6. If any Definition of Done criterion is not yet satisfied, return to step 1 and
   continue with the next stage. Do not stop, summarize, or ask "should I continue?"
   — continue automatically.
7. If you hit a genuine blocker (missing credential, ambiguous requirement not
   resolvable from the three documents, an external dependency that cannot be
   installed), log it clearly in DECISIONS.md with what you tried, and make the
   most reasonable assumption to keep moving rather than halting the whole build.
   Only stop entirely if the blocker makes further progress on ALL remaining
   stages impossible (e.g., no way to run any code at all).
8. Treat "the system works with LLM_PROVIDER=ollama and zero API keys configured" as a
   hard requirement, not a nice-to-have — verify it explicitly with a real run, not by
   assumption. Gemini support is verified separately when a key is available.
9. Only stop when ALL of the following are true simultaneously:
   - Every stage in AGENT.md §2 (Stage 1 through Stage 8) is implemented and tested.
   - Every criterion in AGENT.md §3 "Definition of Done" is checked off in PROGRESS.md.
   - `docker-compose up` brings up a working system from a clean checkout.
   - You have written a final summary in PROGRESS.md confirming completion.

Do not produce a partial implementation and declare it "done for now" — the loop only
ends at full Definition of Done completion or a total blocker per step 7. Prefer taking
many small, verified steps over one large unverified one, and treat Gemini and Ollama as
both first-class providers — do not silently build/test against only one of them. When
in doubt about a design choice not covered by the three documents, choose the option most
consistent with ARCHITECTURE.md's stated principle: category and output format must
remain fully decoupled via the canonical Notes JSON.

Begin now with Stage 1.
```

---

## Notes on using this prompt

- This is written for IDEs/agents that support long autonomous tool-use loops (e.g., Claude Code). For chat-only tools without persistent execution, you'll need to re-paste "continue with the next stage per PROGRESS.md" between turns.
- The `PROGRESS.md` and `DECISIONS.md` files it's told to maintain are intentionally *not* pre-written by you — they're the agent's own running log, so you can audit what it did and why at any point without reading the whole diff.
- If the agent stalls or loops without real progress, interrupt and point it back at the specific unchecked item in `PROGRESS.md` — that's usually enough to unstick it.
