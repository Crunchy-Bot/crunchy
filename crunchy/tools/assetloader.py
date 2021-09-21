import base64

from functools import lru_cache


@lru_cache
def get_base64_asset(name: str) -> str:
    with open(f"assets/{name}", "rb") as file:
        return base64.standard_b64encode(file.read()).decode()
