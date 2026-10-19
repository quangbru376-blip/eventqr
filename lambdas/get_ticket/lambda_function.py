"""AI-assisted GET /ticket?e=<uuid>&t=<uuid>. LabRole, private S3."""
import base64
import os

import boto3
from botocore.config import Config

from api_utils import InputError, uuid_text, reply, error, log_failure

ddb = boto3.resource('dynamodb')
s3 = boto3.client('s3', config=Config(signature_version='s3v4'))


def lambda_handler(event, context):
    if event.get('httpMethod') == 'OPTIONS':
        return reply(200)
    if event.get('httpMethod') != 'GET':
        return error(405, 'METHOD_NOT_ALLOWED', 'Chỉ hỗ trợ GET')
    try:
        query = event.get('queryStringParameters') or {}
        event_id, ticket_id = uuid_text(query.get('e')), uuid_text(query.get('t'))
        found = ddb.Table(os.environ['EVENTS_TABLE']).get_item(
            Key={'eventId': event_id}, ConsistentRead=True).get('Item')
        if not found:
            return error(404, 'EVENT_NOT_FOUND', 'Không tìm thấy sự kiện')
        ticket = ddb.Table(os.environ['TICKETS_TABLE']).get_item(
            Key={'eventId': event_id, 'ticketId': ticket_id}, ConsistentRead=True).get('Item')
        if not ticket:
            return error(404, 'TICKET_NOT_FOUND', 'Không tìm thấy vé')
        qr_key = f'qr/{event_id}/{ticket_id}.png'
        if ticket.get('qrKey') != qr_key or ticket.get('status') not in {'ISSUED', 'CHECKED_IN'}:
            raise ValueError('Unexpected ticket state')
        bucket = os.environ['QR_BUCKET']
        data = {'eventId': event_id, 'ticketId': ticket_id, 'status': ticket['status']}
        mode = os.environ.get('QR_DELIVERY_MODE', 'presigned')
        if mode == 'inline':
            obj = s3.get_object(Bucket=bucket, Key=qr_key)
            try:
                raw = obj['Body'].read(1024 * 1024 + 1)
            finally:
                obj['Body'].close()
            if len(raw) > 1024 * 1024 or not raw.startswith(b'\x89PNG\r\n\x1a\n'):
                raise ValueError('Invalid QR PNG')
            data['qrImageDataUrl'] = 'data:image/png;base64,' + base64.b64encode(raw).decode('ascii')
        elif mode == 'presigned':
            s3.head_object(Bucket=bucket, Key=qr_key)
            data['qrImageUrl'] = s3.generate_presigned_url(
                'get_object', Params={'Bucket': bucket, 'Key': qr_key,
                                    'ResponseContentType': 'image/png',
                                    'ResponseCacheControl': 'no-store'}, ExpiresIn=300)
        else:
            raise ValueError('Invalid QR_DELIVERY_MODE')
        return reply(200, data)
    except InputError as exc:
        return error(400, 'INVALID_INPUT', str(exc))
    except Exception as exc:
        log_failure('GET_TICKET_FAILED', exc)
        return error(500, 'INTERNAL_ERROR', 'Không đọc được vé; kiểm tra log Lambda')
