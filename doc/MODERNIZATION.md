# Modernization audit — 2026-11-10

The working tree was clean at the start. Changes preserve SAM/CloudFormation, Amplify Hosting, Cognito, AppSync, API Gateway, DynamoDB and the asynchronous Plaid worker architecture. No cloud deployment or external publication was performed.

## Findings and changes

| Area | Finding | Change |
| --- | --- | --- |
| Tooling | Installed SAM 1.125.0 rejected the existing Python 3.13 runtime | Verified with isolated SAM 1.171.0; retained supported Python 3.13 |
| Dependency layer | Powertools used a fixed public layer ARN and a different development dependency declaration | Package Powertools 3.39.0 and boto3 with the application layer; no region-specific public layer dependency |
| Plaid SDK | Old Python SDK/environment choices | Plaid Python 46.0.0; Sandbox/Production only; public encryption APIs with unchanged encrypted record format |
| API startup | `SecretsProvider(config=...)` is invalid | Use `boto_config` consistently |
| Identity | REST keys used `sub`, AppSync keys used `username` | All resolver partition keys and Item-ID parsing use `sub`; regression tests use different values for the two claims |
| Account initialization | Trusted browser account metadata could omit balances/accounts | Accounts returned by Transactions Sync are written through the ordered queue |
| Ordering | Initial stream synchronization could run concurrently with webhook sync; standard write queue could reorder updates/removals | Route initialization through per-Item FIFO webhook groups; FIFO write queue and DLQ; correct Lambda FIFO batch size |
| Delivery | Failed SQS batch entries and cursor-write errors were logged and swallowed | Raise failures to retry; do not advance cursor after failed enqueue |
| Transactions | Mutation during pagination was not retried from its original cursor | Bounded restart of the entire page collection, discarding incomplete results |
| Removal | Producer emitted `REMOVE`, writer only recognized `DELETE` | Both deletion event names remove the record |
| FIFO API | Per-message delays and constant webhook dedup IDs were incompatible with reliable delivery | Omit per-message `DelaySeconds` as required by [SQS FIFO](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/APIReference/API_SendMessage.html); unique IDs avoid dropping distinct updates in the dedup interval |
| Webhooks | Malformed JWTs/missing claims could raise; key fetches had no timeout | Validate algorithm/header/claims/body hash and freshness; bounded HTTP timeouts; decoded raw request body; no JWT value in error logs |
| Runtime logging | Request events and Lambda responses could include public/access tokens | Disable event logging and trace response capture |
| Item deletion | Local deletion did not revoke Plaid access, lacked Query permission and suppressed failures | Decrypt owned token, call `/item/remove`, query/delete local records and propagate failures |
| Infrastructure | Resolver creation could precede schema creation; custom roles lacked X-Ray grants | Add schema dependencies and execution-role X-Ray permissions; keep KMS permissions aligned |
| Cognito | Implicit OAuth links were unused; enforced threat protection needs Plus | Remove obsolete implicit-login outputs; preserve enforced protection and specify Plus explicitly |
| Hosting | Obsolete CRA tooling and ambiguous frontend working/artifact directories | Vite 8.3.7, Node 24, lockfile-based installs, explicit Amplify monorepo root and `dist` output; remove unused administrative Amplify role |
| Browser auth | Invalid GraphQL auth mode, malformed OAuth scope, misspelled pool variable | Configure existing Cognito directly, use `userPool` auth for GraphQL and access-token REST headers |
| Browser UX | Link could open before ready; error/cancel left spinner running; 202 balance response parsed as JSON | Wait for Link readiness, recover on failures/cancel, handle empty responses, display load errors, provide data reload and balance refresh |
| OAuth | Plaid redirect was not configured/resumed | Optional stack redirect parameter, tab-scoped Link-token persistence and redirect resume; preserve query parameters across Cognito login |
| Local instructions | No reproducible test command or environment export | Updated Makefile, current prerequisites, public-output export helper, example environment and complete Sandbox acceptance checklist |

AWS still lists Python DynamoDB Encryption Client 3.x as [generally available](https://docs.aws.amazon.com/database-encryption-sdk/latest/devguide/legacy-dynamodb-encryption-client.html), so replacing its ciphertext format was unnecessary. Plaid's [Transactions documentation](https://plaid.com/docs/api/products/transactions/) defines the cursor restart behavior. Amplify's [monorepo guidance](https://docs.aws.amazon.com/amplify/latest/userguide/monorepo-configuration.html) defines the hosting root and build configuration.

## Local verification

- Seven offline Python tests: API startup/auth rejection, real ES256 webhook verification, partial SQS failure, pagination restart/cursor discipline, transaction removal, authenticated token exchange with actual encryption/decryption, and stream-to-FIFO serialization.
- Nine offline AppSync resolver tests, including subject/username differences and pagination/error handling.
- Three frontend configuration tests.
- Production frontend build using Node 24 and Vite 8; clean `npm ci` lockfile installation.
- Current SAM native build for all three Python 3.13 x86_64 functions and the dependency layer. The layer contains Linux binary wheels, not macOS binaries, and is approximately 90 MB uncompressed.
- Current CloudFormation lint, Python dependency consistency and whitespace checks.
- Frontend production dependency audit: zero known vulnerabilities at the time checked. This does not constitute a security audit of the application.

The frontend's roughly 908 kB minified JavaScript entry bundle triggers Vite's size warning. It builds successfully; further code splitting is a performance improvement, not a deployment prerequisite.

## Validation still requiring the target environment

Docker is absent, so container builds/invocations were not executed. No AWS/Plaid/GitHub credentials were used for live integration tests. CloudFormation deployment, actual KMS/IAM permissions, Cognito email/TOTP, AppSync service evaluation, Amplify regional GitHub authorization/builds, Plaid callbacks and OAuth redirects remain to be checked using the root README's acceptance procedure. The old AppSync EvaluateCode tests are opt-in (`npm run test:live --prefix backend/resolvers`).

Updating an existing stack replaces its standard write queue/DLQ with FIFO resources. Drain pending messages and review the changeset first. Production operations also need alarms, DLQ recovery, load testing and an Item reauthentication flow. None of these limitations are hidden by the local checks.
