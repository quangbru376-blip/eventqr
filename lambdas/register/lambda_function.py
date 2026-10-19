"""AI-assisted POST /register; QR -> conditional ticket write -> SNS.

No registration idempotency key in API v0.2: do not blindly repeat a POST.
"""
import json
import uuid

import boto3
from botocore.config import Config

from a_common import (body_json, email_text, env, error, failure, InputError,
                      now_utc, reply, secret_data, text, ticket_url, uuid_text)
from ticket_mail import send_ticket

ddb = boto3.resource('dynamodb')
invoke_client = boto3.client('lambda', config=Config(
    connect_timeout=2, read_timeout=15, retries={'total_max_attempts': 1}))


def lambda_handler(event, context):
    if event.get('httpMethod') == 'OPTIONS':
        return reply(200)
    if event.get('httpMethod') != 'POST':
        return error(405, 'METHOD_NOT_ALLOWED', 'Chỉ hỗ trợ POST')
    try:
        body = body_json(event)
        event_id = uuid_text(body.get('eventId'))
        name = text(body.get('name'), 'Họ tên', 100)
        email = email_text(body.get('email'))
        found = ddb.Table(env('EVENTS_TABLE')).get_item(
            Key={'eventId': event_id}, ConsistentRead=True).get('Item')
        if not found:
            return error(404, 'EVENT_NOT_FOUND', 'Không tìm thấy sự kiện')
        ticket_id = str(uuid.uuid4())
        url = ticket_url(event_id, ticket_id)  # Validate before any writes.
        _, kid = secret_data()  # Metadata matches the same secret used by B.
        result = invoke_client.invoke(
            FunctionName=env('GENERATE_QR_FUNCTION'), InvocationType='RequestResponse',
            Payload=json.dumps({'eventId': event_id, 'ticketId': ticket_id}).encode('utf-8'))
        stream = result['Payload']
        try:
            qr_result = json.loads(stream.read())
        finally:
            stream.close()
        if result.get('FunctionError') or result.get('StatusCode') != 200:
            raise RuntimeError('QR child Lambda failed')
        expected_key = f'qr/{event_id}/{ticket_id}.png'
        if not isinstance(qr_result, dict) or qr_result.get('qrKey') != expected_key:
            raise RuntimeError('QR child Lambda returned unexpected qrKey')
        item = {'eventId': event_id, 'ticketId': ticket_id, 'name': name, 'email': email,
                'status': 'ISSUED', 'createdAt': now_utc(), 'qrKey': expected_key, 'kid': kid}
        ddb.Table(env('TICKETS_TABLE')).put_item(
            Item=item, ConditionExpression='attribute_not_exists(eventId) AND attribute_not_exists(ticketId)')
    except InputError as exc:
        return error(400, 'INVALID_INPUT', str(exc))
    except Exception as exc:
        failure('REGISTER_FAILED', exc)
        return error(500, 'INTERNAL_ERROR', 'Không hoàn tất tạo vé; kiểm tra log trước khi thử lại')

    # From here on a ticket exists. Email failure must not change success into 500.
    try:
        delivery = send_ticket(email, event_id, ticket_id, found.get('name', 'EventQR'))
        if delivery not in {'PUBLISHED', 'PENDING_CONFIRMATION', 'FAILED'}:
            delivery = 'FAILED'
    except Exception as exc:
        failure('REGISTER_EMAIL_FAILED', exc)
        delivery = 'FAILED'
    return reply(201, {'eventId': event_id, 'ticketId': ticket_id, 'status': 'ISSUED',
                       'ticketUrl': url, 'emailDeliveryStatus': delivery})
