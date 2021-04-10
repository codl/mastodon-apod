.PHONY: docker up docker-rm docker-run

IMAGE = mastodon-apod
CONTAINER = mastodon-apod

docker:
	docker build -t $(IMAGE) .

docker-rm:
	docker rm -f $(CONTAINER)

docker-run:
	docker run --name $(CONTAINER) -d --restart unless-stopped \
		-v ${PWD}/ananas.cfg:/app/ananas.cfg $(IMAGE)

up: docker docker-rm docker-run
