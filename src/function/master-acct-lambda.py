


import boto3


def lambda_handler(context, event):
    region = "eu-west-1"
    bucket="aws-controltower-logs-004881111746-eu-west-1"
    crwd_topic_arn = "arn:aws:sns:eu-west-1:292230061137:cs-cloudconnect-aws-cloudtrail"
    log_archive_acct = "004881111746"
    sts_connection = boto3.client('sts')
    acct_b = sts_connection.assume_role(
        RoleArn="arn:aws:iam::"+log_archive_acct+":role/aws-controltower-AdministratorExecutionRole",
        RoleSessionName="cross_acct_lambda"
    )
    print(acct_b)
    ACCESS_KEY = acct_b['Credentials']['AccessKeyId']
    SECRET_KEY = acct_b['Credentials']['SecretAccessKey']
    SESSION_TOKEN = acct_b['Credentials']['SessionToken']

    # create service client using the assumed role credentials, e.g. S3
    client = boto3.client(
        's3',
        aws_access_key_id=ACCESS_KEY,
        aws_secret_access_key=SECRET_KEY,
        aws_session_token=SESSION_TOKEN,
    )


    s3 = boto3.resource('s3',
        aws_access_key_id = ACCESS_KEY,
        aws_secret_access_key = SECRET_KEY,
        aws_session_token = SESSION_TOKEN,
    )
    bucket_notification = s3.BucketNotification('bucket_name')

    response = bucket_notification.put(
        NotificationConfiguration={
            'TopicConfigurations': [
                {
                    'Id': 'string',
                    'TopicArn': crwd_topic_arn,
                    'Events': ['s3:ObjectCreated:Put',
                               's3:ObjectCreated:CompleteMultipartUpload'
                    ],
                },
            ]})
    return "Created notification"