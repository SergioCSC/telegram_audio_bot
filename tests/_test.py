import os
import sys

sys.path.append(os.path.abspath('.'))
import lambda_function


TEST_CHAT_ID = -1


def test_1():  # very short voice
    file_id = 'AwACAgIAAxkBAAOXZA-7de2FoOIamPJLYCJICOAkyw4AAmAmAAIZ-IBI1p4117ajKzgvBA'
    
    message = get_message_from_file_id(file_id)
    _, text = lambda_function._get_chat_id_and_text(message)
    assert text == 'Субтитры делал DimaTorzok'


def test_2():  # short voice with certain text
    file_id = 'AwACAgIAAxkBAAOjZBAQaRzy2C_s43Hw2iyBMNCBxKgAAuwmAAIZ-IBIgJACXptgfmAvBA'
    
    message = get_message_from_file_id(file_id)
    _, text = lambda_function._get_chat_id_and_text(message)
    assert text == 'Проверка расшифровки'


def test_3():  # big voice (> 25 Mb)
    file_id = 'AwACAgIAAxkBAAOlZBAZzwypqnCavQicUWXQi7v9KaUAApslAAJbWWlI3-G3OAcdrB8vBA'
    message = get_message_from_file_id(file_id)
    _, text = lambda_function._get_chat_id_and_text(message)
    assert text == 'Статус код ответа OpenAI: 413\nСообщение об ошибке от OpenAI: Maximum content size limit (26214400) exceeded (36264744 bytes read)'


def test_4():  # forwarded voice
    message = {
        "message_id": 111,
        "from": {
            "id": 1111111111,
            "is_bot": False,
            "first_name": "aaaaaaaaaa",
            "username": "bbbbbbbbb", 
            "language_code": "fr"
        },
        "chat": {
            "id": 222222222,
            "first_name": "ccccccccccc",
            "username": "ddddddddddddd",
            "type": "private"
        },
        "date": 3333333333,
        "forward_from": {
            "id": 4444444444,
            "is_bot": False,
            "first_name": "ttttttttt",
            "username": "rrrrrrrrrrr"
        },
        "forward_date": 333333333,
        "voice": {
            "duration": 377,
            "mime_type": "audio/ogg",
            "file_id": "AwACAgIAAxkBAAOjZBAQaRzy2C_s43Hw2iyBMNCBxKgAAuwmAAIZ-IBIgJACXptgfmAvBA",
            "file_unique_id": "QQQQQQQQQQQQ",
            "file_size": 1461143
        }
    }
    _, text = lambda_function._get_chat_id_and_text(message)
    assert text == 'Проверка расшифровки'


def get_message_from_file_id(file_id: str) -> dict:

    message = {
        'message_id': 174, 
        'from': {
            'id': TEST_CHAT_ID, 
            'is_bot': False, 
            'first_name': 'SSS', 
            'username': 'nn', 
            'language_code': 'en'
        }, 
        'chat': {
            'id': TEST_CHAT_ID, 
            'first_name': 'SSS', 
            'username': 'nn', 
            'type': 'private'
        }, 
        'date': 1111111111, 
        'voice': {
            'duration': 1, 
            'mime_type': 'audio/ogg', 
            'file_id': file_id, 
            'file_unique_id': 'AgAAAAAAAAAAAAAA', 
            'file_size': 3147
        }
    }

    return message


EVENT_TEMPLATE_WITHOUT_BODY = \
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
            "X-Forwarded-For": "",
            "X-Forwarded-Port": "443",
            "X-Forwarded-Proto": "https",
            "accept-encoding": "gzip, deflate"
        },
        "multiValueHeaders": {
            "Content-Length": ["323"],
            "Content-Type": ["application/json"],
            "Host": ["execute-api.us-east-1.amazonaws.com"],
            "X-Amzn-Trace-Id": ["Root=1-11111111-2222222222222"],
            "X-Forwarded-For": [""],
            "X-Forwarded-Port": ["443"],
            "X-Forwarded-Proto": ["https"],
            "accept-encoding": ["gzip, deflate"]
        },
        "queryStringParameters": "None",
        "multiValueQueryStringParameters": "None",
        "requestContext": {
            "accountId": "4444444444444",
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
                "sourceIp": "",
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
        "body": None,
        "isBase64Encoded": "False"
    }


if __name__ == '__main__':
    test_1()
    # test_2()
    # test_3()
    # test_4()
    pass