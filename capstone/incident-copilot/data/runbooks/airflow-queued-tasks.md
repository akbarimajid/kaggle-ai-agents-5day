# Runbook: Airflow tasks stuck in queued

## Symptoms

- Tasks remain in `queued` state for extended periods
- Scheduler logs show tasks being scheduled but not running
- Worker count drops to zero or worker pods stay Pending

## Diagnosis steps

1. Check Airflow UI / status API for queued vs running task counts
2. Inspect Kubernetes events in the target namespace for `FailedScheduling` or quota errors
3. Review `limits.cpu` ResourceQuota utilization metrics
4. Search scheduler logs for "No alive workers" or "insufficient cpu"

## Common root causes

| Cause | Indicators |
|-------|------------|
| Namespace CPU/memory quota exhausted | Quota at 100%, pods Pending, FailedScheduling events |
| No worker deployments | worker_pods_available = 0 without quota errors |
| Image pull failures | Pod events show ErrImagePull |

## Safe remediation

- Confirm quota saturation before action
- Escalate quota increase through platform change control
- Pause non-critical DAGs after stakeholder approval
- Do **not** delete namespaces or disable quotas without approval

## Escalation

Contact platform on-call if quota increase requires cluster-admin intervention.
