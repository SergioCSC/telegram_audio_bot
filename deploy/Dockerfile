# syntax=docker/dockerfile:1.7-labs 

ARG RUNTIME_VERSION="3.12.4"
ARG DISTRO_VERSION="bookworm"
ARG FUNCTION_DIR="/function"

FROM python:${RUNTIME_VERSION}-slim-${DISTRO_VERSION} as build

ARG RUNTIME_VERSION
ARG FUNCTION_DIR

RUN apt update && apt install -y libstdc++6 build-essential libtool autoconf cmake lame

COPY deploy/requirements.txt .
RUN python -m pip install --target ${FUNCTION_DIR} awslambdaric
RUN python -m pip install --target ${FUNCTION_DIR} -r requirements.txt \
    && rm -f ${FUNCTION_DIR}/googleapiclient/discovery_cache/documents/*.json \
    && rm -rf ${FUNCTION_DIR}/selenium/webdriver/common/macos/ \
    ${FUNCTION_DIR}/selenium/webdriver/common/windows/ \
    ${FUNCTION_DIR}/selenium/webdriver/common/devtools/ \
    ${FUNCTION_DIR}/pandas/tests/ \
    ${FUNCTION_DIR}/speech_recognition/ \
    ${FUNCTION_DIR}/numpy/_core/tests/ \
    ${FUNCTION_DIR}/yt_dlp/extractor/__pycache__/
    # && rm -rf ${FUNCTION_DIR}/yt_dlp/extractor/__pycache__/

FROM python:${RUNTIME_VERSION}-slim-${DISTRO_VERSION}


ARG FUNCTION_DIR
WORKDIR ${FUNCTION_DIR}

RUN apt-get update && apt-get install -y lame \
    # && apt-get clean 
    && rm -rf /var/lib/apt/lists/*
    # && rm -f /var/cache/apt/archives/*.deb \
    #    /var/cache/apt/archives/partial/*.deb /var/cache/apt/*.bin
    # || true all: 50.92 mb clean only: 64.85 mb /lists only: 50.92 mb

COPY --from=build ${FUNCTION_DIR} ${FUNCTION_DIR}
# 50.37 mb
# COPY --from=build /usr/bin/lame /usr/bin/lame
# COPY --from=build usr/lib/x86_64-linux-gnu/libmp3lame.so.0.0.0 /usr/lib/x86_64-linux-gnu/libmp3lame.so.0
# COPY --from=build usr/lib/x86_64-linux-gnu/libsndfile.so.1.0.31 /usr/lib/x86_64-linux-gnu/libsndfile.so.1
# COPY --from=build usr/lib/x86_64-linux-gnu/libFLAC.so.8.3.0 /usr/lib/x86_64-linux-gnu/libFLAC.so.8
# COPY --from=build usr/lib/x86_64-linux-gnu/libvorbis.so.0.4.9 /usr/lib/x86_64-linux-gnu/libvorbis.so.0
# COPY --from=build usr/lib/x86_64-linux-gnu/libvorbisenc.so.2.0.12 /usr/lib/x86_64-linux-gnu/libvorbisenc.so.2

COPY opus/opus_linux/ ./opus/opus_linux/
COPY *.py ./

ENV LD_LIBRARY_PATH=./opus/opus_linux/

ENTRYPOINT ["python", "run.py"]