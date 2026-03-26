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
    dir_hash = sha256(join("", [for f in fileset(path.module, "src/*") : filebase64sha256(f)]))
    dockerfile_hash = filebase64sha256("${path.module}/Dockerfile")
  }

  provisioner "local-exec" {
    interpreter = ["PowerShell", "-Command"]
    command = <<-EOT
        $token = aws ecr get-login-password --region ${var.aws_region}
        docker login --username AWS --password $token ${aws_ecr_repository.python_app.repository_url}
      
        docker build -t ${aws_ecr_repository.python_app.repository_url}:latest .
        docker push ${aws_ecr_repository.python_app.repository_url}:latest
    EOT
  }
  depends_on = [aws_ecr_repository.python_app]
}


