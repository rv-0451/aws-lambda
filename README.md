#  Description

This is a simple deployment template you can follow to deploy your lambda. In this example the lambda function will bind the certificates with specific DNs to specified ALB listener.

# What to update

- Update lamdba ARN in `iam/lambda-invoke.policy.json`
- Update `my_lambda` function name with a desired one
- Update `my_lambda.py` code logic

# How to deploy

AWS CLI step-by-step approach.

### Policy + Role

```bash
aws iam create-role \
  --role-name lambda.role \
  --assume-role-policy-document file://iam/lambda.trust.json

aws aws iam put-role-policy \
  --role-name lambda.role \
  --policy-name lambda.policy \
  --policy-document file://iam/lambda.policy.json
```

### Prepare the archive

```bash
zip lambda.zip my_lambda.py
```

### Create lambda function, take the role ARN from the previous commands

```bash
aws lambda create-function \
  --function-name my_lambda \
  --runtime python3.8 \
  --role arn:aws:iam::123456789:role/lambda.role \
  --handler my_lambda.lambda_handler \
  --publish \
  --package-type Zip \
  --zip-file fileb://lambda.zip
```

### Policy + Group + User for invoking lambda

```bash
aws iam create-group \
  --group-name lambda-invokers.group

aws iam create-user \
  --user-name lambda-invoker.user

aws iam put-group-policy \
  --group-name lambda-invokers.group \
  --policy-name lambda-invoke.policy \
  --policy-document file://iam/lambda-invoke.policy.json

aws iam add-user-to-group \
  --group-name lambda-invokers.group \
  --user-name lambda-invoker.user
```

### Create access key for invoker user

```bash
aws iam create-access-key \
  --user-name lambda-invoker.user
```

### Invoke the lambda

```bash
aws lambda invoke \
  --function-name my_lambda \
  --payload file://event.json \
  --cli-binary-format raw-in-base64-out \
  invoke-result.json
```

# How to use this example

To invoke this lambda send a request with the following example payload `event.json`:

```json
{
    "region_name": "eu-central-1",
    "listener_arn": "arn:aws:elasticloadbalancing:eu-central-1:123456789:listener/app/k8s-nginx-albnginx-a1234e36b6/123d4567b4d7b770/12dba3456789d1c7",
    "new_dn_list": [
        "dn1.project.awscloud.internal.company.org",
        "dn2.project.awscloud.internal.company.org",
        "dn3.project.awscloud.internal.company.org",
        "dn4.project.awscloud.internal.company.org"
    ]
}
```

The successful response:

```json
{"statusCode": 200, "headers": {"Content-Type": "application/json"}, "body": "{\"Message\": \"Operation was successful\", \"Error\": \"\"}"}
```
