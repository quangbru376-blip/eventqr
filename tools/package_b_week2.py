"""AI-assisted builder. Does not use AWS credentials or create cloud resources.

Run: py tools/package_b_week2.py --segno-archive PATH_TO_WHEEL_OR_QR_ZIP
Uses Segno from a downloaded wheel or the original B generate-qr ZIP.
"""
import argparse
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument('--segno-archive', '--segno-wheel', dest='segno_archive',
                    type=Path, required=True,
                    help='Segno wheel or original generate-qr ZIP (outside output dist/)')
args = parser.parse_args()
out = ROOT / 'dist'
if args.segno_archive.resolve() == (out / 'eventqr-generate-qr.zip').resolve():
 parser.error('Use a dependency archive outside output dist/ to avoid overwriting the input')
with ZipFile(args.segno_archive) as dependency:
 if 'segno/__init__.py' not in dependency.namelist():
  parser.error('Dependency archive does not contain Segno')
out.mkdir(exist_ok=True)

files = {
 'generate_qr': [('lambdas/generate_qr/lambda_function.py','lambda_function.py'),
                 ('lambdas/common/hmac_utils.py','hmac_utils.py'),
                 ('lambdas/common/api_utils.py','api_utils.py')],
 'get_ticket': [('lambdas/get_ticket/lambda_function.py','lambda_function.py'),
                ('lambdas/common/api_utils.py','api_utils.py')],
 'resend': [('lambdas/resend/lambda_function.py','lambda_function.py'),
            ('lambdas/common/api_utils.py','api_utils.py'),
            ('lambdas/common/ticket_mail.py','ticket_mail.py')],
 'web': [('lambdas/web/lambda_function.py','lambda_function.py')],
}
for name, members in files.items():
 with ZipFile(out / f'eventqr-{name.replace("_","-")}.zip','w',ZIP_DEFLATED) as z:
  for source,target in members:z.write(ROOT/source,target)
  if name == 'generate_qr':
   with ZipFile(args.segno_archive) as wheel:
    for member in wheel.namelist():
     if member.startswith('segno/') or member.endswith('/licenses/LICENSE'):
      z.writestr(member,wheel.read(member))
 print(f'Built dist/eventqr-{name.replace("_","-")}.zip')
