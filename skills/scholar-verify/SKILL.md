---
name: scholar-verify
description: Fact-check a finished research report or draft by splitting it into atomic claims, tracing each to primary sources, and recording a verdict in an auditable claims ledger. Use after scholar-research, or on any draft with factual, numerical, legal, scientific, or product claims that must be checked before publishing; not for opinion editing or style review.
---

# Scholar Verify

Run as a separate pass after drafting. The drafter's confidence is not evidence; memory and model recall are not evidence.

## 1. Extract claims

Read the report. Split each checkable sentence into atomic claims (one fact, number, date, attribution, or causal statement each). Skip opinion, recommendation, and clearly labelled inference. Record each claim:

```bash
python3 <skill-dir>/scripts/claims.py add <run>/claims.jsonl \
  --id C1 --claim "<atomic claim>" --location "report.md#executive-answer" --kind number
```

Kinds: `number`, `date`, `attribution`, `causal`, `product`, `legal`, `scientific`, `other`. Prioritise numbers, attributions, and anything the executive answer depends on.

## 2. Trace sources

For each claim, open the cited URL first. Then find the primary source: the original study, filing, official statistics, changelog, court document, or the author's own post. Secondary coverage, answer engines, and aggregators are discovery only. Syndicated copies count as one source.

## 3. Record a verdict

```bash
python3 <skill-dir>/scripts/claims.py verdict <run>/claims.jsonl --id C1 \
  --verdict supported --source <primary-url> --source <second-url> \
  --note "Table 2 reports 41%, report rounds to 40%"
```

| Verdict | Use when |
|---|---|
| `supported` | A primary or authoritative source states it, in context, within the stated time window |
| `partly` | Core is right but number, scope, date, or wording overstates it |
| `unsupported` | No source found after a reasonable search; the claim may still be true |
| `contradicted` | A primary or authoritative source states otherwise |
| `outdated` | It was true, but newer evidence supersedes it |

`supported` needs at least one source; `contradicted` and `partly` need a note that states the correct version.

## 4. Report and fix

```bash
python3 <skill-dir>/scripts/claims.py summary <run>/claims.jsonl > <run>/verification.md
```

The summary exits non-zero while any claim is unchecked, `contradicted`, or `unsupported`. For each such claim, edit the report: correct it, soften it to the evidence, label it as inference, or delete it. Do not change a verdict to make the check pass. Rerun until it exits zero or the user accepts the listed exceptions.
