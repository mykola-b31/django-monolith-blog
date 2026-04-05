FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app
COPY requirements.txt .

RUN apt update && apt install -y netcat-traditional
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
CMD ["bash", "start.sh"]