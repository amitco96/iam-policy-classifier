# ============================================================================
# ASSIGNMENT PROVIDED EXAMPLES
# ============================================================================

ASSIGNMENT_WEAK_POLICY = {
    "Version": "2022-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": "*",
            "Resource": "*"
        }
    ]
}

ASSIGNMENT_STRONG_POLICY = {
    "Version": "2022-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": "s3:DeleteObject",
            "Resource": "arn:aws:s3:::secure-bucket/*",
            "Condition": {
                "Bool": {"aws:MultiFactorAuthPresent": "true"}
            }
        }
    ]
}

# Assignment examples
ASSIGNMENT_POLICIES = [
    ASSIGNMENT_WEAK_POLICY,
    ASSIGNMENT_STRONG_POLICY
]


# ============================================================================
# EXTENDED TEST POLICIES
# ============================================================================

ADMIN_ACCESS_POLICY = {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": "*",
            "Resource": "*"
        }
    ]
}

PUBLIC_S3_READ_POLICY = {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": "*",
            "Action": "s3:GetObject",
            "Resource": "arn:aws:s3:::company-sensitive-data/*"
        }
    ]
}

S3_FULL_ACCESS_POLICY = {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": "s3:*",
            "Resource": "*"
        }
    ]
}

EC2_READONLY_SCOPED_POLICY = {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "ec2:Describe*",
                "ec2:Get*"
            ],
            "Resource": "arn:aws:ec2:us-east-1:123456789012:instance/*"
        }
    ]
}

DYNAMODB_LIMITED_POLICY = {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "dynamodb:GetItem",
                "dynamodb:Query"
            ],
            "Resource": "arn:aws:dynamodb:us-east-1:123456789012:table/UserData",
            "Condition": {
                "IpAddress": {
                    "aws:SourceIp": "203.0.113.0/24"
                }
            }
        }
    ]
}

S3_SECURE_READ_POLICY = {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": "s3:GetObject",
            "Resource": "arn:aws:s3:::financial-reports-2024/*",
            "Condition": {
                "Bool": {
                    "aws:MultiFactorAuthPresent": "true"
                },
                "IpAddress": {
                    "aws:SourceIp": ["10.0.0.0/16", "192.168.1.0/24"]
                }
            }
        }
    ]
}

# Extended policies
EXTENDED_POLICIES = [
    ADMIN_ACCESS_POLICY,
    PUBLIC_S3_READ_POLICY,
    S3_FULL_ACCESS_POLICY,
    EC2_READONLY_SCOPED_POLICY,
    DYNAMODB_LIMITED_POLICY,
    S3_SECURE_READ_POLICY
]
