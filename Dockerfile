FROM python:3.9

WORKDIR /home/root/

RUN apt-get update && apt-get install -y vim
RUN pip install --upgrade pip && pip install pipenv
RUN mkdir ./logs/
COPY *.py logging.conf Pipfile Pipfile.lock .env ./
RUN pipenv install

ENTRYPOINT pipenv run main
