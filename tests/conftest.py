import importlib
import sys
from pathlib import Path

import pytest


@pytest.fixture
def load_app(monkeypatch):
    for key, value in {
        "AWS_ACCESS_KEY_ID": "testing",
        "AWS_SECRET_ACCESS_KEY": "testing",
        "AWS_DEFAULT_REGION": "us-east-1",
        "AWS_EC2_METADATA_DISABLED": "true",
        "TABLE_NAME": "test-table",
        "KEY_ARN": "arn:aws:kms:us-east-1:123456789012:key/test",
        "PLAID_SECRET_ARN": "test-secret",
        "WEBHOOK_QUEUE_URL": "https://sqs.example/test.fifo",
        "QUEUE_URL": "https://sqs.example/write.fifo",
        "POWERTOOLS_TRACE_DISABLED": "true",
        "POWERTOOLS_METRICS_NAMESPACE": "Test",
    }.items():
        monkeypatch.setenv(key, value)

    import botocore.client

    def offline_call(self, operation, params):
        if operation == "DescribeTable":
            return {
                "Table": {
                    "TableName": "test-table",
                    "KeySchema": [
                        {"AttributeName": "pk", "KeyType": "HASH"},
                        {"AttributeName": "sk", "KeyType": "RANGE"},
                    ],
                }
            }
        raise AssertionError(f"Unexpected AWS call in offline test: {operation}")

    monkeypatch.setattr(botocore.client.BaseClient, "_make_api_call", offline_call)

    def load(service, module):
        for name in list(sys.modules):
            if name == "app" or name.startswith("app."):
                del sys.modules[name]
        monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1] / "backend" / service))
        return importlib.import_module("app." + module)

    return load
