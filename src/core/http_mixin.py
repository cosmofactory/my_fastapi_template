import httpx


class BaseHTTPMixin:
    def __init__(self, base_url: str, client: httpx.AsyncClient, api_key: str, content_type: str):
        self.base_url = base_url
        self.client = client
        self.api_key = api_key
        self.content_type = content_type

    @property
    def headers(self) -> dict:
        return {"authorization": f"Bearer {self.api_key}", "Content-Type": self.content_type}

    def _make_headers(self, headers: dict) -> dict:
        return {**self.headers, **headers}

    async def get(self, url: str, **kwargs) -> httpx.Response:
        headers = self._make_headers(kwargs.pop("headers", {}))
        return await self.client.get(url, headers=headers, **kwargs)

    async def post(self, url: str, json: dict | None = None, **kwargs) -> httpx.Response:
        headers = self._make_headers(kwargs.pop("headers", {}))
        return await self.client.post(url, headers=headers, json=json, **kwargs)

    async def put(self, url: str, json: dict | None = None, **kwargs) -> httpx.Response:
        headers = self._make_headers(kwargs.pop("headers", {}))
        return await self.client.put(url, headers=headers, json=json, **kwargs)

    async def delete(self, url: str, **kwargs) -> httpx.Response:
        headers = self._make_headers(kwargs.pop("headers", {}))
        return await self.client.delete(url, headers=headers, **kwargs)

    async def patch(self, url: str, json: dict | None = None, **kwargs) -> httpx.Response:
        headers = self._make_headers(kwargs.pop("headers", {}))
        return await self.client.patch(url, headers=headers, json=json, **kwargs)
