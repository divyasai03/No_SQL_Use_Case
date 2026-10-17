# AWS Event-Driven Data Ingestion Pipeline

## Project Overview

This project demonstrates an event-driven sales data ingestion system built using AWS services and Python. It validates incoming sales events, stores valid orders in Amazon DynamoDB, and publishes notifications through Amazon SNS to Amazon SQS.

## Architecture

1. A sales event is submitted to an AWS Lambda function.
2. Lambda validates the event fields and checks that quantity and price are positive.
3. Valid orders are stored in the DynamoDB `SalesEvents` table.
4. Lambda publishes the order notification to the SNS `sales-events-topic`.
5. SNS delivers the notification to the subscribed SQS `sales-events-queue`.
6. Amazon CloudWatch Logs records processing information and validation warnings.

## AWS Services Used

- **AWS Lambda:** Runs the Python event-processing function.
- **Amazon DynamoDB:** Stores sales orders.
- **Amazon SNS:** Publishes sales-event notifications.
- **Amazon SQS:** Receives queued notifications from SNS.
- **Amazon CloudWatch:** Stores application logs.
- **AWS IAM:** Controls permissions between services.

## Technologies

- Python
- boto3
- pytest
- AWS Console
- Git and GitHub

## Example Event

```json
{
  "order_id": "1004",
  "customer_id": "C004",
  "product": "Monitor",
  "quantity": 2,
  "price": 12000
}
```

Expected total amount: `24000`.

## Validation and Error Handling

- Rejects missing required fields.
- Rejects non-positive quantity or price.
- Returns status code `400` for invalid events.
- Returns status code `409` when an order ID already exists.
- Logs processing information and validation warnings.
- Raises unexpected AWS service errors so they can be investigated.

## Automated Tests

Run the local test suite from the project root:

```powershell
python -m pytest -v
```

The tests mock AWS service calls and cover valid orders, invalid quantity, missing customer ID, and duplicate order handling.

## Project Structure

```text
aws_event_driven_ingestion/
├── src/
│   └── lambda_function.py
├── tests/
│   └── test_lambda_function.py
├── docs/
├── requirements.txt
└── README.md
```

## Configuration

Configure the following environment variables for the Lambda function:

- `TABLE_NAME`: DynamoDB table name, for example `SalesEvents`.
- `TOPIC_ARN`: ARN of the SNS topic.

The Lambda execution role must have permission to write to the DynamoDB table and publish to the SNS topic.

## Important Design Consideration

The current implementation writes to DynamoDB before publishing to SNS. If publishing fails after the database write succeeds, the order may be stored without its notification. A production implementation should add reliable retry and recovery handling, such as an outbox pattern.

## Security

Do not commit AWS access keys, secret keys, account-specific credentials, `.env` files containing secrets, or virtual-environment files to GitHub.

## Learning Outcomes

- Implemented event validation using Python.
- Integrated AWS Lambda with DynamoDB, SNS, and SQS.
- Applied duplicate-order protection.
- Added logging and error handling.
- Created automated tests with pytest and mocks.
