variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "repo_name" {
  description = "Name of the ECR repository"
  type        = string
  default     = "my-python-app"
}

variable "bucket_name" {
  description = "Name of the S3 Bucket"
  type        = string
  default     = "bucket-name"
}
