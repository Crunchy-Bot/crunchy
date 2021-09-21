FROM python:3.8

WORKDIR /app

COPY . .

RUN pip install poetry

RUN poetry config virtualenvs.create false \
  && poetry install $(test "$PRODUCTION" == production && echo "--no-dev") --no-interaction --no-ansi


ENTRYPOINT ["poetry", "run", "start"]

