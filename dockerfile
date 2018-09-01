FROM python:3.6.6-alpine3.6

COPY . /API

WORKDIR /API

RUN apk update && \
 apk add postgresql-libs && \
 apk add --virtual .build-deps gcc musl-dev postgresql-dev && \
 python3 -m pip install -r requirement.txt --no-cache-dir && \
 apk --purge del .build-deps

CMD ["gunicorn", "-b", "0.0.0.0:80", "-w", "2", "main:app"]
