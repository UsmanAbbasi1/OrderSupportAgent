# VRSP Technical Flow (Sticky Notes Only)

## Sticky Notes

1. User submits issue + tenant/app metadata
2. Client sends `POST /cases` request
3. FastAPI authenticates + validates schema
4. Request normalized into `CaseContext`
5. Context loader fetches logs/metrics/ticket history/runbooks
6. Planner agent creates investigation steps
7. Investigator agent runs data tools and gathers evidence
8. Hypothesis agent generates candidate fixes
9. Verifier agent applies candidate in sandbox/mock
10. Validation tests replay scenario and assert outcome
11. Decision: verification passed?
12. Yes path: response agent drafts customer-safe resolution
13. Yes path: include evidence + confidence score
14. Yes path: API returns validated response
15. No path: record failure reason
16. No path: retry with next hypothesis
17. Retry limit reached: escalate to human Tier-2
18. Persist trace and telemetry for audit/observability

## Connections

1 -> 2 -> 3 -> 4 -> 5 -> 6 -> 7 -> 8 -> 9 -> 10 -> 11  
11 (yes) -> 12 -> 13 -> 14  
11 (no) -> 15 -> 16 -> 8  
16 -> 17 (when max retries hit)  
3, 7, 8, 9, 11, 14, 17 -> 18
