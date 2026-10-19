"""AI-assisted POST /events. API Gateway requires the organizer API key."""
import uuid

import boto3

from a_common import body_json, env, error, failure, InputError, now_utc, reply, start_time, text

ddb = boto3.resource('dynamodb')


def lambda_handler(event, context):
    if event.get('httpMethod') == 'OPTIONS':
        return reply(200)
    if event.get('httpMethod') != 'POST':
        return error(405, 'METHOD_NOT_ALLOWED', 'Chỉ hỗ trợ POST')
    try:
        body = body_json(event)
        item = {'eventId': str(uuid.uuid4()), 'name': text(body.get('name'), 'Tên sự kiện', 100),
                'startTime': start_time(body.get('startTime')),
                'venue': text(body.get('venue'), 'Địa điểm', 200), 'createdAt': now_utc()}
        ddb.Table(env('EVENTS_TABLE')).put_item(
            Item=item, ConditionExpression='attribute_not_exists(eventId)')
        return reply(201, item)
    except InputError as exc:
        return error(400, 'INVALID_INPUT', str(exc))
    except Exception as exc:
        failure('CREATE_EVENT_FAILED', exc)
        return error(500, 'INTERNAL_ERROR', 'Không tạo được sự kiện; kiểm tra log Lambda')
