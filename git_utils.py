import subprocess
from urllib.parse import urlparse

def get_git_revision_short_hash() -> str:
    return subprocess.check_output(['git', 'rev-parse', '--short', 'HEAD']).decode('ascii').strip()


def get_git_url() -> str:
    basic_url = subprocess.check_output(['git', 'config', '--get', 'remote.origin.url']).decode('ascii').strip()
    parsed = urlparse(basic_url)
    if parsed.username and parsed.password:
        # erase username and password
        return parsed._replace(netloc="{}".format(parsed.hostname)).geturl()
    else:
        return parsed.geturl()