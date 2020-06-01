# mastodon-apod

it's a mastodon bot that posts the most recent image from NASA's Astronomy Picture of the Day

it uses [ananas][]

it requires python 3.5 because ananas doesn't support higher versions

[ananas]: https://github.com/chr-1x/ananas

## how to use

* (optional) create a venv to isolate dependencies from the system

      $ python -m venv venv
      $ source venv/bin/activate

* install dependencies

      $ pip install -r requirements.txt

* fill in config file

      $ cp ananas.cfg.example ananas.cfg
      $ $EDITOR ananas.cfg

* run

      $ ananas ananas.cfg

* enjoy
