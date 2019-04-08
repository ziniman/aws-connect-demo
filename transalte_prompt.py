import boto3
import json
import logging
import decimal
from botocore.exceptions import ClientError


logger = logging.getLogger()
logger.setLevel(logging.INFO)

languages = ['en', 'de', 'es', 'nl', 'ru']
# Helper class to convert a DynamoDB item to JSON.
class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, decimal.Decimal):
            if o % 1 > 0:
                return float(o)
            else:
                return int(o)
        return super(DecimalEncoder, self).default(o)


def translate_text(text, target_lang):
    logger.info('Translating text: ' + text + ' to: ' + target_lang)
    translate = boto3.client("translate")
    response =  translate.translate_text(
        Text=text,
        SourceLanguageCode="auto",
        TargetLanguageCode=target_lang
    )
    return response['TranslatedText']


def translate_prompt(event, context):
    #return event
    logger.info('Received event: ' + json.dumps(event))
    content = 'Hi and thanks for calling. Stay tuned while I check for next session of Boaz Ziniman.'
    language_id = event["Details"]["Parameters"]["language_id"]

    if language_id!="Timeout":
        language_id = int(language_id)
        if language_id>1 and len(languages)>=language_id:
            content = translate_text(content, languages[language_id-1])
            # TODO: write code...

    logger.info('Responding with: ' + content)

    resultMap = {"Text":content}
    return resultMap
