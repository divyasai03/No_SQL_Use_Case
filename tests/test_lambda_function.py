import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Make the src folder importable during testing.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

# Prevent real AWS connections when importing the Lambda module.
with patch("boto3.resource") as mock_resource, patch("boto3.client") as mock_client:
    mock_resource.return_value.Table.return_value = MagicMock()
    mock_client.return_value = MagicMock()

    import lambda_function


@pytest.fixture
def aws_mocks():
    with patch.object(lambda_function, "table") as mock_table, patch.object(
        lambda_function, "sns"
    ) as mock_sns:
        lambda_function.TOPIC_ARN = "arn:aws:sns:example"
        yield mock_table, mock_sns


def make_event(**overrides):
    event = {
        "order_id": "TEST-001",
        "customer_id": "C001",
        "product": "Keyboard",
        "quantity": 2,
        "price": 1500,
    }
    event.update(overrides)
    return event


def test_valid_order_is_saved_and_published(aws_mocks):
    mock_table, mock_sns = aws_mocks

    result = lambda_function.lambda_handler(make_event(), None)

    assert result["statusCode"] == 200
    body = json.loads(result["body"])
    assert body["order_id"] == "TEST-001"
    assert body["total_amount"] == 3000.0

    mock_table.put_item.assert_called_once()
    mock_sns.publish.assert_called_once()


def test_negative_quantity_is_rejected(aws_mocks):
    mock_table, mock_sns = aws_mocks

    result = lambda_function.lambda_handler(
        make_event(quantity=-2), None
    )

    assert result["statusCode"] == 400
    mock_table.put_item.assert_not_called()
    mock_sns.publish.assert_not_called()


def test_missing_customer_is_rejected(aws_mocks):
    mock_table, mock_sns = aws_mocks

    result = lambda_function.lambda_handler(
        make_event(customer_id=""), None
    )

    assert result["statusCode"] == 400
    mock_table.put_item.assert_not_called()
    mock_sns.publish.assert_not_called()


def test_duplicate_order_returns_conflict(aws_mocks):
    mock_table, mock_sns = aws_mocks

    error = {
        "Error": {
            "Code": "ConditionalCheckFailedException",
            "Message": "Order already exists",
        }
    }
    mock_table.put_item.side_effect = (
        lambda **kwargs: (_ for _ in ()).throw(
            lambda_function.ClientError(error, "PutItem")
        )
    )

    result = lambda_function.lambda_handler(make_event(), None)

    assert result["statusCode"] == 409
    assert json.loads(result["body"])["message"] == "Order already exists"
    mock_sns.publish.assert_not_called()