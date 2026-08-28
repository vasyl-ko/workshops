# The "bottom of the stack" demo from the slides: an image built FROM scratch.
# scratch = the empty image. No shell, no libc — only static binaries run.
#
# The busybox binary isn't committed; extract it from the (fully static)
# busybox:musl image first:
#
#   docker create busybox:musl                # prints a container id
#   docker cp <id>:/bin/busybox .
#   docker rm <id>
#
#   docker build -f scratch.Dockerfile -t scratch-test .
#   docker run --rm scratch-test              # → "hello from scratch"
#   docker images scratch-test                # ~2 MB
#
# Try the default `busybox` image instead of busybox:musl to see the famous
# failure: it's dynamically linked, and scratch has no linker to run it —
# "exec /busybox: no such file or directory".
FROM scratch

COPY busybox /busybox

ENTRYPOINT ["/busybox", "echo", "hello from scratch"]
