# Chat app realtime -Camel chat

Use django to build backend

## Some Features

- Public chat for all user
- Friend system and private chat (messages, files, images)
- Video call with other people

## Requirement

- [python](https://www.python.org)
- [docker](https://www.docker.com)

## Usage

Install requred modules
```sh
pip install -r require_fix.txt
```
Run redis with docker
```sh
sudo docker run -p 6379:6379 -d redis:5
```
Run server
```sh
python manage.py runserver
```

