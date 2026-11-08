# Evaluation and operational verification — 9 November 2026

The implementation addresses the hybrid verifier, SQL page-access measurement, API
readiness and concurrent-session gaps. **The planned longer real-provider protocol remains
incomplete because Google returned daily-quota errors.** Local/stub results are not presented
as unlimited Gemini throughput, distributed readiness or a production SLA.

Final runtime: [`bfcca5e`](https://github.com/Shaunakrane914/PortiQ/commit/bfcca5e58f5c4cae1d73e08e0107a37b8856e1e8).
[analysis.json](analysis.json) summarizes each source/version and test scope.

| Check | Evidence | Result |
|---|---|---|
| Full local suite | Python 3.14, GUI/performance extras | 282 passed; opt-in live test skipped |
| Supported minimum Python | Isolated Python 3.11, dev/performance extras | 281 passed; live and optional GUI skipped; mypy passed |
| Fresh supplied CLI generation | [Supplied capture](supplied/supplied.json), source `a3b9b24`, evaluator v4 | 10/10; all ten explicit answer checks; 21 SDK attempts; 48,249 reported tokens |
| Final verifier on historical answers | [Offline replay](historical-replay-final.json), source `bfcca5e` | 50/50 accepted; all 46 corrupted data-answer narratives rejected; zero provider calls |
| Final 60-second HTTP soak | [Summary](http-soak-final-summary.json), eight actors, model capacity four | 1,729 requests: 865 correct accepted answers, 864 controlled 503s; recovery passed |
| Production-profile Docker | [Final checks](production-container-final.json), source `bfcca5e` | All 16 checks passed; zero provider calls |
| Pager-access example | [Measured SQL pair](page-profile-example.json) | Same result; baseline 2 versus wasteful equivalent 29 logical page accesses |
| Corrected live conversation protocol | [Raw capture](live-conversations-final.json), source `f0d64fc` | Four correct accepted answers, two HTTP 429 daily-quota failures; incomplete planned nine-query run |

## What changed in the evaluator

Evaluator v4 checks sector percentages independently from SQL scalars, including percentage
tables and `93% in Technology` phrasing. Wrong/missing/negated prices and wrong exposure
figures still fail. Every required result needs distinct matching analytical tool evidence.
Bound label/value pairs and min/max prose are supported without accepting swapped values or
unlabelled numbers. `Sectors with no securities` is not mistaken for an empty overall result.

The [first extended replay](historical-replay.json) scored 44/50 because six valid formats
were still rejected. They were corrected with adversarial tests; the complete separate
[final replay](historical-replay-final.json) accepts all fifty. These are archived model
answers rescored offline, **not fifty fresh Gemini generations**. The original v2 capture
remains unchanged, with its SHA-256 recorded in each replay.

The fresh supplied run independently generated all ten answers and profiled all eight SQL
references using actual pager counters. It took 153.336 seconds including child-only
6.5-second spacing. Page-access score mean was 100; this differs from the VM-work score and
does not imply optimal SQL. The temporary 603-row database and captured runtime/inputs were
unchanged. After capture, `service.py` gained selected-reference binding and `faithfulness.py`
gained the additional valid formats. All ten captured answers were also reverified offline
on the final source; they are not called fresh generations on that later commit.

`--profile-io` uses an optional APSW extra and two matched fresh private pager caches. The
baseline/wasteful example returns 13 in both cases and scores the wasteful query 6.90/100
relative to the baseline. Wrong results or prose receive zero. These are SQLite logical
page accesses, not physical device reads. Engine/version/cache metadata is retained.

## HTTP, deployment and concurrency scope

The final soak made real loopback HTTP requests through the production-configured API, with
an **explicit deterministic SDK stub**. Its artificial provider latency was 100 ms per
boundary invocation. Offered load intentionally exceeded model capacity. All 864 overload
responses carried `Retry-After: 1`, accepted responses were correct, session/client bounds
held, the test ledger matched 1,730 stub invocations, and post-load recovery/shutdown passed.
The 276.71 ms overall response p95 and 33.26 ms maximum readiness time are local stub-test
measurements, not live model latency or Render capacity. The earlier passing soak is also
retained: [summary](http-soak-summary.json).

The complete byte-exact soak JSON captures are gzip-compressed to keep the submission small:
[final](http-soak-final.json.gz) and [earlier](http-soak.json.gz). Each summary records the
SHA-256 of the uncompressed bytes. Stub tokens/SDK-boundary counts are never added to genuine
provider usage.

Actual Docker checks verified authentication, origins, body limits, private-file exclusions,
UID 10001, read-only root, dropped capabilities, no-new-privileges, resource bounds, readiness,
retained test-ledger usage across restart and clean shutdown. They used a disposable volume
and no real key; one synthetic reservation tested persistence without touching the owner
ledger. The [first harness diagnosis](container-first-attempt.json) records an old random
Docker host port retained after restart; refreshing the mapping fixed the harness. Both
[earlier](production-container.json) and final successful application checks are retained.

## Real-provider attempts and the remaining limit

The first [live attempt](live-conversations.json), source `a3b9b24`, accepted all three
initial hybrid requests. On the next wave, two follow-ups chose the wrong portfolio because
`the selected portfolio` was not recognized by the service's history trigger. The verifier
caught the errors. This was not a successful protocol.

The service now resolves explicit selected/current references from that session before
asking the model, or clarifies with zero calls when no selection exists. Independent session
tests cover that binding. The complete separate corrected attempt accepted three initial
hybrids and one follow-up correctly. Two other follow-ups returned structured HTTP 429
`daily_quota` errors with `Retry-After`. The third wave was never started. Its ten SDK
attempts include two quota failures with unreported usage; no complete billing total or
nine-question pass is claimed. The earlier source's `busy_responses` aggregate includes
these two quota responses; the individual HTTP codes are authoritative, and the current
runner records quota and capacity responses separately.

The corrected run demonstrates accepted-answer correctness, isolated session identities,
bounded clients, accounting and graceful quota failures. It does **not** finish the planned
sustained live-provider accuracy protocol. Re-run it after the provider quota recovers using
the [operations guide](../../docs/OPERATIONS.md). Single-process deployment is supported;
distributed replicas, externally operated TLS/monitoring and availability SLAs remain outside
the verified scope.

## Capture integrity

[SHA-256 manifest](artifact-sha256.json) covers the supplied JSON/Markdown/terminal streams,
run manifest, full compressed soak captures, replay records, live attempts and Docker/page
profiles. Failed and incomplete attempts are preserved; no fragments are stitched into a
passing full score. The directory uses the local India date; capture timestamps use UTC.
