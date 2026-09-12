terraform {
  required_version = ">= 1.5.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

variable "aws_region" {
  type        = string
  description = "AWS region for deployment"
  default     = "us-east-1"
}

variable "github_org" {
  type        = string
  description = "GitHub organization or username"
}

variable "github_repo" {
  type        = string
  description = "GitHub repository name"
}

variable "ecr_repo_name" {
  type        = string
  description = "Name of the ECR repository"
  default     = "cloud-native-service"
}

provider "aws" {
  region = variable.aws_region
}

# ------------------------------------------------------------------------------
# 1. GitHub OpenID Connect (OIDC) Identity Provider
# ------------------------------------------------------------------------------
# In AWS, only one GitHub OIDC provider is needed per AWS account.
# If already created, use data aws_iam_openid_connect_provider.
data "tls_certificate" "github" {
  url = "https://token.actions.githubusercontent.com/.well-known/openid-configuration"
}

resource "aws_iam_openid_connect_provider" "github" {
  url             = "https://token.actions.githubusercontent.com"
  client_id_list  = ["sts.amazonaws.com"]
  thumbprint_list = [data.tls_certificate.github.certificates[0].sha1_fingerprint]
}

# ------------------------------------------------------------------------------
# 2. Amazon ECR Repository
# ------------------------------------------------------------------------------
resource "aws_ecr_repository" "app" {
  name                 = variable.ecr_repo_name
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  encryption_configuration {
    encryption_type = "AES256"
  }
}

resource "aws_ecr_lifecycle_policy" "app_lifecycle" {
  repository = aws_ecr_repository.app.name

  policy = jsonencode({
    rules = [
      {
        rulePriority = 1
        description  = "Keep last 30 untagged images"
        selection = {
          tagStatus   = "untagged"
          countType   = "imageCountMoreThan"
          countNumber = 30
        }
        action = {
          type = "expire"
        }
      }
    ]
  })
}

# ------------------------------------------------------------------------------
# 3. IAM Role with GitHub OIDC Trust Policy
# ------------------------------------------------------------------------------
data "aws_iam_policy_document" "github_oidc_assume" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRoleWithWebIdentity"]

    principals {
      type        = "Federated"
      identifiers = [aws_iam_openid_connect_provider.github.arn]
    }

    condition {
      test     = "StringEquals"
      variable = "token.actions.githubusercontent.com:aud"
      values   = ["sts.amazonaws.com"]
    }

    # Strict scoping: only GitHub Actions from main branch of this repo can assume
    condition {
      test     = "StringLike"
      variable = "token.actions.githubusercontent.com:sub"
      values   = ["repo:${variable.github_org}/${variable.github_repo}:ref:refs/heads/main"]
    }
  }
}

resource "aws_iam_role" "github_actions_ecr" {
  name               = "github-actions-${variable.github_repo}-ecr-push"
  assume_role_policy = data.aws_iam_policy_document.github_oidc_assume.json
}

# ------------------------------------------------------------------------------
# 4. Least-Privilege IAM Policy for ECR Push
# ------------------------------------------------------------------------------
data "aws_iam_policy_document" "ecr_push_policy" {
  statement {
    sid    = "ECRAuthToken"
    effect = "Allow"
    actions = [
      "ecr:GetAuthorizationToken"
    ]
    resources = ["*"]
  }

  statement {
    sid    = "ECRImagePush"
    effect = "Allow"
    actions = [
      "ecr:BatchCheckLayerAvailability",
      "ecr:GetDownloadUrlForLayer",
      "ecr:BatchGetImage",
      "ecr:PutImage",
      "ecr:InitiateLayerUpload",
      "ecr:UploadLayerPart",
      "ecr:CompleteLayerUpload"
    ]
    resources = [aws_ecr_repository.app.arn]
  }
}

resource "aws_iam_role_policy" "github_actions_ecr_attach" {
  name   = "ECRPushPolicy"
  role   = aws_iam_role.github_actions_ecr.id
  policy = data.aws_iam_policy_document.ecr_push_policy.json
}

# ------------------------------------------------------------------------------
# Outputs to configure GitHub Variables
# ------------------------------------------------------------------------------
output "aws_role_to_assume_arn" {
  description = "Value to set as GitHub Variable: AWS_ROLE_TO_ASSUME"
  value       = aws_iam_role.github_actions_ecr.arn
}

output "aws_region" {
  description = "Value to set as GitHub Variable: AWS_REGION"
  value       = variable.aws_region
}

output "ecr_repository_name" {
  description = "Value to set as GitHub Variable: ECR_REPOSITORY"
  value       = aws_ecr_repository.app.name
}

output "ecr_repository_url" {
  description = "Full URL of the ECR repository"
  value       = aws_ecr_repository.app.repository_url
}
