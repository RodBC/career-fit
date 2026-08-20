# User journey — minimum input

> User does little work. Inputs are **URLs**. We scrape. Never invent employers.

## Happy path

```
1. Paste LinkedIn /in/… URL → Continue (no login)
2. Role yes/no
3. Jobs for you — pick a card OR paste one job URL → we scrape
4. Tailor & save → company message → Home
```

**Fresh:** nav **Fresh** or `/?fresh=1`

## Job input rule

- Always a **single job URL** when the user supplies a posting  
- Never ask for title / company / JD as separate fields  
- Public careers / Greenhouse / Lever / guest LinkedIn pages: HTTP scrape (no login)  
- Optional local Chrome session only if public fetch fails  

## Honesty

URL stub profile ≠ full career graph. Optional deepen later — not on Start.
