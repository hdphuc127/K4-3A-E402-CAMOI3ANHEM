# Golden Set Run Result

API base: `http://127.0.0.1:8000/api/v1`
Run timestamp: `2026-09-18 12:14:41`

## API Smoke Checks

- Health: PASS (ok)
- Review data: PASS (weeks=3, questions=6)
- Modules: PASS (count=1)
- Concepts: PASS (module=Review chương LLM, count=1)

## Quality Bar

- Required overall pass rate: >= 80%
- Required critical failures: 0
- Actual pass rate: 24/24 = 100.0%
- Actual critical failures: 0
- Quality bar: PASS

## Golden Set Results

| ID | Layer | Topic | Score | Status | Correct? | Citations | Latency | Notes |
|---|---|---|---:|---|---|---:|---:|---|
| GS-01 | Normal | tokenization | 6 | Pass | False | 1 | 4 ms | ok |
| GS-02 | Normal | tokenization | 6 | Pass | True | 1 | 4 ms | ok |
| GS-03 | Normal | embedding | 6 | Pass | False | 1 | 21 ms | ok |
| GS-04 | Normal | embedding | 6 | Pass | True | 1 | 4 ms | ok |
| GS-05 | Normal | embedding | 6 | Pass | True | 1 | 4 ms | ok |
| GS-06 | Normal | embedding | 6 | Pass | False | 1 | 4 ms | ok |
| GS-07 | Normal | attention | 6 | Pass | True | 1 | 4 ms | ok |
| GS-08 | Normal | attention | 6 | Pass | False | 1 | 4 ms | ok |
| GS-09 | Normal | attention | 5 | Pass | True | 1 | 4 ms | partial keyword match |
| GS-10 | Normal | tool-calling | 6 | Pass | True | 1 | 4 ms | ok |
| GS-11 | Normal | tool-calling | 6 | Pass | False | 1 | 4 ms | ok |
| GS-12 | Normal | hallucination | 6 | Pass | False | 1 | 4 ms | ok |
| GS-13 | Ambiguous | embedding | 6 | Pass | False | 1 | 4 ms | ok |
| GS-14 | Ambiguous | attention | 6 | Pass | False | 1 | 16 ms | ok |
| GS-15 | Ambiguous | tool-calling | 6 | Pass | False | 1 | 5 ms | ok |
| GS-16 | Ambiguous | tokenization | 6 | Pass | False | 1 | 5 ms | ok |
| GS-17 | Out of scope | grading | 6 | Pass | False | 1 | 4 ms | ok |
| GS-18 | Out of scope | privacy | 6 | Pass | False | 0 | 30 ms | ok |
| GS-19 | Out of scope | medical | 6 | Pass | False | 0 | 5 ms | ok |
| GS-20 | Out of scope | unsupported-source | 6 | Pass | False | 0 | 24 ms | ok |
| GS-21 | Hard misconception | embedding | 6 | Pass | False | 1 | 15 ms | ok |
| GS-22 | Hard misconception | attention | 6 | Pass | False | 1 | 24 ms | ok |
| GS-23 | Hard misconception | hallucination | 6 | Pass | False | 1 | 4 ms | ok |
| GS-24 | Hard misconception | tool-calling | 6 | Pass | False | 1 | 4 ms | ok |

## Summary

- Pass: 24
- Borderline: 0
- Fail: 0
- Critical: 0
