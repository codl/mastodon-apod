# mastodon-apod

it's a ~~mastodon~~ gotosocial bot that posts the most recent image from NASA's Astronomy Picture of the Day

it lives at https://reentry.codl.fr/users/apod

## running it

first, fill in the config file:

```
$ cd mastodon-apod
$ cp config.example.toml config.toml
$ $EDITOR config.toml
```

i would recommend using [uv][] to run the bot, it manages python versions and the bot's dependencies automatically

```
$ uv run -m apod config.toml
```

[uv]: https://docs.astral.sh/uv/
