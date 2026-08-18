# CV structure (stable skeleton)

All corpus resumes share one skeleton. Tailoring changes *content lenses*, not layout.

## Sections (fixed order)

1. **Header** — name + city + phone + email + LinkedIn  
2. **Summary / Resumo** — 2–4 sentences, angle-first  
3. **Core skills / Competências** — 4–5 bold buckets, tools inside  
4. **Professional experience** — reverse chrono; 1–4 bullets per role  
5. **Projects** (optional but strong) — 1–2 angle-aligned proofs  
6. **Education & additional** — degrees, langs, certs, optional availability  

## Layout constants (from `resume.cls`)

- One page preference  
- Tight geometry (~0.32–0.4in margins)  
- Compact itemize (`itemsep=0`)  
- Section = title + rule  
- `\small` body  

## Language packs

| Locale | Summary | Skills | Experience | Projects | Education |
|--------|---------|--------|------------|----------|-----------|
| `en` | SUMMARY | CORE SKILLS | PROFESSIONAL EXPERIENCE | PROJECTS | EDUCATION & ADDITIONAL |
| `pt` | RESUMO | COMPETÊNCIAS | EXPERIÊNCIA PROFISSIONAL | PROJETOS | FORMAÇÃO & INFORMAÇÕES ADICIONAIS |

## Bullet budget (keeps one page)

| Role recency | Typical bullets |
|--------------|-----------------|
| Current | 2–4 |
| Previous | 1–3 |
| Older / less relevant to angle | 1–2 or omit soft detail |

## What changes per angle (only)

| Field | Changes? |
|-------|----------|
| Name / contact / employers / dates | No |
| Summary | Yes |
| Skill bucket labels + contents | Yes |
| Role subtitle / parenthetical | Soft yes |
| Bullet selection & wording | Yes (from tagged variants) |
| Which projects surface | Yes |
| Availability line | Contextual |
