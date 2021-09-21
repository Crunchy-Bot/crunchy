import asyncio
import json
import logging
import httpx

from roid.__version__ import __version__
from roid.exceptions import HTTPException, DiscordServerError, Forbidden, NotFound
from roid.http import MaybeUnlock, _parse_rate_limit_header

from crunchy.config import DISCORD_API


_log = logging.getLogger("crunchy-http")


class HttpHandler:
    API_VERSION = "v8"

    def __init__(self, token: str):
        self.lock = asyncio.Lock()
        self.client = httpx.AsyncClient(http2=True)

        self.user_agent = (
            f"DiscordBot (https://github.com/chillfish8/roid {__version__})"
        )

        self.__token = token

    async def shutdown(self):
        await self.client.aclose()

    async def request(self, method: str, section: str, headers: dict = None, **extra):
        set_headers = {
            "User-Agent": self.user_agent,
        }

        if extra.pop("pass_token", False):
            set_headers["Authorization"] = f"Bot {self.__token}"

        if headers is not None:
            set_headers = {**headers, **set_headers}

        url = f"{DISCORD_API}{section}"

        await self.lock.acquire()
        with MaybeUnlock(self.lock) as lock:
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
                        raise DiscordServerError(r, data.decode("utf-8"))

                    remaining = r.headers.get("X-Ratelimit-Remaining")
                    if remaining == "0" and r.status_code != 429:
                        # we've depleted our current bucket
                        delta = _parse_rate_limit_header(r)
                        _log.debug(
                            f"we've emptied our rate limit bucket on endpoint: {url}, retry: {delta:.2}"
                        )
                        lock.defer()
                        asyncio.get_running_loop().call_later(delta, self.lock.release)

                    if 300 > r.status_code >= 200:
                        _log.debug(f"{method} {url} successful response: {data}")
                        return data

                    if r.status_code == 429:
                        if not r.headers.get("Via") or isinstance(data, str):
                            # Cloudflare banned, maybe.
                            raise HTTPException(r, data)

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
                        raise Forbidden(r, data)
                    elif r.status_code == 404:
                        raise NotFound(r, data)
                    else:
                        raise HTTPException(r, data)

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
                    raise DiscordServerError(r, data)

                raise HTTPException(r, data)

            raise RuntimeError("Unreachable code in HTTP handling")
