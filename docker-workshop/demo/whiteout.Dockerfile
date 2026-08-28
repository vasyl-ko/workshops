# Whiteout demo — proof that deleting a file does NOT shrink an image.
# Layers are append-only diffs: the `rm` layer is a 4 kB whiteout marker,
# while the 105 MB written by `dd` still ships in the previous layer.
#
#   docker build -f whiteout.Dockerfile -t notes:whiteout .
#   docker images notes:whiteout     # ~119 MB, despite the rm (alpine is ~8 MB)
#   docker history notes:whiteout    # see the 105 MB layer and the 4.1 kB "rm" layer
#   dive notes:whiteout              # the whiteout is visible in the layer diff
FROM alpine:3.20

RUN dd if=/dev/zero of=/big.bin bs=1M count=100

RUN rm /big.bin
