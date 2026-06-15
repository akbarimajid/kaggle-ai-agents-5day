# Runbook: Scheduler instability and metadata DB connections

## Symptoms

- Scheduler pod restarts or CrashLoopBackOff
- Airflow UI reports scheduler unhealthy
- DAG parsing delays increase
- Metadata DB or PgBouncer errors in logs

## Diagnosis steps

1. Check scheduler restart metrics and liveness probe failures
2. Review PgBouncer pool stats: active connections, waiting clients, maxwait
3. Search scheduler logs for `too many connections` or `OperationalError`
4. Correlate with `parsing_processes` and connection pool size settings

## Common root causes

| Cause | Indicators |
|-------|------------|
| PgBouncer pool exhausted | active = max, waiting_clients > 0 |
| Connection leak in plugin | steadily growing active connections |
| Metadata DB overload | long-running queries, high DB CPU |

## Safe remediation

- Temporarily reduce `parsing_processes` per approved runbook
- Restart scheduler pods **one at a time** after pool headroom confirmed
- Coordinate with DBA on long queries
- Request pool size increase through change window only

## Do not

- Drop metadata tables
- Change PgBouncer `pool_mode` in production without DBA review
- Disable PgBouncer during peak
- Share database credentials in tickets or chat
