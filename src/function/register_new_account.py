import json, os, boto3, base64
import logging
import string, random, sys
#from botocore.vendored import requests
import requests
import urllib3
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)
Falcon_Discover_Url = 'https://ctstagingireland.s3-eu-west-1.amazonaws.com/crowdstrike_role_creation_ss.yaml'

SUCCESS = "SUCCESS"
FAILED = "FAILED"

FalconDiscoverSecretsRoleArn = os.environ['FalconDiscoverSecretsRole']
cloudtrail_bucket_owner_id = os.environ['central_s3_bucket_account']
cloudtrail_bucket_region = os.environ['cloudtrail_bucket_region']
iam_role_arn = os.environ['iam_role_arn']
CSAccountNumber = os.environ['CSAccountNumber']
CSAssumingRoleName = os.environ['CSAssumingRoleName']
LocalAccount = os.environ['LocalAccount']


def get_sm_client():
    sts_connection = boto3.client('sts')
    acct_creds = sts_connection.assume_role(
        RoleArn=FalconDiscoverSecretsRoleArn,
        RoleSessionName="cross_acct_lambda"
    )

    ACCESS_KEY = acct_creds['Credentials']['AccessKeyId']
    SECRET_KEY = acct_creds['Credentials']['SecretAccessKey']
    SESSION_TOKEN = acct_creds['Credentials']['SessionToken']

    # create secretsmanager client
    session = boto3.session.Session()
    sm_client = session.client(
        'secretsmanager',
        aws_access_key_id=ACCESS_KEY,
        aws_secret_access_key=SECRET_KEY,
        aws_session_token=SESSION_TOKEN,
    )
    return sm_client


def register_falcon_discover_account(payload, api_keys) -> bool:
    cs_action = 'POST'
    url = "https://api.crowdstrike.com/cloud-connect-aws/entities/accounts/v1?mode=manual"
    auth_token = get_auth_token(api_keys)
    if auth_token:
        auth_header = get_auth_header(auth_token)
    else:
        print("Failed to auth token")
        sys.exit(1)
    headers = {
        'Content-Type': 'application/json',
    }
    headers.update(auth_header)

    try:
        response = requests.request(cs_action, url, headers=headers, data=payload)
        response_content = json.loads(response.text)
        logger.info('Response to register = {}'.format(response_content))

        good_exit = 201 if cs_action == 'POST' else 200
        if response.status_code == good_exit:
            logger.info('Account Registered')
            return True
        elif response.status_code == 409:
            logger.info('Account already registered - nothing to do')
            return True
        else:
            error_code = response.status_code
            error_msg = response_content["errors"][0]["message"]
            logger.info('Account {} Registration Failed - Response {} {}'.format(error_code, error_msg))
            return
    except Exception as e:

        logger.info('Got exception {}'.format(e))
        return


def get_auth_header(auth_token) -> str:
    if auth_token:
        auth_header = "Bearer " + auth_token
        headers = {
            "Authorization": auth_header
        }
        return headers


def get_auth_token(api_keys):

    FalconClientId = api_keys['FalconClientId']
    FalconSecret = api_keys['FalconSecret']
    url = "https://api.crowdstrike.com/oauth2/token"
    payload = 'client_secret=' + FalconSecret + '&client_id=' + FalconClientId
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    response = requests.request('POST', url, headers=headers, data=payload)
    if response.ok:
        response_object = (response.json())
        token = response_object.get('access_token', '')
        if token:
            return \
                token
    return


def format_notification_message(rate_limit_reqs=0, rate_limit_time=0):
    data = {
        "resources": [
            {
                "cloudtrail_bucket_owner_id": cloudtrail_bucket_owner_id,
                "cloudtrail_bucket_region": cloudtrail_bucket_region,
                "external_id": get_random_alphanum_string(),
                "iam_role_arn": iam_role_arn,
                "id": LocalAccount,
                # "rate_limit_reqs": "<integer>",
                # "rate_limit_time": "<long>"
            }
        ]
    }
    logger.info('Post Data {}'.format(data))
    message = json.dumps(data)
    return message


def cfnresponse_send(event, context, responseStatus, responseData, physicalResourceId=None, noEcho=False):
    responseUrl = event['ResponseURL']
    print(responseUrl)

    responseBody = {}
    responseBody['Status'] = responseStatus
    responseBody['Reason'] = 'See the details in CloudWatch Log Stream: ' + context.log_stream_name
    responseBody['PhysicalResourceId'] = physicalResourceId or context.log_stream_name
    responseBody['StackId'] = event['StackId']
    responseBody['RequestId'] = event['RequestId']
    responseBody['LogicalResourceId'] = event['LogicalResourceId']

    json_responseBody = json.dumps(responseBody)

    print("Response body:\n" + json_responseBody)

    headers = {
        'content-type': '',
        'content-length': str(len(json_responseBody))
    }

    try:
        response = requests.put(responseUrl,
                                data=json_responseBody,
                                headers=headers)
        print("Status code: " + response.reason)
    except Exception as e:
        print("send(..) failed executing requests.put(..): " + str(e))


def get_random_alphanum_string(stringLength=15):
    lettersAndDigits = string.ascii_letters + string.digits
    return ''.join((random.choice(lettersAndDigits) for i in range(stringLength)))


def lambda_handler(event, context):
    try:
        response_data = {}
        if event['RequestType'] in ['Create']:
            logger.info('Event = {}'.format(event))
            api_keys = event['ResourceProperties']

            # Format post message
            api_message = format_notification_message()
            # Register account
            register_result = register_falcon_discover_account(api_message, api_keys)
            logger.info('Account registration result: {}'.format(register_result))
            if register_result:
                cfnresponse_send(event, context, SUCCESS, register_result, "CustomResourcePhysicalID")
            else:
                cfnresponse_send(event, context, FAILED, register_result, "CustomResourcePhysicalID")

        elif event['RequestType'] in ['Update']:
            logger.info('Event = ' + event['RequestType'])

            cfnresponse_send(event, context, 'SUCCESS', response_data, "CustomResourcePhysicalID")

        elif event['RequestType'] in ['Delete']:
            logger.info('Event = ' + event['RequestType'])
            # TODO handle account deletion
            response_data["Status"] = "Success"
            cfnresponse_send(event, context, 'SUCCESS', response_data, "CustomResourcePhysicalID")

    except Exception as e:
        logger.error(e)
        response_data = {}
        response_data["Status"] = str(e)
        cfnresponse_send(event, context, 'FAILED', response_data, "CustomResourcePhysicalID")


