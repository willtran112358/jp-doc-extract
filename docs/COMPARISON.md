# OCR / extraction options — comparison (Japanese documents)

Context: GHG / activity-data documents (invoices, gas tickets, CSV activity tables, reports).

## Summary

| Option | JP OCR | Field mapping | Cost (≈ / 1k pages) | Best for |
|---|---|---|---|---|
| **This PoC — text layer** | N/A (embedded text) | Regex + CSV columns | **$0** | Digital PDF, fast feasibility |
| **This PoC — PaddleOCR** | ✅ JP | Regex / + VLM | Compute only | Scan PDF, no cloud API |
| **This PoC — VLM (Claude API)** | ✅ (vision) | Regex on extracted text | ~$3–15 API + tokens | Scan, complex layout, blocked Bedrock |
| **Amazon Textract** | ❌ not supported | Forms EN only | ~$1.50 detect | **Not for JP** |
| **Azure Document Intelligence Read** | ✅ JP | + separate LLM | ~$1.50 | Production JP OCR |
| **Bedrock Claude + Textract** | ❌ | Blocked on some accounts | N/A today | Wait for account unblock |

## Accuracy (qualitative)

| Document type | Text-layer PoC | PaddleOCR | VLM | Textract |
|---|---|---|---|---|
| Digital JP invoice PDF | **High** | Overkill | Overkill | Fail |
| Scan invoice | None | Medium–High | **High** | Fail |
| CSV activity table | **Medium** (column map) | N/A | High (if sent as text) | N/A |
| Multi-page report | Low (few fields) | Medium | **High** | Fail |

## When to use this repo in a larger solution

1. **Phase 1 (now):** Prove Draft JSON schema + evidence format on synthetic / digital samples.
2. **Phase 2:** `--mode paddle` on Lambda (colleague track) for scan samples.
3. **Phase 3:** `--mode vlm` or cloud LLM when Bedrock/GCP Sonnet is unblocked.
4. **Production:** Replace inline scripts with API Gateway + worker; SF receives small JSON only.

## Cost example — 10,000 docs/year, 2 pages each

| Stack | OCR | LLM map | Total ≈ / year |
|---|---|---|---|
| Text-layer PoC only | $0 | $0 | **$0** (digital only) |
| Azure Read + Claude API | ~$30 | ~$100–200 | **~$130–230** |
| Textract + Bedrock | N/A for JP | — | **Not viable** |

## References

- [Amazon Textract language limits](https://docs.aws.amazon.com/textract/latest/dg/limits-document.html)
- [Azure Document Intelligence Read](https://learn.microsoft.com/azure/ai-services/document-intelligence/prebuilt/read)
