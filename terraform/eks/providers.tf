
provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "portfolio-devops-eks-sandbox"
      Environment = var.environment
      ManagedBy   = "Terraform"
    }
  }
}