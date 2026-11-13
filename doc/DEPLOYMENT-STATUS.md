# Deployment status and next steps — November 12, 2026

## Current state

The development application is deployed in **us-east-1** as CloudFormation stack **`aws-plaid-modern-dev`**, using **Plaid Sandbox**. The final stack status was `UPDATE_COMPLETE`; Amplify's initial successful release passed build, deploy and verify. AWS resources are running and can incur ongoing charges.

The modernization, setup guides, private credential helpers and secure-data-flow diagrams were already committed to `main`. Today's deployment used that source plus the Amplify header correction described below. No Plaid production credentials were used.

## What happened today

1. Validated the privately stored Sandbox credentials without printing them; confirmed the AWS target and source.
2. Packaged the container-built Lambda code and dependency layer. SAM created its managed artifact storage and uploaded deployment artifacts.
3. Reviewed the generated change set: **52 additions**, with no modifications or removals of existing application resources. Created the new application stack.
4. Started the initial Amplify website release from GitHub `main`.
5. Fixed Amplify custom response headers to use the monorepo `applications` / `appRoot: frontend` format. The frontend compiled, but its initial publish failed on the previous header format. One attempted header update also failed because the packaged template represented its multiline string differently; CloudFormation rolled that update back. The corrected source, built and packaged header strings were parsed and linted before retrying.
6. Applied the corrected header configuration through a reviewed change set. The app was updated without replacement; the branch's dependent app reference was also included. The stack update and retried website release completed successfully.

The persistent fix is in `template.yml`. The generated build templates and private deployment-state files are not repository source and are not committed. Header syntax follows the [AWS monorepo custom-header reference](https://docs.aws.amazon.com/amplify/latest/userguide/custom-header-YAML-format.html).

## Verification and limits

- CloudFormation finished successfully; Amplify build, deploy and verify all succeeded.
- The published React entry page and its referenced JavaScript/CSS assets returned HTTP 200.
- Responses included `X-Frame-Options: SAMEORIGIN` and `X-Content-Type-Options: nosniff`.
- The protected token API returned HTTP 401 without authentication.
- Earlier local/container validation remains recorded in [the predeployment review](PREDEPLOYMENT.md): 23 offline tests, six AppSync service evaluations, container builds and local Lambda smoke checks passed. Those are historical results, not a claim that every check was rerun after deployment.
- **Signup, email verification, TOTP MFA, authenticated bank linking, transaction synchronization and account deletion have not yet been verified together against this deployment.** Hosting success is not complete product acceptance.

## Identifying project resources

The deployed application stack carries **`Project=aws-plaid-modern`** and **`Environment=dev`**. A postdeployment Resource Groups Tagging API query for the Project tag returned **25 resource entries**, across CloudFormation, DynamoDB, SQS, API Gateway, CloudWatch Logs, Lambda, Cognito, Amplify, AppSync, KMS and Secrets Manager. These entries are not a one-to-one count of the 52 CloudFormation additions.

Use that Project tag in AWS resource discovery and the stack's **Resources** tab for the authoritative stack membership list. Existing resource tags also identify the GitHub organization/repository and environment where configured. Tag coverage is **not asserted for every resource or generated child object**: tag support and propagation differ by service, and the SAM-managed artifact stack/bucket are separate deployment infrastructure. Complete coverage, including IAM and artifact storage, remains a follow-up audit; do not assume every object is found by the Project filter.

## Next session checklist

See the [November 13 next-session runbook](NEXT-SESSION.md) for read-only resume commands, acceptance evidence, troubleshooting resources and data-preservation considerations.

1. Open the Amplify branch URL from the stack's `FrontendUrl` output. Create a test account, verify email and enroll TOTP MFA.
2. Sign in and connect a **Sandbox** institution through Plaid Link. Confirm initial accounts/transactions appear and remain scoped to that user.
3. Exercise transaction updates/removals and webhook-driven sync; inspect Lambda errors and both FIFO dead-letter queues. Verify disconnect removes the intended Item and revokes its Plaid access.
4. Before testing an OAuth institution, register the exact deployed redirect URL in the Plaid dashboard and configure the matching redirect parameter. Initial deployment used an empty OAuth redirect; start with a non-OAuth Sandbox institution.
5. Audit remaining resource/artifact tags, review log retention, alarms and budget alerts, and measure actual costs. These operational follow-ups are not marked complete.
6. Address acceptance-test findings before considering production credentials or production readiness.

## Source publication and cost boundaries

Amplify now has **automatic builds enabled on `main`**. Pushing today's code and documentation can trigger another frontend build/release. A source push does not apply SAM infrastructure changes; today's header correction has already been applied separately through CloudFormation.

Keep credentials in the private local preparation file and AWS Secrets Manager. Do not commit them, generated frontend environment files, packaged artifacts, account identities or credential-bearing deployment parameter files. Never put Plaid secrets or access tokens into frontend configuration.

The [predeployment review](PREDEPLOYMENT.md) is a dated historical record. Its statements about no deployment and missing prerequisites describe the earlier review, and are superseded by this report for current operational status.
