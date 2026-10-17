import json
import logging
import os
from decimal import Decimal

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

dynamodb = boto3.resource("dynamodb")
sns = boto3.client("sns")

TABLE_NAME = os.environ.get("TABLE_NAME", "SalesEvents")
TOPIC_ARN = os.environ.get("TOPIC_ARN")

table = dynamodb.Table(TABLE_NAME)


def lambda_handler(event, context):
    try:
        logger.info("Received sales event: %s", json.dumps(event))

        order_id = str(event["order_id"]).strip()
        customer_id = str(event["customer_id"]).strip()
        product = str(event["product"]).strip()
        quantity = int(event["quantity"])
        price = Decimal(str(event["price"]))

        if not order_id or not customer_id or not product:
            raise ValueError("Order, customer, and product are required")

        if quantity <= 0 or price <= 0:
            raise ValueError("Quantity and price must be positive")

        if not TOPIC_ARN:
            raise ValueError("TOPIC_ARN environment variable is not configured")

        total_amount = quantity * price

        item = {
            "order_id": order_id,
            "customer_id": customer_id,
            "product": product,
            "quantity": quantity,
            "price": price,
            "total_amount": total_amount,
        }

        table.put_item(
            Item=item,
            ConditionExpression="attribute_not_exists(order_id)",
        )

        message = {
            "order_id": order_id,
            "customer_id": customer_id,
            "product": product,
            "quantity": quantity,
            "price": float(price),
            "total_amount": float(total_amount),
        }

        sns.publish(
            TopicArn=TOPIC_ARN,
            Subject="New Sales Event",
            Message=json.dumps(message),
        )

        logger.info(
            "Order %s saved to DynamoDB and published to SNS",
            order_id,
        )

        return {
            "statusCode": 200,
            "body": json.dumps({
                "message": "Sales event saved to DynamoDB and published to SNS",
                "order_id": order_id,
                "total_amount": float(total_amount),
            }),
        }

    except ClientError as error:
        error_code = error.response["Error"]["Code"]

        if error_code == "ConditionalCheckFailedException":
            return {
                "statusCode": 409,
                "body": json.dumps({
                    "message": "Order already exists",
                    "order_id": str(event.get("order_id", "unknown")),
                }),
            }

        logger.exception("AWS service operation failed")
        raise

    except (KeyError, TypeError, ValueError) as error:
        logger.warning("Invalid sales event: %s", error)
        return {
            "statusCode": 400,
            "body": json.dumps({
                "message": "Invalid sales event",
                "error": str(error),
            }),
        }
