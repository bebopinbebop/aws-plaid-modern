# Predeployment review — 2026-11-10

> **Historical review:** Deployment was subsequently authorized and completed on November 12, 2026. See [current deployment status](DEPLOYMENT-STATUS.md) for the deployed state, verification limits, tags and next steps. The review below records the earlier predeployment state.

**Assessment: local/container validation passes; cloud deployment is not yet ready for approval.** The remaining prerequisites are saved/validated Sandbox credentials, confirmed regional Amplify GitHub App access, approval of the source branch to host, and an explicit deployment decision. No stack, change set, artifact upload, hosting job or application-data mutation was created during this review.

## Target and source

- Region confirmed by the user: **us-east-1 (Northern Virginia)**.
- Existing AWS profile: `default`; STS identity succeeded. The account/user identity was reported in the private work session and is intentionally not embedded in this public repository.
- Proposed new stack: `aws-plaid-modern-dev`. This is a proposal, not a provisioned stack.
- Repository: `https://github.com/bebopinbebop/aws-plaid-modern.git`.
- The work was initially prepared on local `codex/modernize-aws-plaid`. The user subsequently explicitly requested **publication to the existing remote `main` branch**, retaining the three commits. No alternate remote branch is requested. Remote `main` initially remained at `6ec8e0c` before publication.
- For eventual hosting, propose `BranchName=main` after the reviewed source is available there. The user authorized source publication to main; **AWS deployment and hosting-job creation remain unauthorized**.

Read-only inventory found four root CloudFormation stacks in the configured account/Region, but none with this sample's `ApiFunction`, `DependencyLayer`, `WebhookQueue` and `WriteQueue` resource combination. Amplify listed **zero hosting apps** in this account/Region. Other Plaid-related nested resources belong to a separate Amplify sandbox and are not a deployment of this repository. This is not a search of every AWS account/Region.

## Checks completed

| Check | Result and scope |
| --- | --- |
| Docker Desktop | Reachable Linux/amd64 engine; Desktop 4.99.0, Engine 29.9.3; Compose bundled |
| Supported local tools | SAM 1.171.0 and Node 24.22.2 used from isolated local installations; shell defaults still resolve to SAM 1.125.0 / Node 20.18.0 |
| Final SAM container build | Passed for Python 3.13/x86_64 shared layer and all three functions |
| Local Lambda runtime | Empty `BatchWriterFunction` invocation returned null successfully; unauthenticated `ApiFunction` token request returned 401; both used fake credentials and no application writes |
| Offline tests | 11 Python tests, 9 resolver tests and 3 frontend configuration tests: **23** total |
| Linux dependencies | All 11 Python tests also passed inside the Linux SAM build image using the container-built shared layer |
| AppSync service runtime | All 6 existing `EvaluateCode` tests passed in us-east-1 under Node 24; no API or stack was created |
| Frontend | Production Vite build passed; approximately 908 kB minified entry bundle still produces a performance warning |
| Infrastructure | Source and built templates passed current CloudFormation lint; AWS's read-only `ValidateTemplate` accepted the final source |
| AWS identity / IAM | STS identity verified; 26 representative deployment/read actions were allowed by identity-policy simulation, with no missing context values |
| GitHub | Authenticated repository access verified; remote reported zero Actions workflows and zero repository webhooks |
| Hygiene | Python dependency consistency, formatting, whitespace, staged credential/artifact checks and exact previous-README suffix preservation passed |

IAM simulation is not a guarantee that every deployment API call will succeed: resource policies, service-specific conditions, organizational controls, quotas and future role configuration still matter. AWS template validation is not an actual resource-creation rehearsal. A real change set would require authorized packaging/uploads and cloud mutations, so none was prepared remotely.

