"""AI-assisted GET /stats/{eventId}; Query all pages, no whole-table Scan."""
import boto3

from a_common import env, error, failure, InputError, reply, uuid_text

ddb = boto3.resource('dynamodb')


def lambda_handler(event, context):
    if event.get('httpMethod') == 'OPTIONS':
        return reply(200)
    if event.get('httpMethod') != 'GET':
        return error(405, 'METHOD_NOT_ALLOWED', 'Chỉ hỗ trợ GET')
    try:
        event_id = uuid_text((event.get('pathParameters') or {}).get('eventId'))
        if not ddb.Table(env('EVENTS_TABLE')).get_item(
                Key={'eventId': event_id}, ConsistentRead=True).get('Item'):
            return error(404, 'EVENT_NOT_FOUND', 'Không tìm thấy sự kiện')
        table = ddb.Table(env('TICKETS_TABLE'))
        params = {'KeyConditionExpression': '#e = :e',
                  'ExpressionAttributeNames': {'#e': 'eventId', '#s': 'status', '#t': 'ticketId'},
                  'ExpressionAttributeValues': {':e': event_id},
                  'ProjectionExpression': '#t, #s', 'ConsistentRead': True}
        total = checked = 0
        while True:
            page = table.query(**params)
            for item in page.get('Items', []):
                if str(item.get('ticketId', '')).startswith('EMAIL#'):
                    continue
                if item.get('status') not in {'ISSUED', 'CHECKED_IN'}:
                    raise ValueError('Unexpected ticket status')
                total += 1
                checked += item['status'] == 'CHECKED_IN'
            last = page.get('LastEvaluatedKey')
            if not last:
                break
            params['ExclusiveStartKey'] = last
        return reply(200, {'eventId': event_id, 'totalTickets': total,
                           'checkedInTickets': checked, 'notCheckedInTickets': total - checked})
    except InputError as exc:
        return error(400, 'INVALID_INPUT', str(exc))
    except Exception as exc:
        failure('STATS_FAILED', exc)
        return error(500, 'INTERNAL_ERROR', 'Không đọc được thống kê; kiểm tra log Lambda')
