#!/usr/bin/env python3
"""Write only public stack outputs to a Vite .env.local file (never credentials)."""

import argparse
import json
from pathlib import Path
import subprocess

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--stack-name", required=True)
parser.add_argument("--region", required=True)
parser.add_argument("--profile")
parser.add_argument("--output", type=Path, default=Path("frontend/.env.local"))
args = parser.parse_args()
command = [
    "aws",
    "cloudformation",
    "describe-stacks",
    "--stack-name",
    args.stack_name,
    "--region",
    args.region,
    "--output",
    "json",
    "--no-cli-pager",
]
if args.profile:
    command += ["--profile", args.profile]
result = json.loads(subprocess.check_output(command, text=True))
outputs = {entry["OutputKey"]: entry["OutputValue"] for entry in result["Stacks"][0]["Outputs"]}
mapping = {
    "VITE_BACKEND_URL": "BackendUrl",
    "VITE_GRAPHQL_URL": "GraphQLUrl",
    "VITE_COGNITO_USERPOOL_ID": "CognitoUserPoolId",
    "VITE_COGNITO_CLIENT_ID": "CognitoUserPoolClientId",
}
values = {"VITE_REGION": args.region, **{key: outputs[value] for key, value in mapping.items()}}
args.output.write_text("".join(f"{key}={value}\n" for key, value in values.items()))
print(f"Wrote public configuration to {args.output}")
