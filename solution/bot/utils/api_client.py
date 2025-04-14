import httpx
from config import API_BASE_URL

async def api_get(endpoint: str) -> httpx.Response:
    url = f"{API_BASE_URL}{endpoint}"
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
    return response

async def api_post(endpoint: str, json_data: dict = None, files: dict = None) -> httpx.Response:
    url = f"{API_BASE_URL}{endpoint}"
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=json_data, files=files)
    return response

async def api_put(endpoint: str, json_data: dict = None) -> httpx.Response:
    url = f"{API_BASE_URL}{endpoint}"
    async with httpx.AsyncClient() as client:
        response = await client.put(url, json=json_data)
    return response

async def api_delete(endpoint: str) -> httpx.Response:
    url = f"{API_BASE_URL}{endpoint}"
    async with httpx.AsyncClient() as client:
        response = await client.delete(url)
    return response

async def api_put_image(endpoint: str, json_data: dict = None, files: dict = None) -> httpx.Response:
    url = f"{API_BASE_URL}{endpoint}"
    async with httpx.AsyncClient() as client:
        response = await client.put(url, json=json_data, files=files)
    return response
