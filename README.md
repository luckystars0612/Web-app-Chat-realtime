# Chat app realtime -Camel chat

Use django to build backend

## Some Features

- Realtime message and notification
- Public chat for all user
- Friend system and private chat (messages, files, images)
- Video call with other people
- Chat with BOT simsimi

## Requirement

- [python](https://www.python.org)
- [docker](https://www.docker.com)

## Usage

Install required modules
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

