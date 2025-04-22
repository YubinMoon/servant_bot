FROM python:3.13-alpine

RUN apk update
RUN apk add build-base musl-dev

WORKDIR /bot

COPY ./requirements.txt /bot/requirements.txt

RUN pip install -r requirements.txt

COPY ./app /bot/app

CMD ["python", "-m", "app.main"]
