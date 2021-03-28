resource "aws_db_subnet_group" "tfe_rds_subnet_group" {
  name       = "${var.friendly_name_prefix}-tfe-db-subnet-group"
  subnet_ids = var.rds_subnet_ids

  tags = merge(
    { "Name" = "${var.friendly_name_prefix}-tfe-db-subnet-group" },
    { "Description" = "Subnets for TFE PostgreSQL RDS instance" },
    var.common_tags
  )
}

resource "aws_rds_global_cluster" "tfe" {
  count = var.is_secondary == true ? 0 : 1

  global_cluster_identifier = "${var.friendly_name_prefix}-tfe-rds-global-cluster"
  database_name             = var.rds_database_name
  deletion_protection       = false
  engine                    = var.rds_engine
  engine_version            = var.rds_engine_version
  storage_encrypted         = var.kms_key_arn != "" ? true : false
}

resource "aws_rds_cluster" "tfe" {
  global_cluster_identifier       = var.is_secondary == true ? var.rds_global_cluster_id : aws_rds_global_cluster.tfe[0].id
  cluster_identifier              = "${var.friendly_name_prefix}-tfe-rds-cluster-${data.aws_region.current.name}"
  engine                          = var.rds_engine
  engine_mode                     = var.rds_engine_mode
  engine_version                  = var.rds_engine_version
  database_name                   = var.is_secondary == true ? null : var.rds_database_name
  availability_zones              = var.rds_availability_zones
  db_subnet_group_name            = aws_db_subnet_group.tfe_rds_subnet_group.id
  db_cluster_parameter_group_name = aws_rds_cluster_parameter_group.tfe.id
  port                            = 5432
  master_username                 = var.is_secondary == true ? null : var.rds_master_username
  master_password                 = var.is_secondary == true ? null : var.rds_master_password
  storage_encrypted               = var.kms_key_arn != "" ? true : false
  kms_key_id                      = var.kms_key_arn
  vpc_security_group_ids          = [aws_security_group.tfe_rds_allow.id]
  replication_source_identifier   = var.is_secondary == true ? var.rds_replication_source_identifier : null
  source_region                   = var.is_secondary == false ? null : var.source_region
  backup_retention_period         = var.rds_backup_retention_period
  preferred_backup_window         = var.rds_preferred_backup_window
  preferred_maintenance_window    = var.rds_preferred_maintenance_window
  skip_final_snapshot             = var.rds_skip_final_snapshot

  tags = merge(
    { "Name" = "${var.friendly_name_prefix}-tfe-rds-cluster-${data.aws_region.current.name}" },
    { "Description" = "TFE RDS Aurora PostgreSQL database cluster" },
    { "Is_Secondary" = var.is_secondary },
    var.common_tags
  )

  lifecycle {
    ignore_changes = [replication_source_identifier]
  }
}

resource "aws_rds_cluster_instance" "tfe" {
  count = var.rds_replica_count + 1

  identifier              = "${var.friendly_name_prefix}-tfe-rds-cluster-instance-${count.index}"
  cluster_identifier      = aws_rds_cluster.tfe.id
  instance_class          = var.rds_instance_class
  engine                  = aws_rds_cluster.tfe.engine
  engine_version          = aws_rds_cluster.tfe.engine_version
  db_parameter_group_name = aws_db_parameter_group.tfe.id
  apply_immediately       = true
  publicly_accessible     = false

  tags = merge(
    { "Name" = "${var.friendly_name_prefix}-tfe-rds-cluster-instance-${count.index}" },
    { "Description" = "TFE RDS Aurora PostgreSQL DB cluster instance" },
    { "Is_Secondary" = var.is_secondary },
    var.common_tags
  )

  depends_on = [aws_rds_cluster.tfe]
}

resource "aws_rds_cluster_parameter_group" "tfe" {
  name        = "${var.friendly_name_prefix}-tfe-rds-cluster-parameter-group-${data.aws_region.current.name}"
  family      = "aurora-postgresql11"
  description = "TFE RDS Aurora PostgreSQL DB cluster parameter group"
}

resource "aws_db_parameter_group" "tfe" {
  name        = "${var.friendly_name_prefix}-tfe-rds-db-parameter-group-${data.aws_region.current.name}"
  family      = "aurora-postgresql11"
  description = "TFE RDS Aurora PostgreSQL DB instance parameter group"
}
