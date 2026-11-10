import hashlib
import json
import time
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from jose import jwt
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization


def test_api_import_and_missing_auth(load_app):
    module = load_app("api", "lambda_handler")
    from app import utils
    from aws_lambda_powertools.event_handler.exceptions import UnauthorizedError

    router = MagicMock()
    router.current_event.request_context.authorizer = None
    with pytest.raises(UnauthorizedError):
        utils.authorize_request(router)
    assert module.resolver is not None


def test_webhook_signature_and_claims(load_app, monkeypatch):
    webhook = load_app("api", "routers.webhook")
    private_key = ec.generate_private_key(ec.SECP256R1())
    pem = private_key.private_bytes(
        serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()
    )
    public = private_key.public_key().public_bytes(
        serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo
    )
    monkeypatch.setattr(webhook, "get_credentials", lambda: {})
    webhook.KEY_CACHE["test"] = {"expired_at": None}
    # Keep expired_at alongside the real JWK in the cache.
    from jose import jwk

    webhook.KEY_CACHE["test"].update(jwk.construct(public, "ES256").to_dict())
    body = '{"item_id":"item"}'
    claims = {
        "iat": int(time.time()),
        "request_body_sha256": hashlib.sha256(body.encode()).hexdigest(),
    }

    def token(values):
        return jwt.encode(values, pem, algorithm="ES256", headers={"kid": "test"})

    assert webhook.verify(body, token(claims))
    assert not webhook.verify(body + " ", token(claims))
    assert not webhook.verify(body, "invalid")
    assert not webhook.verify(body, token({**claims, "iat": time.time() - 301}))
    assert not webhook.verify(body, token({**claims, "iat": time.time() + 90}))
    assert not webhook.verify(body, token({"iat": time.time()}))


def test_queue_partial_failure_raises(load_app):
    module = load_app("webhook_processor", "products.abstract_product")
    product = object.__new__(module.AbstractProduct)
    product.sqs = MagicMock()
    product.sqs.send_message_batch.return_value = {"Failed": [{"Id": "1", "Code": "Throttled"}]}
    with pytest.raises(RuntimeError):
        product.send_messages(
            [
                {
                    "Id": "1",
                    "MessageBody": "{}",
                    "MessageAttributes": {"ItemId": {"StringValue": "item", "DataType": "String"}},
                }
            ]
        )
    entry = product.sqs.send_message_batch.call_args.kwargs["Entries"][0]
    assert entry["MessageGroupId"] == "item"


def test_sync_restarts_pagination_and_commits_only_after_enqueue(load_app, monkeypatch):
    module = load_app("webhook_processor", "products.transactions")
    from plaid.exceptions import ApiException
    from app import datastore

    monkeypatch.setattr(
        datastore, "get_item", lambda *args: {"access_token": "secret", "cursor": "start"}
    )
    product = object.__new__(module.Transactions)
    product.client = MagicMock()
    page = lambda cursor, more, added: {
        "next_cursor": cursor,
        "has_more": more,
        "added": added,
        "modified": [],
        "removed": [],
    }
    mutation_error = ApiException(status=400)
    mutation_error.body = json.dumps({"error_code": "TRANSACTIONS_SYNC_MUTATION_DURING_PAGINATION"})
    product.client.transactions_sync.side_effect = [
        page("page2", True, ["discard"]),
        mutation_error,
        page("finish", False, ["keep"]),
    ]
    product.build_message = MagicMock(side_effect=lambda u, i, e, t: {"transaction": t})
    product.send_messages = MagicMock()
    product.store_cursor = MagicMock()
    product.sync("user", "item")
    assert [
        call.args[0].get("cursor") for call in product.client.transactions_sync.call_args_list
    ] == ["start", "page2", "start"]
    product.send_messages.assert_called_once_with([{"transaction": "keep"}])
    product.store_cursor.assert_called_once_with("user", "item", "finish")
    product.client.transactions_sync.side_effect = [page("finish", False, ["keep"])]
    product.send_messages.side_effect = RuntimeError("queue unavailable")
    product.store_cursor.reset_mock()
    with pytest.raises(RuntimeError):
        product.sync("user", "item")
    product.store_cursor.assert_not_called()


def test_writer_deletes_removed_transactions(load_app):
    module = load_app("batch_writer", "lambda_handler")
    module.table = MagicMock()
    context = SimpleNamespace(
        function_name="test",
        function_version="$LATEST",
        invoked_function_arn="arn:aws:lambda:us-east-1:123456789012:function:test",
        memory_limit_in_mb=128,
        aws_request_id="test",
    )
    module.handler(
        {
            "Records": [
                {
                    "body": json.dumps({"pk": "user", "sk": "transaction"}),
                    "messageAttributes": {"EventName": {"stringValue": "REMOVE"}},
                }
            ]
        },
        context,
    )
    batch = module.table.batch_writer.return_value.__enter__.return_value
    batch.delete_item.assert_called_once_with(Key={"pk": "user", "sk": "transaction"})
    batch.put_item.assert_not_called()


