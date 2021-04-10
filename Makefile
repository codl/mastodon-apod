IMAGE := mastodon-apod
CONTAINER := mastodon-apod
UID := $(shell id -u)

docker:
	docker build -t $(IMAGE) .

docker-rm:
	docker rm -f $(CONTAINER)

docker-run:
	docker run --name $(CONTAINER) -d --restart unless-stopped \
		-v ${PWD}/config/:/app/config --user $(UID) $(IMAGE)

up: docker docker-rm docker-run

.PHONY: docker up docker-rm docker-run
