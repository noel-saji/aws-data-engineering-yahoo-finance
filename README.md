# Financial Data Engineering Pipeline

## Project Description
This project implements a scalable **end-to-end data pipeline** that automates the extraction of financial market data using the **Yahoo Finance API**. The architecture follows a modern data lake pattern where raw data is ingested into **AWS S3**, processed, and stored in a transformed layer. Infrastructure is managed as code using **Terraform**, while **Docker** ensures a consistent environment for the data ingestion logic.

---

## 1. Prerequisites
Before setting up the project, ensure you have the following installed and configured:

*   **AWS Account**: An active [AWS Free Tier](https://aws.amazon.com) or professional account.
*   **AWS CLI**: Installed and configured with your local machine. Refer to the [AWS CLI Setup Guide](https://docs.aws.amazon.com).
*   **Terraform**: Version 1.0 or higher. [Download Terraform](https://www.terraform.io).
*   **Docker**: Ensure Docker is installed and running. [Docker Desktop](https://www.docker.com).
*   **Yahoo API**: Ensure you signup and retrieve Yahoo API key from [Yahoo API](https://financeapi.net/).

---

## 2. Initialisation

> [!IMPORTANT]
> **Manual AWS Setup Tasks**
> The following steps must be completed in the [AWS Management Console](https://console.aws.amazon.com) before running the automation scripts.

### IAM Configuration
1.  **Create IAM User**: From your **Root Account**, create a new IAM user.
2.  **Permissions**: Attach the `AdministratorAccess` policy to this user.
3.  **Security Credentials**: Generate an **Access Key** and **Secret Access Key**. Save these locally for CLI configuration.

### Secrets Management
Navigate to [AWS Secrets Manager](https://aws.amazon.com) and create a secret containing the following keys:
*   `AWS_Access_key`
*   `AWS_Secrets`
*   `Yahoo_API`

### Storage Layer
Create an **S3 Bucket** (e.g., `my-data-engineering-project`) and manually create the following folder structure:
*   `raw/`
*   `transformed/`
  
> [!IMPORTANT]
> **Change Bucket name inside raw_script and transforned scripts(Python)**
> After creating S3 bucket Name, Copy this Bucket name and paste it inside raw and transformed script files on Bucket names initialised
---

## 3. Deployment & Execution

### Pull the Repository
Clone the project to your local environment:
```bash
cd data-engineering-project
git clone https://github.com/noel-saji/aws-data-engineering-yahoo-finance.git
```

## 🛠 4. Infrastructure as Code (IaC)

This project leverages **Terraform** to provision and manage cloud resources consistently. All configuration files are housed within the `/terraform` directory.

### 📁 Directory Structure

```text
terraform/
├── main.tf            # S3, IAM, and Security definitions
├── variables.tf       # Input variables
├── providers.tf       # AWS provider configuration
└── outputs.tf         # Key resource IDs (Bucket names, etc.)
```


---

## 🚀 Deployment Workflow

### 1️⃣ Initialize

Download the required AWS provider and initialize Terraform:

```bash
terraform init
```
### 2️⃣ Plan

Preview the changes Terraform will apply to your infrastructure:

```bash
terraform plan
```

### 3️⃣ Apply

Deploy the resources to AWS:

```bash
terraform apply
```

## 🧹 5. Cleanup

To delete all provisioned AWS resources and prevent unnecessary costs:

```bash
terraform destroy
```
