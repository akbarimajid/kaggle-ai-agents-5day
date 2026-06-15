# Runbook: DAG failures after deployment

## Symptoms

- DAG fails immediately after a release
- Task errors reference configuration, environment variables, or external datasets
- Failure rate spikes correlate with deploy timestamp

## Diagnosis steps

1. Identify recent deployments via release metadata (`get_deployments`)
2. Compare failing DAG version with last known good version
3. Search worker logs for `KeyError`, missing env vars, or 404 dataset errors
4. Verify worker ConfigMap / deployment env matches DAG expectations

## Common root causes

| Cause | Indicators |
|-------|------------|
| Missing environment variable | KeyError in worker logs; ConfigMap diff |
| Invalid external resource reference | BigQuery/S3 404 errors |
| Breaking DAG code change | Stack trace in task import |

## Safe remediation

- Roll back to previous DAG bundle version via standard release pipeline
- Fix configuration in staging before re-promoting
- Re-run failed DAG after validation
- Add CI checks for required env vars and dataset existence

## Do not

- Patch workers manually in production
- Disable retries globally
- Modify production datasets without data governance approval
