#-------------------------------------------------------------------------------------------------------------------------------------------
# S3 Bucket
#-------------------------------------------------------------------------------------------------------------------------------------------
resource "aws_s3_bucket" "tfe_app" {
  bucket = "${var.friendly_name_prefix}-tfe-app-${data.aws_region.current.name}-${data.aws_caller_identity.current.account_id}"
  acl    = "private"

  versioning {
    enabled = true
  }

  dynamic "server_side_encryption_configuration" {
    for_each = length([var.kms_key_arn]) == 0 ? [] : [var.kms_key_arn]

    content {
      rule {
        apply_server_side_encryption_by_default {
          sse_algorithm     = "aws:kms"
          kms_master_key_id = var.kms_key_arn
        }
      }
    }
  }

  # --- S3 Cross-Region Replication --- #
  dynamic "replication_configuration" {
    for_each = length(keys(var.bucket_replication_configuration)) == 0 || var.is_secondary == true ? [] : [var.bucket_replication_configuration]

    content {
      role = aws_iam_role.s3_crr[0].arn

      dynamic "rules" {
        for_each = replication_configuration.value.rules

        content {
          id       = lookup(rules.value, "id", null)
          priority = lookup(rules.value, "priority", null)
          prefix   = lookup(rules.value, "prefix", null)
          status   = lookup(rules.value, "status", null)

          dynamic "destination" {
            for_each = length(keys(lookup(rules.value, "destination", {}))) == 0 ? [] : [lookup(rules.value, "destination", {})]

            content {
              bucket             = lookup(destination.value, "bucket", null)
              storage_class      = lookup(destination.value, "storage_class", null)
              replica_kms_key_id = lookup(destination.value, "replica_kms_key_id", null)
              account_id         = data.aws_caller_identity.current.account_id

              dynamic "access_control_translation" {
                for_each = length(keys(lookup(destination.value, "access_control_translation", {}))) == 0 ? [] : [lookup(destination.value, "access_control_translation", {})]

                content {
                  owner = access_control_translation.value.owner
                }
              }
            }
          }

          dynamic "source_selection_criteria" {
            for_each = length(keys(lookup(rules.value, "source_selection_criteria", {}))) == 0 ? [] : [lookup(rules.value, "source_selection_criteria", {})]

            content {
              dynamic "sse_kms_encrypted_objects" {
                for_each = length(keys(lookup(source_selection_criteria.value, "sse_kms_encrypted_objects", {}))) == 0 ? [] : [lookup(source_selection_criteria.value, "sse_kms_encrypted_objects", {})]

                content {
                  enabled = sse_kms_encrypted_objects.value.enabled
                }
              }
            }
          }

          dynamic "filter" {
            for_each = length(keys(lookup(rules.value, "filter", {}))) == 0 ? [] : [lookup(rules.value, "filter", {})]

            content {
              prefix = lookup(filter.value, "prefix", null)
              tags   = lookup(filter.value, "tags", null)
            }
          }

        }
      }
    }
  }

  tags = merge(
    { "Name" = "${var.friendly_name_prefix}-tfe-app-${data.aws_region.current.name}-${data.aws_caller_identity.current.account_id}" },
    { "Description" = "TFE object storage" },
    var.common_tags
  )
}

# resource "aws_s3_bucket_public_access_block" "tfe_app_bucket_block_public" {
#   bucket = aws_s3_bucket.tfe_app.id

#   block_public_acls       = true
#   block_public_policy     = true
#   restrict_public_buckets = true
#   ignore_public_acls      = true

#   depends_on = [aws_s3_bucket.tfe_app]
# }

#-------------------------------------------------------------------------------------------------------------------------------------------
# S3 Cross-Region Replication IAM
#-------------------------------------------------------------------------------------------------------------------------------------------
resource "aws_iam_role" "s3_crr" {
  count = length(keys(var.bucket_replication_configuration)) > 0 && var.is_secondary == false ? 1 : 0
  
  name = "${var.friendly_name_prefix}-tfe-s3-crr-iam-role-${data.aws_region.current.name}"
  path = "/"

  assume_role_policy = <<POLICY
{
    "Version": "2012-10-17",
    "Statement": [
      {
        "Sid": "",
        "Effect": "Allow",
        "Principal": {
          "Service": "s3.amazonaws.com"
        },
        "Action": "sts:AssumeRole"
      }
    ]
  }
POLICY

  tags = merge(
    { Name = "${var.friendly_name_prefix}-tfe-s3-crr-iam-role" },
    var.common_tags
  )
}

resource "aws_iam_policy" "s3_crr" {
  count = length(keys(var.bucket_replication_configuration)) > 0 && var.is_secondary == false ? 1 : 0

  name = "${var.friendly_name_prefix}-tfe-s3-crr-iam-policy-${data.aws_region.current.name}"

  policy = <<POLICY
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Action": [
        "s3:GetReplicationConfiguration",
        "s3:ListBucket"
      ],
      "Effect": "Allow",
      "Resource": [
        "${aws_s3_bucket.tfe_app.arn}"
      ]
    },
    {
      "Action": [
        "s3:GetObjectVersion",
        "s3:GetObjectVersionAcl"
      ],
      "Effect": "Allow",
      "Resource": [
        "${aws_s3_bucket.tfe_app.arn}/*"
      ]
    },
    {
      "Action": [
        "s3:ReplicateObject",
        "s3:ReplicateDelete"
      ],
      "Effect": "Allow",
      "Resource": "arn:aws:s3:::${var.destination_bucket}/*"
    }
  ]
}
POLICY
}

resource "aws_iam_policy_attachment" "s3_crr" {
  count = length(keys(var.bucket_replication_configuration)) > 0 && var.is_secondary == false ? 1 : 0

  name       = "${var.friendly_name_prefix}-tfe-s3-crr-iam-policy-attach-${data.aws_region.current.name}"
  roles      = [aws_iam_role.s3_crr[0].name]
  policy_arn = aws_iam_policy.s3_crr[0].arn
}