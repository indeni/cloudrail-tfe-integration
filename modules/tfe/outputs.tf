#------------------------------------------------------------------------------------------------------------------
# TFE URLs
#------------------------------------------------------------------------------------------------------------------
output "tfe_url" {
  value       = "https://${var.tfe_hostname}"
  description = "URL of TFE application based on `tfe_hostname` input."
}

output "tfe_admin_console_url" {
  value       = "https://${var.tfe_hostname}:8800"
  description = "URL of TFE (Replicated) Admin Console based on `tfe_hostname` input."
}

output "tfe_alb_dns_name" {
  value       = aws_lb.tfe_alb.dns_name
  description = "DNS name of AWS Application Load Balancer."
}

#------------------------------------------------------------------------------------------------------------------
# External Services
#------------------------------------------------------------------------------------------------------------------
output "s3_bucket_name" {
  value       = aws_s3_bucket.tfe_app.id
  description = "Name of TFE S3 bucket."
}

output "s3_bucket_arn" {
  value       = aws_s3_bucket.tfe_app.arn
  description = "Name of TFE S3 bucket."
}

output "rds_global_cluster_id" {
  value       = concat(aws_rds_global_cluster.tfe.*.id, [""])[0]
  description = "RDS Aurora Global Cluster identifier."
}

output "rds_cluster_arn" {
  value       = aws_rds_cluster.tfe.arn
  description = "ARN of RDS Aurora Cluster."
  depends_on  = [aws_rds_cluster_instance.tfe]
}

output "rds_cluster_members" {
  value       = aws_rds_cluster.tfe.cluster_members
  description = "List of RDS Instances that are part of this RDS Cluster."
  depends_on  = [aws_rds_cluster_instance.tfe]
}

output "s3_crr_iam_role_arn" {
  value       = concat(aws_iam_role.s3_crr.*.arn, [""])[0]
  description = "ARN of S3 Cross-Region Replication IAM Role."
}