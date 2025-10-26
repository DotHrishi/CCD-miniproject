variable "aws_region" {
  description = "AWS region"
  type = string
  default = "us-east-1"
}

variable "s3_bucket_name" {
  description = "Bucket name for file storage"
  type = string
  default = "file-share-bucket-demo-12345"
}
