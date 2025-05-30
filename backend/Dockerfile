FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt \
    && apt-get update \
    && apt-get install -y netcat-openbsd

COPY ./foodgram ./foodgram/
COPY ./manage.py .
RUN mkdir -p recipes users api \
    && mkdir -p recipes/migrations users/migrations api/migrations \
    && touch recipes/migrations/__init__.py \
    && touch users/migrations/__init__.py \
    && touch api/migrations/__init__.py

COPY ./recipes ./recipes/
COPY ./users ./users/
COPY ./api ./api/
COPY entrypoint.sh .
RUN chmod +x entrypoint.sh

ENTRYPOINT ["/bin/sh", "entrypoint.sh"] 