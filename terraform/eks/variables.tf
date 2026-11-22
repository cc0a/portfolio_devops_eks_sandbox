
variable "aws_region" {
  description = "AWS deployment region"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Deployment environment"
  type        = string
  default     = "dev"
}

variable "cluster_name" {
  description = "EKS cluster name"
  type        = string
  default     = "cloud-incident-manager-eks"
}

variable "kubernetes_version" {
  description = "Kubernetes version for EKS"
  type        = string
  default     = "1.37"
}

variable "admin_cidrs" {
  description = "Public IPv4 CIDR ranges allowed to access the EKS API"
  type        = list(string)

  validation {
    condition = (
      length(var.admin_cidrs) > 0 &&
      alltrue([
        for cidr in var.admin_cidrs :
        can(cidrnetmask(cidr))
      ])
    )
    error_message = "Provide at least one valid IPv4 CIDR, preferably your public IP with a /32 mask."
  }
}
