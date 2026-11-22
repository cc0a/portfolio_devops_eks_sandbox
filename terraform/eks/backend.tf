terraform {
  backend "s3" {
    bucket       = "cloud-incident-manager-tfstate-795734304267"
    key          = "portfolio-devops-eks-sandbox/dev/terraform.tfstate"
    region       = "us-east-1"
    encrypt      = true
    use_lockfile = true
  }
}
