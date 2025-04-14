FROM python:3.12-slim

WORKDIR /solution

RUN apt-get update && apt-get install -y postgresql-client && rm -rf /var/lib/apt/lists/*

COPY requirements.txt requirements.txt

RUN pip install -r requirements.txt

COPY . .

RUN chmod +x entry.sh

ENTRYPOINT [ "sh", "entry.sh" ]
