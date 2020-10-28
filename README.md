# ensiie-calendar-dl

A python script to extract my school calendar to a file using iCalendar format.

## Installation

```sh
git clone https://github.com/lrabane/ensiie-calendar-dl.git
cd ensiie-calendar-dl
pip install -r requirements.txt
```

## Usage

```sh
./ensiie_calendar_dl.py username password output.ics
```

## Docker

First, install [Docker](https://docs.docker.com/install/).

Build with: 
```shell script
docker build --rm -t calendar-dl .
```

Run with:
```shell script
docker run -v $HOME/cal:/cal --env USER=<your username> --env PASSWORD=<your password> calendar-dl 
```

Example [docker-compose](https://docs.docker.com/compose/install/) (recommended):
```yaml
version: '3.3'
services:
    calendar-dl:
        image: calendar-dl
        container_name: calendar-dl
        hostname: calendar-dl
        volumes:
            - /cal:/cal
        environment:
            - USER=<Your username>
            - PASSWORD=<Your password>
            - FILE_NAME=<file name>
```
`FILE_NAME` is optional, default is `output`. don't add the .ics extension, the dockerfile handles it.

## Public iCal link

Here is an nginx config file to make your calendar accessible to any online calendar that can handle the iCal format, like Google Calendar. It was made to work with [this nginx + let's encrypt image](https://hub.docker.com/r/linuxserver/swag). If you want to use a different nginx image, make sure to use correct ssl settings.

The calendar will be available at `ensiie-cal.<domain.tld>/FILE_NAME.ics`. The file name is effectively the password to access your calendar. You should make this secure (long and random).

```
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;

    include ssl.conf;

    client_max_body_size 0;

    add_header X-Robots-Tag "noindex, nofollow, nosnippet, noarchive";
    location = /robots.txt {
       add_header Content-Type text/plain;
       return 200 "User-agent: *\nDisallow: /\n";
    }

    ssl_client_certificate /config/keys/ca/ca.crt;
    ssl_verify_client optional;

    server_name ensiie-cal.<domain.tld>;
    location / {
        root /cal;
    }
}
```
