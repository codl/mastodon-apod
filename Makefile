IMAGE := ghcr.io/codl/mastodon-apod
CONTAINER := mastodon-apod
UID := $(shell id -u)

docker:
	docker buildx build --target bot -t $(IMAGE) .

docker-rm:
	docker rm -f $(CONTAINER)


docker-run:
	docker run --name $(CONTAINER) -d --restart unless-stopped \
		-v ${PWD}/config.toml:/config.toml --user $(UID) $(IMAGE)

up: docker docker-rm docker-run

test-docker:
	docker buildx build --target test -t $(IMAGE):test .
	docker run --rm $(IMAGE):test

sync:
	uv sync --all-extras

test: sync
	uv run python -m pytest

coverage: sync
	uv run python -m coverage run --source=src -m pytest
	uv run python -m coverage report

.PHONY: docker up docker-rm docker-run test-docker coverage test sync
