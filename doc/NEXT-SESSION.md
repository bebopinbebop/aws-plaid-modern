# Next-session runbook — November 13, 2026

This adds operational detail to the [November 12 deployment handoff](DEPLOYMENT-STATUS.md). It records the next work to do; it does **not** claim a new deployment, a fresh cloud-health check or completed banking acceptance tests on November 13.

## Resume without redeploying

The application was already deployed with Plaid Sandbox. Start with the existing site rather than running the deployment sequence again. The previous source publication included these commits:

- `e771454` — Fix Amplify custom headers for the frontend monorepo.
- `50fc887` — Record Sandbox deployment results and next-session checklist.

Both were pushed to remote `main` and the local/remote heads matched at the end of that session. The working tree was clean when this documentation follow-up began. The automatic Amplify build potentially triggered by that push was **not subsequently verified** in that session; the earlier successful initial release is the verified hosting result.

These read-only commands retrieve the current stack status and site URL using the existing AWS profile. They print status/public URL only, not stack parameters or secret values:

```sh
aws cloudformation describe-stacks \
  --stack-name aws-plaid-modern-dev --region us-east-1 --profile default \
  --query 'Stacks[0].StackStatus' --output text --no-cli-pager

aws cloudformation describe-stacks \
  --stack-name aws-plaid-modern-dev --region us-east-1 --profile default \
  --query "Stacks[0].Outputs[?OutputKey=='FrontendUrl'].OutputValue | [0]" \
  --output text --no-cli-pager
```

In the CloudFormation stack's Resources tab, open `FrontendApp`, then its `main` branch. Check the latest Amplify job and its source commit before attributing behavior to a new push. A successful frontend build does not apply a changed SAM template to the backend.

## Acceptance evidence to collect

All rows below are **pending**. Use Sandbox data and record only sanitized outcomes; avoid screenshots or logs containing tokens, MFA codes, institution credentials or financial details.

| Check | Passing evidence |
| --- | --- |
| Signup and email verification | A new test user can verify their email and reach MFA enrollment. |
| MFA and sign-in | TOTP enrollment completes and a later sign-in succeeds with MFA. |
| Non-OAuth Sandbox Link | Link returns to the application without a token-exchange error; the linked Item appears after refresh. |
| Initial synchronization | Expected Sandbox accounts and transactions appear after workers complete. |
| User isolation | A separate test account cannot see the first account's Items, accounts or transactions. |
| Incremental sync | Controlled Sandbox updates/removals are reflected after sync, without duplicate records. |
| Disconnect | The selected Item is revoked and its intended local records are removed; another Item remains intact. |
| Sign-out | Protected data is unavailable after signing out. |

For each result, record the date, deployed source commit, scenario, expected versus observed behavior and any sanitized error. Do not mark webhook handling verified solely because an initial sync succeeded: initial sync and subsequent signed webhook delivery exercise different triggers.

## Where to inspect a failure

Logical IDs below identify resources in the stack's Resources tab; physical names are generated and should be obtained there.

| Symptom | First resources to inspect |
| --- | --- |
| Site fails to publish or shows old code | `FrontendApp` / `Branch`: latest Amplify job, source commit, build and deploy steps. |
| Signup or MFA fails | `CognitoUserPool` and `UserPoolClient`; capture the sanitized UI error. |
| Link creation, token exchange or disconnect fails | `ApiFunction`, `ApiFunctionLogGroup` and `AccessLogGroup`. |
| Item links but transactions do not arrive | `WebhookQueue`, `WebhookProcessorFunction` and `WebhookProcessorFunctionLogGroup`, then `WriteQueue`, `BatchWriterFunction` and `BatchWriterFunctionLogGroup`. |
| Repeated worker failures | `WebhookDeadLetterQueue` and `WriteDeadLetterQueue`; investigate the cause before any replay. |
| Authenticated read fails | `GraphQLApi`, its resolvers/data source and `Table`; distinguish an authorization error from pending synchronization. |

The template explicitly sets **three-day retention** on all four application log groups. Collect necessary sanitized evidence promptly. Reading queue metrics is a useful first step; receiving/replaying messages or invoking write paths changes state and is not part of a read-only inspection.

## Remaining operational work

- Audit project tags against CloudFormation membership, including IAM and the separate SAM artifact infrastructure. The previously observed 25 tagged entries do not establish complete coverage.
- Review budget alerts, service alarms and actual spend; these were not configured or validated by the deployment report.
- Decide whether three-day log retention is sufficient before longer testing.
- Review data preservation before any stack deletion or resource replacement. The current template explicitly uses `DeletionPolicy: Delete` / `UpdateReplacePolicy: Delete` on several stateful resources, including `Table`, `PlaidCredential` and `CognitoUserPool`. Stopping a session does not stop AWS charges, and deleting a stack is not a harmless pause.
- Keep OAuth-specific testing pending until the deployed redirect is registered in Plaid and the matching backend parameter is configured.

No new AWS mutation is required to publish this runbook locally. Committing it records the handoff; pushing to connected `main` can trigger an Amplify release and should be treated as publication.
