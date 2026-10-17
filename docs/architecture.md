# System Architecture

## Event Flow

1. A sales event is submitted to the Lambda function.
2. Lambda validates required fields, quantity, and price.
3. The validated order is written to DynamoDB.
4. Lambda publishes a notification to SNS.
5. SNS forwards the notification to its subscribed SQS queue.
6. CloudWatch Logs records processing activity and validation warnings.

## Components

- **Lambda:** Python event-processing logic.
- **DynamoDB:** Persistent order storage.
- **SNS:** Event notification distribution.
- **SQS:** Queues notifications for downstream consumers.
- **CloudWatch Logs:** Troubleshooting and observability.
- **IAM:** Permissions for service-to-service operations.

## Error Handling

- Invalid input returns status code 400.
- Duplicate order IDs return status code 409.
- Unexpected AWS service errors are logged and raised.

## Reliability Consideration

DynamoDB is written before SNS is published. A publish failure can therefore leave a saved order without a notification. For production use, consider an outbox pattern and a retry or recovery mechanism.
