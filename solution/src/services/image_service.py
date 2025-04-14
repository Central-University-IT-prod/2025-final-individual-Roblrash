import asyncio
import io
import os
import uuid
import urllib.parse
from fastapi import HTTPException
from minio import Minio
from minio.error import S3Error
from src.backend.metrics import api_errors_total


def get_minio_client() -> Minio:
    """
    Создаёт клиента MinIO, используя переменные окружения, заданные в docker-compose.
    Ожидается, что переменные MINIO_URL, MINIO_ACCESS_KEY и MINIO_SECRET_KEY установлены.
    """
    raw_url = os.getenv("MINIO_URL")
    if not raw_url:
        raise HTTPException(status_code=500, detail="Переменная MINIO_URL не установлена")

    if raw_url.startswith("http://"):
        endpoint = raw_url[len("http://"):]
    elif raw_url.startswith("https://"):
        endpoint = raw_url[len("https://"):]
    else:
        endpoint = raw_url
    endpoint = endpoint.rstrip("/")

    access_key = os.getenv("MINIO_ACCESS_KEY")
    secret_key = os.getenv("MINIO_SECRET_KEY")
    if not access_key or not secret_key:
        raise HTTPException(status_code=500, detail="Переменные MINIO_ACCESS_KEY или MINIO_SECRET_KEY не установлены")

    return Minio(
        endpoint,
        access_key=access_key,
        secret_key=secret_key,
        secure=False
    )


async def save_image_file(file) -> str:
    """
    Загружает файл изображения в MinIO и возвращает публичный URL.
    """
    loop = asyncio.get_running_loop()
    client = get_minio_client()
    bucket_name = "ad-images"

    def ensure_bucket():
        if not client.bucket_exists(bucket_name):
            client.make_bucket(bucket_name)

    await loop.run_in_executor(None, ensure_bucket)

    file_ext = file.filename.split(".")[-1]
    object_name = f"{uuid.uuid4()}.{file_ext}"

    data = await file.read()
    data_length = len(data)
    stream = io.BytesIO(data)

    def upload():
        try:
            client.put_object(bucket_name, object_name, stream, data_length)
        except S3Error as err:
            api_errors_total.inc()
            raise HTTPException(status_code=500, detail=f"Ошибка при загрузке изображения: {err}")

    await loop.run_in_executor(None, upload)

    minio_url = os.getenv("MINIO_URL")
    public_url = f"{minio_url.rstrip('/')}/{bucket_name}/{object_name}"
    return public_url


def extract_object_info(url: str) -> tuple:
    """
    Извлекает имя бакета и имя объекта из публичного URL.
    Ожидается формат URL: http://<host>:<port>/<bucket>/<object>
    """
    parsed = urllib.parse.urlparse(url)
    path = parsed.path.lstrip('/')
    parts = path.split('/', 1)
    if len(parts) != 2:
        raise ValueError("Невалидный URL изображения")
    return parts[0], parts[1]


async def delete_image_file(image_url: str) -> None:
    """
    Удаляет изображение из MinIO по его публичному URL.
    """
    loop = asyncio.get_running_loop()
    client = get_minio_client()
    try:
        bucket, object_name = extract_object_info(image_url)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    def remove_object():
        try:
            client.remove_object(bucket, object_name)
        except S3Error as err:
            api_errors_total.inc()
            raise HTTPException(status_code=500, detail=f"Ошибка при удалении изображения: {err}")

    await loop.run_in_executor(None, remove_object)
