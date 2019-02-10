import boto3
import json
import logging
import decimal
from boto3.dynamodb.conditions import Key, Attr
from botocore.exceptions import ClientError

from datetime import datetime, timedelta
from dateutil import tz
import time

logger = logging.getLogger()
logger.setLevel(logging.INFO)

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('boaz_sessions')

languages = ['en', 'de', 'es', 'nl']
# Helper class to convert a DynamoDB item to JSON.
class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, decimal.Decimal):
            if o % 1 > 0:
                return float(o)
            else:
                return int(o)
        return super(DecimalEncoder, self).default(o)

def get_session():
    filename = 'sessions_list'
    cache = read_cache(filename)
    from_zone = tz.gettz('UTC')
    to_zone = tz.gettz('Asia/Jerusalem')

    timestamp = datetime.utcnow()
    timestamp = timestamp.replace(tzinfo=from_zone)
    timestamp = timestamp.astimezone(to_zone)
    timestamp = timestamp.strftime('%Y-%m-%d %H:%M')
    print timestamp

    if not cache:
        try:
            response = table.query(
                IndexName='speaker-datetime-index',
                Limit=1,
                KeyConditionExpression=Key('speaker').eq('Boaz Ziniman') & Key('datetime').gte(timestamp)
            )

            items = response[u'Items']

            buttons = []

            if items:
                for item in items:
                    buttons.append(item)
            else:
                return None

            store_cache(filename, buttons)
            return buttons

        except ClientError as e:
            logger.error(e.response['Error']['Message'])
            return None
    else:
        return cache

def store_cache(filename, data):
    file = open('/tmp/%s' % filename,'w')
    json.dump(data, file, cls=DecimalEncoder)
    file.close()

    logger.info('Wrote cache to %s: %s' % (filename, data))
    return True

def translate_text(text, target_lang):
    translate = boto3.client("translate")
    response =  translate.translate_text(
        Text=text,
        SourceLanguageCode="auto",
        TargetLanguageCode=target_lang
    )
    return response['TranslatedText']

def read_cache(filename):
    #return False

    try:
        with open('/tmp/%s' % filename) as json_data:
            data = json.load(json_data)
            print(data)
            json_data.close()

        logger.info('Read cache from file %s: %s' % (filename, data))
        return data

    except Exception as e:
        logger.warning("Failed to read cache file %s. %s" % (filename, e))

def NextSession(event, context):
    #return event
    logger.info('Received event: ' + json.dumps(event))


    lookup_val = time.strftime("%d-%m-%Y")

    language_id = int(event["Details"]["Parameters"]["language_id"])

    #TZ Adjustments - Basic TZ is UTC
    current_ts = int(time.time()) + (60*60*3)

    next_session = get_session()
    logger.info(next_session)
    item = None

    if next_session:
        for item in next_session:
            speaker = item['speaker']
            session_name = item['topic']
            session_date = item['datetime']
            session_location = item["location"]

    if item:
        logger.info(item)
        session_date = datetime.strptime(session_date,'%Y-%m-%d %H:%M').strftime('%B %d at %H:%M')
        content = 'Next session for %s is.  %s, on %s, in %s. Thanks for using the demo. Goodbye!' % (speaker, session_name, session_date, session_location)
    else:
        content = 'I could not find any future sessions.'

    if language_id>1:
        content = translate_text(content, languages[1])
        # TODO: write code...
    logger.info('Responding with: ' + content)

    resultMap = {"Text":content}
    return resultMap

def translate_prompt(event, context):
    #return event
    logger.info('Received event: ' + json.dumps(event))


    language_id = int(event["Details"]["Parameters"]["language_id"])
    content = 'Hi and thanks for calling. Stay tuned while I check for next session of Boaz Ziniman.'

    if language_id>1:
        content = translate_text(content, languages[1])
        # TODO: write code...
    logger.info('Responding with: ' + content)

    resultMap = {"Text":content}
    return resultMap
