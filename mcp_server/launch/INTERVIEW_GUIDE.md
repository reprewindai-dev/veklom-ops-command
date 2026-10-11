# Veklom Gate — discovery interview guide

Goal: 15 conversations in two weeks with people who run Docker Compose in production, to decide whether the paid wedge (approval inbox + evidence) is real before building it.

**Pass bar (from `PRODUCT.md`):** 5 people run Veklom Gate against real servers, and 3 agree to pay for the approval inbox (pre-sale or letter of intent). Below that, change the wedge before building the paid tier.

Rules for every call:

- You are learning, not pitching. Talk less than a third of the time.
- Ask about the past, not hypotheticals. "Tell me about the last time…" beats "Would you…".
- Never claim users, logos or reviews we don't have. Say plainly: "No production users yet, no external security review. You'd be early."
- Write notes within 15 minutes of hanging up, using the scoring sheet below.

---

## 1. Who to find

Target mix: **8 agencies/freelancers, 7 small product teams.** Disqualify anyone not running Docker/Compose on servers they control.

| Segment | Signal they fit | Where to find them |
|---|---|---|
| Agencies and freelancers running client Docker hosts | Manage 5+ client servers; hand-rolled Compose deploys; do on-call for clients | r/selfhosted and r/docker posts about multi-client ops; Upwork/Contra profiles listing "Docker, DevOps, maintenance retainers"; local agency directories; Docker community Slack/Discord |
| Small product teams (2–20 engineers) on their own servers | Compose in production on owned or rented boxes; already use Claude Code or Cursor | Show HN commenters on self-hosting threads; GitHub issues on Docker MCP servers (ckreiling/mcp-server-docker, QuantGeekDev/docker-mcp); indie-hacker communities |
| Anyone who has written about an agent breaking infra | Public post-mortem, tweet or issue | Search "agent deleted", "Cursor dropped my database", "Claude Code docker" on X, Reddit, HN |

Outreach message (adapt; keep it short):

> Hi {name}, I saw your {post/comment} about running {Compose/client servers}. I'm building an open-source tool that lets AI agents restart and inspect Docker containers without being able to exec, delete volumes or read secrets. I'm not selling anything yet. Could I ask you 25 minutes of questions about how you handle ops and risky changes today? Happy to share what I learn from the other conversations.

Track every contact in one sheet: name, segment, source, date contacted, date booked, outcome.

---

## 2. Call structure (25 minutes)

### Opening (2 min)

> Thanks for the time. I'm trying to understand how teams like yours run Docker in production and where AI agents fit, if at all. I'll mostly ask questions. There are no right answers, and "we don't do that" is a useful answer. Mind if I take notes?

### Context (4 min)

1. Walk me through your setup. How many hosts, roughly how many containers, Compose or something else?
2. Who gets paged when something breaks at night? What do they usually do first?
3. For agencies: how many clients' servers are you responsible for? Do clients ever ask who did what on their box?

### Agents today (6 min)

4. Do you or your team use Claude Code, Cursor, ChatGPT or another agent near your servers? What do you let it do?
5. What have you deliberately **not** let it do? Why?
6. **Tell me about the last time an agent, script or teammate broke something in production.** What happened, how long did it take to notice, what did it cost?
7. Has an agent ever had access to a credential it shouldn't have? How did you find out?

### Approvals and risk (6 min)

8. **Who approves risky changes today, like stopping a service or touching a database?** How does that approval happen: Slack message, call, nothing?
9. Tell me about the last time you needed someone's approval at an awkward hour. How long did it take?
10. If a client or auditor asked you to prove who restarted a container last Tuesday, what would you show them?

### Money (4 min)

11. **What do you pay today for anything adjacent:** monitoring, uptime, secrets (Infisical, Doppler), access (Teleport, StrongDM), Portainer, on-call (PagerDuty)? Per host, per seat?
12. Who signs off on a new tool at that price? Is there a number below which you just buy?

### Show, then ask (3 min, only after the questions above)

Share the 3-minute demo video or run the live demo. Then:

13. What, if anything, would stop you running this on one real server this week?
14. Which part matters to you most: no destructive routes, signed approvals, autonomous restarts, or the audit trail? Which matters least?

---

## 3. The pre-sale ask

Ask only if they showed real pain (scored 2+ on pain below). Make it concrete and easy to refuse.

**Step 1: run it.**

> Would you put the open-source version on one real server, read-only first, in the next week? I'll help you set it up on a call.

**Step 2: commit to pay (Team or Agency fit).**

> The open-source version already lets you approve from your phone with a self-hosted page; the key never leaves your device. The paid part is that, hosted for you, with push notifications, two-person approval for chosen actions, and audit retention. We're pricing early access at $29 per host a month, or $149 for up to 10 hosts; $399 for agencies up to 50. The hosted version is not built yet. Would you commit to that as an early customer if it ships within {N} weeks, either by pre-paying the first month (refundable if we don't ship) or signing a one-paragraph letter of intent?

Accept these as a "commit": a paid pre-order, a signed LOI naming price and host count, or a purchase order. A verbal "sounds great, let me know" is **not** a commit; score it as interest.

If they decline, ask: "What would have to be true for you to say yes?" Write the answer verbatim.

Letter of intent template (keep it to this length):

> {Company} intends to purchase Veklom Gate {Team/Agency} for approximately {N} hosts at ${price}/month once the approval inbox is generally available, subject to it supporting {their must-have}. This letter is non-binding. Signed, {name, role, date}.

---

## 4. Scoring sheet

Fill one row per conversation within 15 minutes of the call.

| # | Name / company | Segment (A = agency, T = team) | Hosts | Uses agents near prod? (Y/N) | Pain 0–3 | Approval process today | Pays for adjacent tools ($/mo) | Ran it on a real server? (Y/N, date) | Commit to pay? (None / Interest / LOI / Pre-paid) | Must-have they named | Quote worth keeping |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | | | | | | | | | | | |
| 2 | | | | | | | | | | | |
| 3 | | | | | | | | | | | |
| 4 | | | | | | | | | | | |
| 5 | | | | | | | | | | | |
| 6 | | | | | | | | | | | |
| 7 | | | | | | | | | | | |
| 8 | | | | | | | | | | | |
| 9 | | | | | | | | | | | |
| 10 | | | | | | | | | | | |
| 11 | | | | | | | | | | | |
| 12 | | | | | | | | | | | |
| 13 | | | | | | | | | | | |
| 14 | | | | | | | | | | | |
| 15 | | | | | | | | | | | |

**Pain score**

- 0 — No agents near production and no plans to.
- 1 — Uses agents, no incident, mild worry.
- 2 — Has had a near miss or an awkward approval/audit moment in the last 6 months.
- 3 — Lost time, data or a client over it, or is blocked from using agents on servers because of the risk.

**Tally (update after every call)**

| Measure | Count | Bar |
|---|---|---|
| Conversations held | | 15 |
| Ran it against a real server | | **5** |
| Committed to pay (LOI or pre-paid only) | | **3** |
| Agencies with pain ≥ 2 | | — |
| Teams with pain ≥ 2 | | — |

**Decision after 15 conversations**

- **Both bars met:** build the approval inbox; first customers are the committers.
- **Run bar met, pay bar missed:** the open-source core is useful but the paid wedge is wrong. Re-read the "what would have to be true" answers and the must-haves; pick the most repeated one as the next wedge.
- **Run bar missed:** the setup cost or the trust gap is too high. Look at what stopped people (question 13) before writing any more product.

Keep the raw notes. Do not round "interest" up to "commit" in the tally.
