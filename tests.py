import lambda_function


def get_event_from_chat_id_file_id(chat_id: int, file_id: str) -> dict:

    body_voice_0 = '{\"update_id\":0123456789,\n\"message\":{\"message_id\": 77, \"from\": {\"id\": 987654321, \"is_bot\": false, \"first_name\": \"Serg!o\", \"username\": \"n_log_n\", \"language_code\": \"en\"}, \"chat\": {\"id\": '
    body_voice_5 = ', \"first_name\": \"Serg!o\", \"username\": \"n_log_n\", \"type\": \"private\"}, \"date\": 123456789, \"voice\": {\"duration\": 1, \"mime_type\": \"audio/ogg\", \"file_id\": \"'
    body_voice_9 = '\", \"file_unique_id\": \"AgAAAAAAAAAAAAAAA\", \"file_size\": 2164}}}'

    body_voice = f'{body_voice_0}{chat_id}{body_voice_5}{file_id}{body_voice_9}'

    event = \
    {
        "version": "1.0",
        "resource": "",
        "path": "/default",
        "httpMethod": "POST",
        "headers": {
            "Content-Length": "323",
            "Content-Type": "application/json",
            "Host": ".execute-api.us-east-1.amazonaws.com",
            "X-Amzn-Trace-Id": "Root=1-1111111-222222222222222",
            "X-Forwarded-For": "91.108.6.97",
            "X-Forwarded-Port": "443",
            "X-Forwarded-Proto": "https",
            "accept-encoding": "gzip, deflate"
        },
        "multiValueHeaders": {
            "Content-Length": ["323"],
            "Content-Type": ["application/json"],
            "Host": ["execute-api.us-east-1.amazonaws.com"],
            "X-Amzn-Trace-Id": ["Root=1-11111111-2222222222222"],
            "X-Forwarded-For": ["91.108.6.97"],
            "X-Forwarded-Port": ["443"],
            "X-Forwarded-Proto": ["https"],
            "accept-encoding": ["gzip, deflate"]
        },
        "queryStringParameters": "None",
        "multiValueQueryStringParameters": "None",
        "requestContext": {
            "accountId": "145384694416",
            "apiId": "",
            "domainName": ".execute-api.us-east-1.amazonaws.com",
            "domainPrefix": "",
            "extendedRequestId": "=",
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
            "path": "/default",
            "protocol": "HTTP/1.1",
            "requestId": "e8-=",
            "requestTime": "1/Jan/2222:00:00:00 +0000",
            "requestTimeEpoch": 1111111111,
            "resourceId": "ANY ",
            "resourcePath": "",
            "stage": "default"
        },
        "pathParameters": "None",
        "stageVariables": "None",
        "body": body_voice,
        "isBase64Encoded": "False"
    }
    
    return event


def test_1():
    chat_id = 534111842
    file_id = 'AwACAgIAAxkBAAOjZBAQaRzy2C_s43Hw2iyBMNCBxKgAAuwmAAIZ-IBIgJACXptgfmAvBA'
    
    event = get_event_from_chat_id_file_id(chat_id, file_id)
    parsed_chat_id, text = lambda_function._get_chat_id_and_text(event)
    assert chat_id == parsed_chat_id
    assert text == 'Проверка расшифровки'


def test_2():
    chat_id = 534111842
    file_id = 'AwACAgIAAxkBAAOXZA-7de2FoOIamPJLYCJICOAkyw4AAmAmAAIZ-IBI1p4117ajKzgvBA'
    
    event = get_event_from_chat_id_file_id(chat_id, file_id)
    parsed_chat_id, text = lambda_function._get_chat_id_and_text(event)
    assert chat_id == parsed_chat_id
    assert text == 'Субтитры делал DimaTorzok'


if __name__ == '__main__':
    test_1()
    test_2()