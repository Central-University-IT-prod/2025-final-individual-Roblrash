FROM python:3.12-slim

WORKDIR /solution

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

COPY bot/ bot/

CMD ["python", "bot/main.py"]
