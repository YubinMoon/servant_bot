FROM python:3.10-alpine

RUN apk update
RUN apk add build-base musl-dev

WORKDIR /bot

COPY ./requirements.txt /bot/requirements.txt

RUN pip install -r requirements.txt

COPY .env /bot/.env

COPY ./app /bot/app

CMD ["python", "main.py"]
