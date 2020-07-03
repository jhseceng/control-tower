import boto3
import os
import logging
import requests
import json

# Set up our logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)

SUCCESS = "SUCCESS"
FAILED = "FAILED"


def cfnresponse_send(event, context, responseStatus, physicalResourceId=None, noEcho=False):
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
        # SecretList = json.loads(get_secret('FalconSecret'))
        # FalconClientId = SecretList['FalconClientId']
        # FalconSecret = SecretList['FalconSecret']
        # logger.info('FalconClientId {}'.format(FalconClientId))
        # logger.info('FalconSecret {}'.format(FalconSecret))
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




def lambda_handler(event, context):
    logger.info('Got event {}'.format(event))
    try:
        response_data = {}
        if event['RequestType'] in ['Create']:
            event_data = event['ResourceProperties']
            log_archive_acct = event_data['log_archive_acct']
            region = event_data['region']
            bucket = event_data['log_archive_bucket']
            crwd_topic_arn = event_data['crwd_topic_arn']

            s3 = boto3.resource('s3')
            bucket_notification = s3.BucketNotification(bucket)
            print(bucket_notification)

            response = bucket_notification.put(
                NotificationConfiguration={
                    'TopicConfigurations': [
                        {
                            'Id': 'string',
                            'TopicArn': crwd_topic_arn,
                            'Events': ['s3:ObjectCreated:Put'
                                       ],
                        },
                    ]})
            logger.info('Response to bucket notification add {}'.format(response))
            if response['ResponseMetadata']['HTTPStatusCode'] == 200:
                cfnresponse_send(event, context, SUCCESS, "CustomResourcePhysicalID")
            else:
                cfnresponse_send(event, context, FAILED, "CustomResourcePhysicalID")
        elif event['RequestType'] in ['Delete']:
            cfnresponse_send(event, context, SUCCESS, "CustomResourcePhysicalID")
        else:
            cfnresponse_send(event, context, SUCCESS, "CustomResourcePhysicalID")
    except Exception as e:
        logger.info('Got exception {}'.format(e))
        cfnresponse_send(event, context, FAILED, "CustomResourcePhysicalID")
    return "Created notification"
