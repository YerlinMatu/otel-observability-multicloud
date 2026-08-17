terraform {
  required_version = ">= 1.6"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.region
}

variable "region" {
  type    = string
  default = "us-east-1"
}
variable "vpc_id" {
  type = string
}
variable "private_subnets" {
  type = list(string)
}
variable "service_a_image" {
  type = string
}
variable "service_b_image" {
  type = string
}

resource "aws_ecs_cluster" "this" {
  name = "otel-lab"
}

resource "aws_cloudwatch_log_group" "app" {
  name              = "/otel/microservices"
  retention_in_days = 7
}

resource "aws_security_group" "ecs" {
  name   = "otel-lab-ecs"
  vpc_id = var.vpc_id

  ingress {
    from_port = 0
    to_port   = 65535
    protocol  = "tcp"
    self      = true
  }
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

data "aws_iam_policy_document" "assume" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["ecs-tasks.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "task" {
  name               = "otel-lab-task"
  assume_role_policy = data.aws_iam_policy_document.assume.json
}

resource "aws_iam_role_policy_attachment" "execution" {
  role       = aws_iam_role.task.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}
resource "aws_iam_role_policy_attachment" "xray" {
  role       = aws_iam_role.task.name
  policy_arn = "arn:aws:iam::aws:policy/AWSXRayDaemonWriteAccess"
}
resource "aws_iam_role_policy_attachment" "cloudwatch" {
  role       = aws_iam_role.task.name
  policy_arn = "arn:aws:iam::aws:policy/CloudWatchAgentServerPolicy"
}

locals {
  log_config = {
    logDriver = "awslogs"
    options = {
      awslogs-group         = aws_cloudwatch_log_group.app.name
      awslogs-region        = var.region
      awslogs-stream-prefix = "ecs"
    }
  }
}

resource "aws_ecs_task_definition" "app" {
  family                   = "otel-lab"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = 1024
  memory                   = 2048
  execution_role_arn       = aws_iam_role.task.arn
  task_role_arn            = aws_iam_role.task.arn

  container_definitions = jsonencode([
    {
      name         = "service-a"
      image        = var.service_a_image
      essential    = true
      portMappings = [{ containerPort = 8080 }]
      environment = [
        { name = "SERVICE_NAME", value = "service-a" },
        { name = "SERVICE_B_URL", value = "http://127.0.0.1:8081" },
        { name = "OTEL_EXPORTER_OTLP_ENDPOINT", value = "http://127.0.0.1:4317" }
      ]
      logConfiguration = local.log_config
    },
    {
      name         = "service-b"
      image        = var.service_b_image
      essential    = true
      portMappings = [{ containerPort = 8081 }]
      environment = [
        { name = "SERVICE_NAME", value = "service-b" },
        { name = "OTEL_EXPORTER_OTLP_ENDPOINT", value = "http://127.0.0.1:4317" }
      ]
      logConfiguration = local.log_config
    },
    {
      name      = "otel-collector"
      image     = "public.ecr.aws/aws-observability/aws-otel-collector:latest"
      essential = true
      command   = ["--config=env:OTEL_CONFIG"]
      environment = [
        { name = "AWS_REGION", value = var.region },
        { name = "OTEL_CONFIG", value = file("${path.module}/../../otel/collector-aws.yaml") }
      ]
      logConfiguration = local.log_config
    }
  ])
}

resource "aws_ecs_service" "app" {
  name            = "otel-lab"
  cluster         = aws_ecs_cluster.this.id
  task_definition = aws_ecs_task_definition.app.arn
  desired_count   = 2
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = var.private_subnets
    security_groups  = [aws_security_group.ecs.id]
    assign_public_ip = false
  }
}
