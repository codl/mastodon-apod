IMAGE := ghcr.io/codl/mastodon-apod
CONTAINER := mastodon-apod
UID := $(shell id -u)

lock: requirements.txt dev-requirements.txt

requirements.txt: pyproject.toml
	uv pip compile -o $@ $<

dev-requirements.txt: dev-requirements.in requirements.txt
	uv pip compile -o $@ $<

docker:
	docker buildx build --target bot -t $(IMAGE) .

docker-rm:
	docker rm -f $(CONTAINER)


docker-run:
	docker run --name $(CONTAINER) -d --restart unless-stopped \
		-v ${PWD}/config/:/app/config --user $(UID) $(IMAGE)

up: docker docker-rm docker-run

test-docker:
	docker buildx build --target test -t $(IMAGE):test .
	docker run --rm $(IMAGE):test

.PHONY: docker up docker-rm docker-run test-docker lock
