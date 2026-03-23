# 1. Define the IAM Role and the Trust Policy (Trusted Entities)
resource "aws_iam_role" "batch_ecs_task_role" {
  name = "BatchEcsTaskTerraform"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Sid    = ""
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
      },
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "batch.amazonaws.com"
        }
      }
    ]
  })
}

# 2. Attach the Managed Policies from your image
locals {
  policies = [
    "arn:aws:iam::aws:policy/AmazonECS_FullAccess",
    "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy",
    "arn:aws:iam::aws:policy/AmazonS3FullAccess",
    "arn:aws:iam::aws:policy/AWSBatchFullAccess",
    "arn:aws:iam::aws:policy/SecretsManagerReadWrite"
  ]
}

resource "aws_iam_role_policy_attachment" "managed_attachments" {
  for_each   = toset(local.policies)
  role       = aws_iam_role.batch_ecs_task_role.name
  policy_arn = each.value
}


# 3. IAM Role for EventBridge to trigger Batch
resource "aws_iam_role" "scheduler_role" {
  name = "yahoo_terraform_scheduler_role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = { Service = "scheduler.amazonaws.com" }
    }]
  })
}

resource "aws_iam_role_policy" "scheduler_batch_policy" {
  name = "allow_batch_submit"
  role = aws_iam_role.scheduler_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = "batch:SubmitJob"
        Resource = [
          aws_batch_job_definition.python_app_job.arn,
          aws_batch_job_queue.fargate_queue.arn
        ]
      },
      {
        Effect   = "Allow"
        Action   = "sqs:SendMessage"
        Resource = aws_sqs_queue.dlq.arn
      }
    ]
  })
}