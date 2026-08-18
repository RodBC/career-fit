# Career Fit — Product

**One-liner:** A career operating system — start with high-signal reach-out (tailored CV + decision-maker drafts), then keep advancing the candidate with a tracker and a coach that suggests what to do next.

## Vision

Career Fit is the default workspace for candidates who refuse Easy Apply roulette.

**Day one:** the user dumps everything — deep self-profile **and** current resume. We structure it into a career graph.

**Every day after:** we help them track applications, people they’ve reached, network bridges, and curriculum progress — and we keep suggesting sharp next moves: recruiters to contact, people who can help, LinkedIn post topics, courses, hackathons, projects to build.

At scale this is not “AI resume writer.” It is:

- **Career graph** — skills, preferences, hates, wins, goals, resume facts  
- **Fit + artifact factory** — angled CVs, messages, interview briefs without AI smell  
- **Career CRM** — applied jobs, outreach, replies, network helpers  
- **Growth coach** — continuous suggestions that close gaps and create signal  
- **Friendly product** — guided UI/UX, progressive onboarding, calm home screen (see `docs/ECOSYSTEM.md`)

## Wedge → ecosystem

```
intake (profile + resume)
    → tailor + reach-out          ← wedge / pay proof
    → track applications & people ← retention
    → suggest growth & network    ← daily habit / moat
```

Do not build the full ecosystem before the wedge converts. Full map: [`docs/ECOSYSTEM.md`](ECOSYSTEM.md).

## Why this wins money

| Buyer pain | Our answer | Monetization hook |
|------------|------------|-------------------|
| Applications vanish into ATS void | Reach humans with credible artifacts | Paid seat when outreach volume matters |
| AI CVs sound fake | Playbook fine-tuned on real multi-angle corpus | Quality is the upgrade |
| Finding the right recruiter is tedious | Rank + draft from contacts the user provides (later: assisted capture) | Time saved = subscription |
| “What should I do this week?” | Suggestion engine tied to gaps + active pipeline | Habit → Pro retention |
| Lost track of who I messaged | Career CRM (jobs, recruiters, network) | Switching cost |
| Interview panic | Tutoring briefs mapped to role + interviewer | Upsell pack |

## Tiers (draft)

### Free — Prove it

- 1 profile + resume intake  
- 3 tailored CVs / month  
- Paste-based recruiter drafts  
- Light application list (limited)  

**Purpose:** acquisition; CV quality sells itself.

### Pro — $29/mo (working price; was $19–39 band)

- Unlimited tailor  
- Full career CRM (applications, outreach, network notes)  
- Suggestion engine (courses, posts, projects, people, hackathons)  
- Job paste normalizers  
- Interview prep generator  

### Team / Coach — higher

- Multi-profile (career coaches, bootcamps)  
- Shared pipelines + curriculum paths  
- White-label exports  

## Moat (in priority order)

1. **Angle playbook + anti-AI-smell craft** (already in repo)  
2. Longitudinal outcomes (what angles/suggestions convert)  
3. Career graph + tracker data (personal switching cost)  
4. Network / warm-path suggestions from user-owned exports  
5. Brand trust: we do not burn user accounts with reckless scraping  

Scrapers are **not** the moat.

## Exit criteria for current MVP (Phase A)

- User can upload profile + paste JD → download `.tex` / `.md` + message in <2 minutes  
- User can paste 3 recruiters → get ranked drafts  
- AI agents consistently update `docs/context/` without being reminded twice  

## Next product milestones

| Phase | Milestone | Status |
|-------|-----------|--------|
| A | Guided intake (profile form + resume upload) | ✅ local MVP |
| B | Applications + outreach tracker in UI | ✅ local MVP (Home + localStorage) |
| C | First suggestion cards (gap → course/post/project) | ✅ Today lite (max 3); richer taxonomy later |
| D | Network bridge objects | planned |

## Explicit non-goals (near term)

- Becoming a LinkedIn growth-hacking / auto-post tool  
- Auto-apply or auto-DM bots  
- Competing with LinkedIn Recruiter for enterprise sourcing  
- Boiling the ocean UI before wedge retention exists  
