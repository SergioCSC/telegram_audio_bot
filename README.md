# Telegram audio bot

This is the code for my Telegram bot designed for interaction with OpenAI: https://t.me/get_gpt_advice_bot


With this bot you can:

* transcribe audio and voice messages into text

* translate English to Russian (write to the bot: ```translate: here_is_my_text```) and vice versa (```переведи: здесь_мой_текст```)

* correct text written in any language (write to the bot: ```correct: here_is_my_text```)

* chat with ChatGPT 3.5 (just write your request to the bot)

&nbsp;
## Requirements

To run this code, you have to create a *.env* file in the project folder with the following variables:

```console
OPEN_AI_API_KEY=your open ai api key here
TELEGRAM_BOT_TOKEN=your telegram bot token here
```

&nbsp;
### Run on AWS Lambda

My bot hosts on Amazon Lambda. If you want to host your bot there too:

* Create an AWS Lambda function
* Use *python 3.9* runtime for the function
* Create an API gateway trigger in your Lambda and use it as a webhook for the telegram bot using the following HTTP request:

      https://api.telegram.org/bot*your-bot-token-here*/setWebhook?url=*lambda-trigger-url-here*

  Telegram waits for an answer from bots for about 30 seconds only. However, chatGPT may create an answer that takes longer. So, instead of making trigger for this lambda function, you can create another lambda function and set this webhook to it. The purpose of this auxiliary function will be: 
  * to accept a request from Telegram
  * to asynchroniously invoke the main lambda function
  * to instantly reply to Telegram with 
  
    ```json
    {'statusCode': 200, 'body': 'Success'}
    ```

  See the sample code of this parent function in *deploy/parent_aws_lambda_f.py*

* Add *pandas* layer (version 3) to your Lambda function (it contains python *requests* library)
* Add *lame* binary and *.so (from ```apt install lame```) to project root
* Upload the ZIP archive with this code (including the *opus* folder with the opus decoder library) in the Lambda function

&nbsp;
### Run locally

If you want to run this code locally, you need to:

* install lame library to convert wav to mp3:
  ```console
  apt install lame
  ```

* install the python library *requests*:

  ```console
  pip install -r deploy/requirements.txt
  ```

* Then, run

  ```console
  python lambda_function.py
  ```

&nbsp;
## Third parties
* This code uses *opusdec* library of opus audio codec under the three-clause BSD license.
  For details, see https://opus-codec.org/license/

* This code uses LAME mp3 encoder of The LAME Project
under LGPL license.
  For details, see https://lame.sourceforge.io/

