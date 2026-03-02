# Find the secret by its name
data "aws_secretsmanager_secret" "yh_finance" {
  name = "YH_Finance_Api"
}

# Fetch the current version of the secret
data "aws_secretsmanager_secret_version" "yh_finance_latest" {
  secret_id = data.aws_secretsmanager_secret.yh_finance.id
}

# Decode the JSON string into a local map for use
locals {
  finance_secrets = jsondecode(data.aws_secretsmanager_secret_version.yh_finance_latest.secret_string)
}

# This finds your Default VPC
data "aws_vpc" "default" {
  default = true
}

# This finds the subnets within that Default VPC
data "aws_subnets" "default" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.default.id]
  }
}

# This finds the "default" security group in that VPC
data "aws_security_group" "default" {
  name   = "default"
  vpc_id = data.aws_vpc.default.id
}


# 1. Fetch the existing Role from AWS Console
data "aws_iam_role" "existing_batch_role" {
  name = "BatchEcsTaskExecutionRole"
}

# 2. Batch Compute Environment (Using the existing role)
resource "aws_batch_compute_environment" "fargate_env" {
  name = "yahoo_terraform"
  type                     = "MANAGED"
  state                    = "ENABLED"
  # Reference the ARN from the data source
  service_role             = data.aws_iam_role.existing_batch_role.arn

  compute_resources {
    type                = "FARGATE"
    max_vcpus           = 4
    subnets             = data.aws_subnets.default.ids
    security_group_ids  = [data.aws_security_group.default.id]
  }
}

# 3. Job Queue
resource "aws_batch_job_queue" "fargate_queue" {
  name                 = "yahoo_terraform_job_queue"
  state                = "ENABLED"
  priority             = 1

  compute_environment_order {
    order               = 1
    compute_environment = aws_batch_compute_environment.fargate_env.arn
  }
}

# 4. Job Definition
resource "aws_batch_job_definition" "python_app_job" {
  name = "yahoo_terraform_job_definition"
  type = "container"

  platform_capabilities = ["FARGATE"]
  
  # Ensure the docker push happens before the job definition is created
  depends_on = [null_resource.docker_push]

  container_properties = jsonencode({
    image = "${aws_ecr_repository.python_app.repository_url}:latest"
    resourceRequirements = [
      { type = "VCPU", value = "2" },
      { type = "MEMORY", value = "4096" }
    ]
    # Reference the same existing role ARN
    executionRoleArn = data.aws_iam_role.existing_batch_role.arn

    networkConfiguration = {
      assignPublicIp = "ENABLED"
    }

    environment = [
      { name  = "AWS_ACCESS_KEY_ID", value = local.finance_secrets["AWS_ACCESS_KEY"]},
      { name  = "AWS_SECRET_ACCESS_KEY", value = local.finance_secrets["AWS_SECRET_ACCESS_KEY"]}
    ]
    fargatePlatformConfiguration = { platformVersion = "LATEST" }
    runtimePlatform = {
      operatingSystemFamily = "LINUX"
      cpuArchitecture       = "X86_64"
    }
  })
}
