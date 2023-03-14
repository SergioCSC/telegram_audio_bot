import lambda_function

chat_id = 534111842

# body_start = '{\"update_id\":124257435,\n\"message\":{\"message_id\":439,\"from\":{\"id\":534111842,\"is_bot\":false,\"first_name\":\"Sergio\",\"username\":\"n_log_n\",\"language_code\":\"en\"},\"chat\":{\"id\":'
# body_middle = ',\"title\":\"Test Group for bots\",\"type\":\"supergroup\"},\"date\":1674068886,\"text\":\"'
# body_finish = '\",\"entities\":[{\"offset\":0,\"length\":2,\"type\":\"bot_command\"}]}}'

# body = f'{body_start}{chat_id}{body_middle}{command}{body_finish}'
body_voice_start = '{\"update_id\":124257435,\n\"message\":{\"message_id\": 77, \"from\": {\"id\": 534111842, \"is_bot\": false, \"first_name\": \"Serg!o\", \"username\": \"n_log_n\", \"language_code\": \"en\"}, \"chat\": {\"id\": 534111842, \"first_name\": \"Serg!o\", \"username\": \"n_log_n\", \"type\": \"private\"}, \"date\": 1678696679, \"voice\": {\"duration\": 1, \"mime_type\": \"audio/ogg\", \"file_id\": \"'
file_id = 'AwACAgIAAxkBAAOZZA-9aRfvV3CgE1iv7wABFJqCMwlHAAJiJgACGfiASELKuglq638QLwQ'
body_voice_finish = '\", \"file_unique_id\": \"AgADOyEAAvOheEg\", \"file_size\": 2164}}}'

body_voice = f'{body_voice_start}{file_id}{body_voice_finish}'

event = \
{
    "version": "1.0",
    "resource": "/kobuleti_weather",
    "path": "/default/kobuleti_weather",
    "httpMethod": "POST",
    "headers": {
        "Content-Length": "323",
        "Content-Type": "application/json",
        "Host": "1ykm8geil9.execute-api.us-east-1.amazonaws.com",
        "X-Amzn-Trace-Id": "Root=1-63c84418-1cdec56523ada7094cd8702d",
        "X-Forwarded-For": "91.108.6.97",
        "X-Forwarded-Port": "443",
        "X-Forwarded-Proto": "https",
        "accept-encoding": "gzip, deflate"
    },
    "multiValueHeaders": {
        "Content-Length": ["323"],
        "Content-Type": ["application/json"],
        "Host": ["1ykm8geil9.execute-api.us-east-1.amazonaws.com"],
        "X-Amzn-Trace-Id": ["Root=1-63c84418-1cdec56523ada7094cd8702d"],
        "X-Forwarded-For": ["91.108.6.97"],
        "X-Forwarded-Port": ["443"],
        "X-Forwarded-Proto": ["https"],
        "accept-encoding": ["gzip, deflate"]
    },
    "queryStringParameters": "None",
    "multiValueQueryStringParameters": "None",
    "requestContext": {
        "accountId": "145384694416",
        "apiId": "1ykm8geil9",
        "domainName": "1ykm8geil9.execute-api.us-east-1.amazonaws.com",
        "domainPrefix": "1ykm8geil9",
        "extendedRequestId": "e8-T6jzPIAMEVrw=",
        "httpMethod": "POST",
        "identity": {
            "accessKey": "None",
            "accountId": "None",
            "caller": "None",
            "cognitoAmr": "None",
            "cognitoAuthenticationProvider": "None",
            "cognitoAuthenticationType": "None",
            "cognitoIdentityId": "None",
            "cognitoIdentityPoolId": "None",
            "principalOrgId": "None",
            "sourceIp": "91.108.6.97",
            "user": "None",
            "userAgent": "",
            "userArn": "None"
        },
        "path": "/default/kobuleti_weather",
        "protocol": "HTTP/1.1",
        "requestId": "e8-T6jzPIAMEVrw=",
        "requestTime": "18/Jan/2023:19:10:16 +0000",
        "requestTimeEpoch": 1674069016865,
        "resourceId": "ANY /kobuleti_weather",
        "resourcePath": "/kobuleti_weather",
        "stage": "default"
    },
    "pathParameters": "None",
    "stageVariables": "None",
    "body": body_voice,
    "isBase64Encoded": "False"
}

print(lambda_function.lambda_handler(event, None))