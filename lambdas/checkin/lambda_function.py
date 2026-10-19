"""AI-assisted POST /checkin; HMAC verification + atomic conditional update."""
import re

import boto3
from botocore.exceptions import ClientError

from a_common import (body_json, env, error, failure, InputError, now_utc,
                      reply, secret_data, uuid_text)
from hmac_utils import verify_ticket

ddb = boto3.resource('dynamodb')


def lambda_handler(event, context):
    if event.get('httpMethod') == 'OPTIONS':
        return reply(200)
    if event.get('httpMethod') != 'POST':
        return error(405, 'METHOD_NOT_ALLOWED', 'Chỉ hỗ trợ POST')
    try:
        body = body_json(event)
        selected_event = uuid_text(body.get('eventId'))
        payload = body.get('qrPayload')
        if not isinstance(payload, str) or len(payload) > 512:
            raise InputError('Thiếu hoặc sai qrPayload')
        parts = payload.split('.')
        if len(parts) != 4 or parts[0] != 'v1' or not re.fullmatch(r'[A-Za-z0-9_-]{43}', parts[3]):
            raise InputError('QR sai định dạng hoặc phiên bản')
        qr_event, ticket_id = uuid_text(parts[1]), uuid_text(parts[2])
        key, _ = secret_data()
        if not verify_ticket(payload, key):
            return error(403, 'INVALID_SIGNATURE', 'Chữ ký vé không hợp lệ')
        if qr_event != selected_event:
            return error(403, 'EVENT_MISMATCH', 'Vé thuộc sự kiện khác')
        found = ddb.Table(env('EVENTS_TABLE')).get_item(
            Key={'eventId': selected_event}, ConsistentRead=True).get('Item')
        if not found:
            return error(404, 'EVENT_NOT_FOUND', 'Không tìm thấy sự kiện')
        table = ddb.Table(env('TICKETS_TABLE'))
        checked_at = now_utc()
        try:
            result = table.update_item(
                Key={'eventId': selected_event, 'ticketId': ticket_id},
                UpdateExpression='SET #s = :checked, checkedInAt = :at',
                ConditionExpression='attribute_exists(eventId) AND attribute_exists(ticketId) AND #s = :issued',
                ExpressionAttributeNames={'#s': 'status'},
                ExpressionAttributeValues={':checked': 'CHECKED_IN', ':issued': 'ISSUED', ':at': checked_at},
                ReturnValues='ALL_NEW')
        except ClientError as exc:
            if exc.response.get('Error', {}).get('Code') != 'ConditionalCheckFailedException':
                raise
            existing = table.get_item(
                Key={'eventId': selected_event, 'ticketId': ticket_id}, ConsistentRead=True).get('Item')
            if not existing:
                return error(404, 'TICKET_NOT_FOUND', 'Không tìm thấy vé')
            if existing.get('status') == 'CHECKED_IN' and existing.get('checkedInAt'):
                return error(409, 'TICKET_ALREADY_CHECKED_IN', 'Vé đã được check-in',
                             {'checkedInAt': existing['checkedInAt']})
            raise ValueError('Unexpected ticket status')
        item = result['Attributes']
        return reply(200, {'eventId': selected_event, 'ticketId': ticket_id,
                           'name': item.get('name', ''), 'status': item['status'],
                           'checkedInAt': item['checkedInAt']})
    except InputError as exc:
        return error(400, 'INVALID_INPUT', str(exc))
    except Exception as exc:
        failure('CHECKIN_FAILED', exc)
        return error(500, 'INTERNAL_ERROR', 'Không hoàn tất check-in; kiểm tra log Lambda')
