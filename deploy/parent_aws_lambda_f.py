import json
import boto3
 
# Define the client to interact with AWS Lambda
client = boto3.client('lambda')
 
def lambda_handler(event,context):

    response = client.invoke(
        FunctionName = 'arn_of_your_main_lambda_function_here',
        InvocationType = 'Event',
        Payload = json.dumps(event)
    )
 
    return {'statusCode': 200, 'body': 'Success'}