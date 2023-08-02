# mastodon-apod

it's a mastodon bot that posts the most recent image from NASA's Astronomy Picture of the Day

it uses [ananas][]

[ananas]: https://github.com/chr-1x/ananas

## how to use

this is only tested on python 3.10

you should run this from a [virtual environemnt][venv] or risk suffering
terrible dependency mismatches sometime in the future

[venv]: https://packaging.python.org/en/latest/guides/installing-using-pip-and-virtual-environments/#creating-a-virtual-environment

* install the package and its dependencies

      $ pip install .

* fill in config file

      $ cp config/ananas.cfg.example config/ananas.cfg
      $ $EDITOR config/ananas.cfg

* run

      $ ananas config/ananas.cfg

* enjoy

## how to use (docker)

* fill in config file

      $ cp config/ananas.cfg.example config/ananas.cfg
      $ $EDITOR config/ananas.cfg

* build

      $ docker buildx build -t mastodon-apod .
      $ # or, shortened:
      $ make docker

* stop and remove potential existing container

      $ docker rm -f mastodon-apod
      $ # or, shortened:
      $ make docker-rm

* and run

      $ docker run -n mastodon-apod -d --restart unless-stopped -v $(pwd)/config:/app/config --user $(id -u) mastodon-apod
      $ # or, shortened:
      $ make docker-run

these last three steps can be run at once with

      $ make up
