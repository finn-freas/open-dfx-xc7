FROM ubuntu:24.04

ARG DEVICES="xc7a50t"
ARG YOSYS="oss-cad-suite"
ARG JOBS="4"

RUN apt-get update \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        ca-certificates curl git tar gzip \
 && rm -rf /var/lib/apt/lists/*

RUN useradd -m -s /bin/bash ofx
USER ofx
WORKDIR /home/ofx/open-dfx-xc7
COPY --chown=ofx:ofx install/ install/

RUN bash install/install.sh --run --prefix /home/ofx/ofx --cache /home/ofx/.cache/ofx \
        --devices "$DEVICES" --yosys "$YOSYS" --jobs "$JOBS" \
 && rm -rf /home/ofx/.cache/ofx/build /home/ofx/.cache/ofx/work /home/ofx/.cache/ofx/mamba/pkgs \
           /home/ofx/.cache/ofx/dl/oss-cad-suite-*.tgz

COPY --chown=ofx:ofx flow/ flow/
COPY --chown=ofx:ofx designs/ designs/
RUN bash install/link_repo.sh --run --prefix /home/ofx/ofx --repo /home/ofx/open-dfx-xc7

ENV OFX_PREFIX=/home/ofx/ofx
ENV PATH=/home/ofx/ofx/bin:/home/ofx/ofx/opt/oss-cad-suite/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/home/ofx/ofx/py3bin
CMD ["bash"]
