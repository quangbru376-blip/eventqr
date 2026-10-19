"""AI-assisted integration regression tests for the merged B source.

These 15 tests are new local checks, separate from B's historical test report.
AWS clients are fake; no network, AWS credentials, email or camera is used.
"""
import io
import json
import os
import unittest
from unittest.mock import patch

from test_a import E, T, OTHER, ROOT, fake, load, request, data, code

generate = load('merged_generate', ROOT/'lambdas/generate_qr/lambda_function.py')
ticket = load('merged_ticket', ROOT/'lambdas/get_ticket/lambda_function.py')
resend = load('merged_resend', ROOT/'lambdas/resend/lambda_function.py')
web = load('merged_web', ROOT/'lambdas/web/lambda_function.py')


class BTests(unittest.TestCase):
    def setUp(self):
        fake.reset()
        generate._key = None
        self.env = patch.dict(os.environ, WEB_BUCKET='test-web', QR_DELIVERY_MODE='presigned')
        self.env.start()
        self.addCleanup(self.env.stop)
        self.key = f'qr/{E}/{T}.png'
        fake.tickets[(E, T)] = {
            'eventId': E, 'ticketId': T, 'email': 'test@example.invalid',
            'name': 'Local guest', 'status': 'ISSUED', 'qrKey': self.key,
        }

    def get_ticket(self):
        return ticket.lambda_handler({
            'httpMethod': 'GET', 'queryStringParameters': {'e': E, 't': T}}, None)

    def resend_ticket(self, **extra):
        return resend.lambda_handler(request({'eventId': E, 'ticketId': T, **extra}), None)

    def test_qr_png_retry_and_secret_cache(self):
        for _ in range(2):
            self.assertEqual(generate.lambda_handler({'eventId': E, 'ticketId': T}, None),
                             {'qrKey': self.key})
        self.assertEqual(fake.secret_calls, 1)
        self.assertEqual(len(fake.objects), 1)
        self.assertTrue(fake.objects[('test-bucket', self.key)].startswith(b'\x89PNG\r\n\x1a\n'))

    def test_qr_invalid_uuid_never_uploads(self):
        with self.assertRaisesRegex(RuntimeError, 'QR_GENERATION_FAILED'):
            generate.lambda_handler({'eventId': 'invalid', 'ticketId': T}, None)
        self.assertFalse(fake.objects)

    def test_ticket_presigned_contract_and_no_email(self):
        with patch.object(fake, 'head_object', create=True) as head, patch.object(
                fake, 'generate_presigned_url', create=True,
                return_value='https://example.invalid/qr.png') as signed:
            result = self.get_ticket()
        self.assertEqual(result['statusCode'], 200)
        self.assertNotIn('email', data(result))
        self.assertEqual(data(result)['qrImageUrl'], 'https://example.invalid/qr.png')
        head.assert_called_once_with(Bucket='test-bucket', Key=self.key)
        self.assertEqual(signed.call_args.kwargs['ExpiresIn'], 300)
        self.assertEqual(signed.call_args.kwargs['Params']['Key'], self.key)

    def test_ticket_inline_png_and_stream_closed(self):
        stream = io.BytesIO(b'\x89PNG\r\n\x1a\nlocal-test')
        with patch.dict(os.environ, QR_DELIVERY_MODE='inline'), patch.object(
                fake, 'get_object', create=True, return_value={'Body': stream}):
            result = self.get_ticket()
        self.assertEqual(result['statusCode'], 200)
        self.assertTrue(data(result)['qrImageDataUrl'].startswith('data:image/png;base64,'))
        self.assertTrue(stream.closed)

    def test_ticket_missing_event(self):
        fake.events.clear()
        self.assertEqual(code(self.get_ticket()), 'EVENT_NOT_FOUND')

    def test_ticket_missing_ticket(self):
        fake.tickets.clear()
        self.assertEqual(code(self.get_ticket()), 'TICKET_NOT_FOUND')

    def test_ticket_wrong_qr_key_rejected(self):
        fake.tickets[(E, T)]['qrKey'] = f'qr/{E}/{OTHER}.png'
        self.assertEqual(self.get_ticket()['statusCode'], 500)

    def test_resend_pending_never_publishes(self):
        fake.confirmed = False
        result = self.resend_ticket()
        self.assertEqual(result['statusCode'], 409)
        self.assertEqual(code(result), 'EMAIL_CONFIRMATION_REQUIRED')
        self.assertFalse(fake.sent)

    def test_resend_new_subscription_never_publishes(self):
        fake.subscribed = False
        self.assertEqual(self.resend_ticket()['statusCode'], 409)
        self.assertTrue(fake.subscribed)
        self.assertFalse(fake.sent)

    def test_resend_wrong_filter_fails_closed(self):
        fake.bad_filter = True
        result = self.resend_ticket()
        self.assertEqual(result['statusCode'], 503)
        self.assertEqual(code(result), 'EMAIL_DELIVERY_FAILED')
        self.assertFalse(fake.sent)

    def test_resend_uses_stored_email_and_preserves_checkin(self):
        fake.tickets[(E, T)].update(status='CHECKED_IN', checkedInAt='2026-10-19T12:00:00Z')
        before = dict(fake.tickets[(E, T)])
        result = self.resend_ticket(email='other@example.invalid')
        self.assertEqual(data(result)['emailDeliveryStatus'], 'PUBLISHED')
        self.assertEqual(fake.sent[0]['MessageAttributes']['email'],
                         {'DataType': 'String', 'StringValue': 'test@example.invalid'})
        self.assertEqual(fake.tickets[(E, T)], before)

    def test_resend_sns_failure_returns_503(self):
        fake.mail_fail = True
        self.assertEqual(self.resend_ticket()['statusCode'], 503)
        self.assertFalse(fake.sent)

    def test_resend_invalid_json(self):
        result = resend.lambda_handler({'httpMethod': 'POST', 'body': '{'}, None)
        self.assertEqual(result['statusCode'], 400)

    def test_web_allowlist_and_javascript_type(self):
        with patch.object(fake, 'get_object', create=True,
                          return_value={'Body': io.BytesIO(b'// local test')}) as get:
            result = web.lambda_handler({
                'httpMethod': 'GET', 'pathParameters': {'page': 'app.js'}}, None)
        self.assertEqual(result['statusCode'], 200)
        self.assertEqual(result['headers']['Content-Type'], 'application/javascript; charset=utf-8')
        get.assert_called_once_with(Bucket='test-web', Key='app.js')
        for page in ['../config.js', 'qr/private.png', 'lambda_function.py']:
            result = web.lambda_handler({
                'httpMethod': 'GET', 'pathParameters': {'page': page}}, None)
            self.assertEqual(result['statusCode'], 404)

    def test_options_for_public_b_routes(self):
        for module in [ticket, resend]:
            with self.subTest(module=module.__name__):
                result = module.lambda_handler({'httpMethod': 'OPTIONS'}, None)
                self.assertEqual(result['statusCode'], 200)
                self.assertEqual(result['headers']['Access-Control-Allow-Origin'],
                                 'https://example.invalid')
