# 1. Create the SQS Dead Letter Queue
resource "aws_sqs_queue" "dlq" {
  name = "yahoo_terrafrom_sqs"
}

# 2. Create the EventBridge Schedule
resource "aws_scheduler_schedule" "yahoo_schedule" {
  name = "yahoo_terraform_scheduler"
  group_name = "default"

  flexible_time_window {
    mode = "OFF"
  }

  # Updated to run every 10 minutes
  schedule_expression = "rate(10 minutes)"

  # Optional but recommended to ensure permissions are ready
  depends_on = [aws_iam_role_policy.scheduler_batch_policy] 

  target {
    arn      = "arn:aws:scheduler:::aws-sdk:batch:submitJob"
    role_arn = aws_iam_role.scheduler_role.arn

    input = jsonencode({
      JobDefinition = aws_batch_job_definition.python_app_job.arn
      JobName       = "yahoo_scheduled_run"
      JobQueue      = aws_batch_job_queue.fargate_queue.arn
    })

    dead_letter_config {
      arn = aws_sqs_queue.dlq.arn
    }
  }
}