A preflight infrastructure correction removed `AWS::ApiGateway::Account` and its broad log-push managed policy from the local template. This HTTP API already configures stage access logging. The account-wide REST API logging resource could overwrite a role used by unrelated APIs; [AWS documents that account-wide conflict](https://docs.aws.amazon.com/AWSCloudFormation/latest/TemplateReference/aws-resource-apigateway-account.html). HTTP API [log delivery uses the stage/log group configuration](https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-logging.html). No existing AWS setting was changed.

## Save and validate Sandbox credentials locally

No `.env` is needed for backend Plaid credentials. The application reads Secrets Manager after deployment; Vite environment variables are public. The following helper creates a **local preparation file**, not an application environment file and not an AWS secret.

Copy into zsh:

```zsh
cd /Users/pilot/repo/aws-plaid-modern
.venv/bin/python scripts/save_plaid_credentials.py
```

For other checkouts, first change to that checkout's root. Both the client ID and Sandbox secret prompts are hidden. The helper writes `~/.config/aws-plaid-modern/plaid-sandbox.json`, enforces a `700` directory and `600` file, refuses a symlink credential directory, and uses exclusive creation to prevent overwriting an existing file. It prints only the destination, never the values. Do not paste credentials into chat, command arguments or frontend configuration.

Then perform the optional, non-mutating authentication check:

```sh
.venv/bin/python scripts/check_plaid_credentials.py
```

The checker requires the private permissions, permits only the explicit Sandbox endpoint, and calls Plaid's read-only [`/institutions/get`](https://plaid.com/docs/api/institutions/) endpoint with bounded timeouts. It does not create a Link token, Item, webhook, transaction or AWS resource. It prints a success/failure summary without raw response bodies or credentials. Passing it establishes authentication, not all Transactions product entitlements or the end-to-end Link workflow.

The private credential file was not present when these results were recorded, so **actual Plaid authentication remains unverified**. Matching Plaid SSM parameter names were found in a separate Amplify sandbox; their values were not retrieved or reused. The storage/check helpers were tested with fake values, including permission checks, no overwrite, symlink rejection and Sandbox-only network targeting.

## Git publication boundary

Source publication and AWS deployment are separate decisions. No checked-in/remote GitHub Actions workflows or repository webhooks were found, and no Amplify hosting apps existed in the inspected AWS account/Region. The final requested destination is `main`; no Amplify app currently exists in the inspected target to auto-build it. Check installed GitHub integrations and other accounts/Regions before any future push if those settings change.

The session prepared three coherent local commits. Automatic approval review initially rejected the public push because approval for the exact public destination/branch was not recorded. The user then explicitly requested `main` on the existing remote repository. Fetch and integrate remote main without force-pushing, then use the normal approval path for `https://github.com/bebopinbebop/aws-plaid-modern.git`, branch `main`. If review still requires human confirmation, retain the commits locally and present that exact destination. Do not publish to an alternate branch or claim a push succeeded before remote verification. No review rejection is bypassed.

The template enables Amplify branch auto-builds. After an Amplify app is connected, future pushes to its configured branch can publish the frontend even without SAM deployment. Repository workflow/hook checks are evidence of current settings, not a perpetual guarantee about all external GitHub App integrations.

## Resources proposed by a new stack

The source declares **49 resources**, plus any resources generated by the SAM transform. Principal resources are:

- Three Lambda functions, a Python dependency layer, event source mappings and four log groups.
- API Gateway HTTP API, four routes, JWT authorizer, Lambda integration and default stage.
- Cognito pool/client/domain/resource server, required TOTP and **Plus** threat protection.
- AppSync GraphQL API, DynamoDB datasource/schema and three resolver/function pairs.
- DynamoDB global-table resource with one regional replica, GSI and stream.
- One multi-Region KMS key, one stack-scoped Plaid Secrets Manager secret.
- Two FIFO work queues and two FIFO DLQs, with work-queue policies.
- Five IAM roles and three standalone IAM policies, plus configured managed policies.
- One Amplify app and one configured source branch.

This incurs ongoing AWS costs, including Cognito Plus, KMS, Secrets Manager, logs and hosting. Plaid production is not proposed. Review the actual generated change set, IAM scope and deletion/replacement policies before execution; this inventory is not a remotely created change set.

## Exact deployment sequence for later approval

These are **future commands**, not actions executed by this review. Select the installed current tools in your shell first; the temporary verification paths are not a permanent installation plan. Install/select Node 24 and SAM 1.171.0 or a compatible current release, then verify versions.

```sh
DEMO_PROFILE=default
DEMO_REGION=us-east-1
DEMO_STACK=aws-plaid-modern-dev

aws sts get-caller-identity --profile "$DEMO_PROFILE" --region "$DEMO_REGION"
make test
make validate
make frontend
sam build --use-container --parallel
```

Before any deployment command:

1. Validate the private Sandbox credentials. Confirm Transactions access in Plaid.
2. Confirm the [regional Amplify GitHub App](https://docs.aws.amazon.com/amplify/latest/userguide/setting-up-GitHub-access.html) is installed with access to this repository and that a suitable PAT is available for connection. Existing authenticated Git access alone does not verify the installation. Do not expose the PAT.
3. Review the source commits and authorize the intended hosted branch update separately. The proposed `main` must contain the reviewed modernized code before Amplify builds it. The authorized source-publication step must still pass its approval review; it does not authorize deploying AWS.
4. Confirm the proposed account, stack name, costs and resource policies. Recheck for an existing stack by that exact name and apply the migration procedure below if appropriate.

Only after explicit AWS deployment approval:

```sh
sam deploy --guided \
  --stack-name "$DEMO_STACK" \
  --region "$DEMO_REGION" \
  --profile "$DEMO_PROFILE" \
  --capabilities CAPABILITY_IAM CAPABILITY_AUTO_EXPAND \
  --confirm-changeset
```

Guided parameter choices:

| Parameter | Proposed value / source |
| --- | --- |
| `Environment` | `dev` |
| `GitHubOrg` | `bebopinbebop` |
| `GitHubRepo` | `aws-plaid-modern` |
| `BranchName` | `main`, only after the reviewed source is available there |
| `PlaidEnvironment` | `sandbox` |
| `PlaidClientId` / `PlaidSecretKey` | Existing secure store or the private local preparation file; hidden guided entry, never command arguments |
| `GitHubAccessToken` | Appropriate existing secure token; hidden guided entry |
| `PlaidRedirectUri` | Empty for initial non-OAuth test, or the exact registered HTTPS frontend return URL if already known |

Do not save sensitive parameter overrides into shared configuration. `sam deploy --no-execute-changeset` still packages/uploads artifacts and creates a cloud change set; it is **not** permitted by the current no-cloud-mutation boundary. No deployment command here is safe to run merely because it is documented.

After successful authorized deployment, inspect the public outputs and hosting build before use:

```sh
aws cloudformation describe-stacks \
  --stack-name "$DEMO_STACK" --region "$DEMO_REGION" --profile "$DEMO_PROFILE" \
  --query 'Stacks[0].{Status:StackStatus,Outputs:Outputs}' --output json

python3 scripts/export_frontend_env.py \
  --stack-name "$DEMO_STACK" --region "$DEMO_REGION" --profile "$DEMO_PROFILE"
npm start --prefix frontend
```

Open `http://localhost:3000`, or the hosted `FrontendUrl` after an authorized Amplify build. Starting/redeploying an Amplify job is a publication action and was not done during preflight. If OAuth is needed, register the actual hosted URL and review/deploy the `PlaidRedirectUri` update explicitly.

## Existing-stack/FIFO migration, if a different target is selected

No matching deployment was identified in the inspected target. If an existing older sample stack is selected elsewhere, do not treat this as a blind in-place update:

1. Back up data and inspect its actual resources, queue types, pending/in-flight/delayed messages, active workers and DLQs.
2. Coordinate a maintenance/recovery window and pause input/consumption as appropriate through approved operational steps. Account for incoming Plaid webhooks and initial-stream work during the window.
3. Drain and reconcile the standard `WriteQueue` and `WriteDeadLetterQueue` before their replacement with FIFO resources. Confirm totals and business state, not only visible queue counts.
4. Review secret replacement from the stack-scoped name and any historical username-versus-sub data keys. No automatic data migration is supplied.
5. Review/execute the authorized change set, resume processing and reconcile outstanding sync/write state.

DLQ redrive can replay an older update after a newer one was applied. Plan per-Item reconciliation instead of blindly replaying messages. These are proposed operational steps; no queue was paused, drained, purged or redriven during this session.

## Only after deployment

The root README's Sandbox acceptance checklist still needs real Cognito email verification/TOTP/session restoration; Link cancellation/retry and successful exchange; initial accounts/transactions and pagination; explicit balance refresh; signed Plaid webhook delivery and added/modified/removed transaction persistence; user isolation; actual KMS/IAM operation; Amplify hosting/repository authorization and OAuth redirects. Load/recovery behavior and production readiness are not established by local tests.

The local API 401 check verifies the handler's own missing-user response, not API Gateway's deployed JWT authorizer. AppSync EvaluateCode verifies resolver execution, not deployed authentication/data isolation. Empty writer invocation verifies startup, not successful live DynamoDB writes. Keep these distinctions in the deployment review.
