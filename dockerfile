FROM python:3.10-alpine

RUN apk update
RUN apk add build-base musl-dev

WORKDIR /app

COPY ./requirements.txt /app/requirements.txt

RUN pip install -r requirements.txt

COPY . /app

CMD ["python", "main.py"]
