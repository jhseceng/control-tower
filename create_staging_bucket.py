# Uploads files to an S3 bucket for staging
#
# Usage python3 create_staging_bucket.py
# -b <S3 Bucket Name> Optional will default to 'crowdstrike-staging-<account>-account-xyz'
# -r region
# -a account where the bucket will be created, choices=['control-tower', 'log-archive'],
#

import os
import sys
import boto3
import logging
import argparse
import string
import random
import time
from logging.handlers import RotatingFileHandler
from botocore.exceptions import ClientError



def create_bucket(bucket_name, region):
    """Create an S3 bucket in a specified region

    If a region is not specified, the bucket is created in the S3 default
    region (us-east-1).

    :param bucket_name: Bucket to create
    :param region: String region to create bucket in, e.g., 'us-west-2'
    :return: True if bucket created, else False
    """

    print('Creating bucket:')
    try:
        s3_client = boto3.client('s3', region_name=region,verify=False)
        location = {'LocationConstraint': region}
        s3_client.create_bucket(Bucket=bucket_name,CreateBucketConfiguration=location)
    except ClientError as e:
        print('Error creating bucket {}'.format(ClientError))
        sys.exit(1)
    return True

def bucket_exists(bucket_name,region):
    """
    Checks that the S3 bucket exists in the region
    :param bucket_name: The name of the S3 bucket
    :param region:
    :return: True or False
    """
    s3_client = boto3.client('s3', region_name=region,verify=False)
    try:
        response = s3_client.list_buckets()
    except ClientError as e:
        print('Error listing buckets {}'.format(e))
        sys.exit(1)

    # Output True if bucket exists

    for bucket in response['Buckets']:
        if bucket_name ==  bucket["Name"]:
            print('Bucket already exists')
            return True
    return False


def get_random_alphanum_string(stringLength=5) -> string:
    """
    Returns a random string
    :param stringLength:
    :return: string
    """
    lettersAndDigits = string.ascii_letters + string.digits
    return ''.join((random.choice(lettersAndDigits) for i in range(stringLength)))

def upload_dir(dir, bucket):
    """
    :param dir:
    :param bucket:
    :return:
    """
    files = os.listdir(dir)
    for filename in files:
        filepath = dir+'/'+filename
        upload_file(filepath, bucket, filename)

def upload_file(file_name, bucket, object_name=None):
    """Upload a file to an S3 bucket

    :param file_name: File to upload
    :param bucket: Bucket to upload to
    :param object_name: S3 object name. If not specified then file_name is used
    :return: True if file was uploaded, else False
    """
    # If S3 object_name was not specified, use file_name
    if object_name is None:
        object_name = file_name

    # Upload the file
    s3_client = boto3.client('s3')

    try:
        start_time = time.time()
        print('Uploading file {}:'.format(file_name))
        content = open(file_name, 'rb')
        s3_client.put_object(
            Bucket=bucket,
            Key=object_name,
            Body=content
        )
        print("Successfully finished uploading file to s3 bucket. Time {}s".format(
            time.time() - start_time))
    except Exception as e:
        print('File Upload error {}'.format(e))
        sys.exit(1)
    return True



def main():
    if account == 'log-archive':
        account_prefix = 'log-archive'
    else:
        account_prefix = 'control-tower'
    if not bucket_exists(s3bucket,region):
        create_bucket(s3bucket, region)
    upload_dir(account_prefix, s3bucket)



if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Get Params to create lambda bucket')
    parser.add_argument('-r', '--aws_region', help='AWS Region', required=True)
    parser.add_argument('-b', '--s3bucket', help='<S3 Bucket Name> Optional will default to "crowdstrike-staging-<account>-account-xyz" ')
    parser.add_argument('-a', '--account', choices=['control-tower', 'log-archive'],
                        required=True, help="Account where the bucket will be created, choices=['control-tower', 'log-archive'],")

    args = parser.parse_args()

    region = args.aws_region
    account = args.account
    if args.s3bucket:
        s3bucket = args.s3bucket
    else:
        s3bucket = 'crowdstrike-staging-' + args.account + '-account-' + get_random_alphanum_string(5).lower()
    main()




