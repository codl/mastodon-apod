group "default" {
    targets = ["main"]
}

target "main" {
    dockerfile = "Dockerfile"
    tags = ["mastodon-apod"]
}

target "test" {
    inherits = ["main"]
    target = "test"
    tags = ["mastodon-apod:test"]
}
