import asyncio
import json
import logging
import httpx

from roid.exceptions import HTTPException

from crunchy.config import CRUNCHY_API

_log = logging.getLogger("crunchy-api")


class CrunchyApiHTTPException(HTTPException):
    """Something has gone wrong with the api."""


class CrunchyApi:
    def __init__(self, api_token: str):
        self.lock = asyncio.Lock()
        self.client = httpx.AsyncClient(http2=True)

        self.__token = api_token or ""

    async def shutdown(self):
        await self.client.aclose()

    async def request(self, method: str, section: str, headers: dict = None, **extra):
        set_headers = {
            "Authorization": self.__token,
        }

        if headers is not None:
            set_headers = {**headers, **set_headers}

        url = f"{CRUNCHY_API}/{section}"

        async with self.lock:
            r = None
            for tries in range(5):
                try:
                    r = await self.client.request(
                        method, url, headers=set_headers, **extra
                    )

                    data = await r.aread()
                    try:
                        data = json.loads(data)
                    except json.JSONDecodeError:
                        data = data.decode("utf-8")

                    if r.status_code >= 500:
                        raise CrunchyApiHTTPException(r, data.decode("utf-8"))

                    if 300 > r.status_code >= 200:
                        _log.debug(f"{method} {url} successful response: {data}")
                        return data

                    if r.status_code == 429:
                        if not r.headers.get("Via") or isinstance(data, str):
                            # Cloudflare banned, maybe.
                            raise CrunchyApiHTTPException(r, data)

                        # sleep a bit
                        retry_after: float = data["retry_after"]  # noqa
                        message = f"We are being rate limited. Retrying in {retry_after:.2} seconds."
                        _log.warning(message)

                        is_global = data.get("global", False)
                        if is_global:
                            _log.warning(
                                "Global rate limit has been hit. Retrying in %.2f seconds.",
                                retry_after,
                            )

                        await asyncio.sleep(retry_after)
                        _log.debug(
                            "Rate limit wait period has elapsed. Retrying request."
                        )

                        continue

                    if r.status_code == 403:
                        raise CrunchyApiHTTPException(r, data)
                    elif r.status_code == 404:
                        raise CrunchyApiHTTPException(r, data)
                    else:
                        raise CrunchyApiHTTPException(r, data)

                # An exception has occurred at the transport layer e.g. socket interrupt.
                except httpx.TransportError as e:
                    if tries < 4:
                        _log.warning(
                            f"failed preparing to retry connection failure due to error {e!r}"
                        )
                        await asyncio.sleep(1 + tries * 2)
                        continue
                    raise
                finally:
                    if r is not None:
                        await r.aclose()

            if r is not None:
                # We've run out of retries, raise.
                if r.status_code >= 500:
                    raise CrunchyApiHTTPException(r, data)

                raise CrunchyApiHTTPException(r, data)

            raise RuntimeError("Unreachable code in HTTP handling")
