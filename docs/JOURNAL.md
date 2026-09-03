# Journal rules (after extract)

OCR/text extract stops at fields. `src/journal.py` + `rules/journal_rules.json` map those fields to a **draft 仕訳** (AP journal) for a downstream accounting system.

```
PDF/CSV → extract → draft_fields → journal_rules → journal_draft.lines
                                         ↓
                              evidence_history (source=journal_rule)
```

| Rule | Example |
|---|---|
| Vendor → payee_code | デモ電力 → `V-ELEC` |
| Keyword → 費目 / account | 電気 → `5110 水道光熱費` |
| Site/dept → split | 本社工場 → 施設 70% / 総務 30% |
| Tax-in amount | gross → net + 仮払消費税; credit 未払金 |

Lines always balance (`debit == credit`). Status `skipped` if no `amount_yen` (e.g. activity CSV).

**HITL:** `hitl.original` + `draft_fields` + `journal_draft`. `approval` / `registered` stay null — no auto-post.

Edit `rules/journal_rules.json` only; do not put client names in code.
