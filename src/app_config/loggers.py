from datetime import datetime, timezone

from gunicorn.glogging import Logger


class GunicornLogger(Logger):
    def access(self, resp, req, environ, request_time):
        now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S %z")
        path_info = environ.get("PATH_INFO", "")
        method = environ.get("REQUEST_METHOD", "")
        server_protocol = environ.get("SERVER_PROTOCOL", "")
        status = resp.status.split()[0] if " " in resp.status else resp.status
        self.access_log.info(f'[{now}] "{method} {path_info} {server_protocol}" {status}')