def test_authenticated_exchange_encrypts_token_and_creates_item(load_app, monkeypatch):
    api = load_app("api", "lambda_handler")
    from app import datastore, utils
    from app.routers import tokens
    from dynamodb_encryption_sdk.delegated_keys.jce import JceNameLocalDelegatedKey
    from dynamodb_encryption_sdk.material_providers.static import (
        StaticCryptographicMaterialsProvider,
    )
    from dynamodb_encryption_sdk.materials.raw import RawEncryptionMaterials, RawDecryptionMaterials
    from dynamodb_encryption_sdk.encrypted import CryptoConfig
    from dynamodb_encryption_sdk.encrypted.item import decrypt_python_item
    from dynamodb_encryption_sdk.structures import EncryptionContext, AttributeActions
    from dynamodb_encryption_sdk.identifiers import CryptoAction

    signing = JceNameLocalDelegatedKey.generate("HmacSHA256", 256)
    encryption = JceNameLocalDelegatedKey.generate("AES", 256)
    provider = StaticCryptographicMaterialsProvider(
        encryption_materials=RawEncryptionMaterials(signing_key=signing, encryption_key=encryption),
        decryption_materials=RawDecryptionMaterials(
            verification_key=signing, decryption_key=encryption
        ),
    )
    original_materials = provider.encryption_materials

    def checked_materials(context):
        assert context.attributes["pk"] == {"S": "USER#subject#ITEM#item"}
        assert context.attributes["sk"] == {"S": "v0"}
        return original_materials(context)

    monkeypatch.setattr(provider, "encryption_materials", checked_materials)
    monkeypatch.setattr(tokens, "AwsKmsCryptographicMaterialsProvider", lambda **kwargs: provider)
    monkeypatch.setattr(datastore, "check_institution", lambda *args: False)
    client = MagicMock()
    client.item_public_token_exchange.return_value = SimpleNamespace(
        item_id="item", access_token="sensitive-token"
    )
    monkeypatch.setattr(utils, "get_plaid_client", lambda: client)
    write = MagicMock()
    monkeypatch.setattr(tokens.dynamodb.meta.client, "transact_write_items", write)
    payload = {
        "public_token": "public-token",
        "metadata": {"institution": {"institution_id": "bank", "name": "Bank"}},
    }
    event = {
        "version": "2.0",
        "routeKey": "$default",
        "rawPath": "/v1/tokens",
        "headers": {"content-type": "application/json"},
        "isBase64Encoded": False,
        "requestContext": {
            "stage": "$default",
            "http": {"method": "POST", "path": "/v1/tokens"},
            "authorizer": {"jwt": {"claims": {"sub": "subject"}, "scopes": []}},
        },
        "body": json.dumps(payload),
    }
    result = api.resolver.resolve(event, None)
    assert result["statusCode"] == 202
    stored = write.call_args.kwargs["TransactItems"][0]["Put"]["Item"]
    assert stored["pk"] == "USER#subject#ITEM#item"
    assert stored["access_token"] != "sensitive-token"
    stored["cursor"] = "later-cursor"
    decrypted = decrypt_python_item(
        stored,
        CryptoConfig(
            materials_provider=provider,
            encryption_context=EncryptionContext(
                table_name="test-table", partition_key_name="pk", sort_key_name="sk"
            ),
            attribute_actions=AttributeActions(
                default_action=CryptoAction.DO_NOTHING,
                attribute_actions={"access_token": CryptoAction.ENCRYPT_AND_SIGN},
            ),
        ),
    )
    assert decrypted["access_token"] == "sensitive-token"
    assert decrypted["cursor"] == "later-cursor"


def test_initial_sync_uses_same_fifo_group_as_webhooks(load_app, monkeypatch):
    import importlib

    utils = load_app("webhook_processor", "utils")
    monkeypatch.setattr(utils, "get_plaid_client", MagicMock())
    handler = importlib.import_module("app.lambda_handler")
    from aws_lambda_powertools.utilities.data_classes.dynamo_db_stream_event import DynamoDBRecord
    from aws_lambda_powertools.utilities.data_classes.sqs_event import SQSRecord

    sqs = MagicMock()
    monkeypatch.setattr(handler.boto3, "client", lambda *args, **kwargs: sqs)
    monkeypatch.setattr(handler.transactions, "sync", MagicMock())
    monkeypatch.setattr(handler.accounts_balance, "get_balances", MagicMock())
    handler.record_handler(
        DynamoDBRecord({"dynamodb": {"NewImage": {"sk": {"S": "USER#subject#ITEM#item"}}}})
    )
    handler.transactions.sync.assert_not_called()
    message = sqs.send_message.call_args.kwargs
    assert message["MessageGroupId"] == "item"
    attributes = {
        key: {"stringValue": value["StringValue"], "dataType": "String"}
        for key, value in message["MessageAttributes"].items()
    }
    handler.record_handler(
        SQSRecord({"body": message["MessageBody"], "messageAttributes": attributes})
    )
    handler.transactions.sync.assert_called_once_with("subject", "item")
    handler.accounts_balance.get_balances.assert_not_called()
