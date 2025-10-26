resource "aws_s3_bucket" "file_share" {
  bucket = var.s3_bucket_name
  acl    = "private"
  tags = { Name = "file-share-bucket" }
}
# NOTE: This is a minimal example. For EKS and full infra use terraform-aws-modules/eks/aws.
