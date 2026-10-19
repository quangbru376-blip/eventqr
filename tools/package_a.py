"""AI-assisted local ZIP builder. No AWS calls or credentials required."""
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

root = Path(__file__).resolve().parents[1]
out = root / 'dist'
out.mkdir(exist_ok=True)
for folder in ['create_event', 'register', 'checkin', 'stats']:
    members = [(root/'lambdas'/folder/'lambda_function.py', 'lambda_function.py'),
               (root/'lambdas/common/a_common.py', 'a_common.py')]
    if folder == 'register':
        members += [(root/'lambdas/common/ticket_mail.py', 'ticket_mail.py'),
                    (root/'lambdas/common/api_utils.py', 'api_utils.py')]
    if folder == 'checkin':
        members.append((root/'lambdas/common/hmac_utils.py', 'hmac_utils.py'))
    name = out/f'eventqr-{folder.replace("_", "-")}.zip'
    with ZipFile(name, 'w', ZIP_DEFLATED) as archive:
        for source, target in members:
            archive.write(source, target)
    print('Built', name.name)
