provider "aws" {
  region = var.aws_region # <--- VARIABLE USED HERE
}

resource "aws_ecr_repository" "python_app" {
  name                 = var.repo_name # <--- VARIABLE USED HERE
  image_tag_mutability = "MUTABLE"
  force_delete         = true

  image_scanning_configuration {
    scan_on_push = true
  }
}

data "aws_ecr_authorization_token" "token" {}

resource "null_resource" "docker_push" {
  triggers = {
    dockerfile_hash = filebase64sha256("${path.module}/Dockerfile")
    token_expiry    = data.aws_ecr_authorization_token.token.expires_at
  }

  provisioner "local-exec" {
    interpreter = ["PowerShell", "-Command"]
    command = <<-EOT
        aws ecr get-login-password --region ${data.aws_ecr_authorization_token.token.region} | docker login --username AWS --password-stdin ${aws_ecr_repository.python_app.repository_url}
      
        docker build -t ${aws_ecr_repository.python_app.repository_url}:latest .
      
        docker push ${aws_ecr_repository.python_app.repository_url}:latest
    EOT
  }

  depends_on = [aws_ecr_repository.python_app]
}


