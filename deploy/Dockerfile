ARG RUNTIME_VERSION="3.11.3"
ARG DISTRO_VERSION="bullseye"
ARG FUNCTION_DIR="/function"

FROM python:${RUNTIME_VERSION}-slim-${DISTRO_VERSION} as build

ARG RUNTIME_VERSION
ARG FUNCTION_DIR

RUN apt update && apt install -y libstdc++6 build-essential libtool autoconf cmake lame

COPY deploy/requirements.txt .
RUN python -m pip install --target ${FUNCTION_DIR} awslambdaric
RUN python -m pip install --target ${FUNCTION_DIR} -r requirements.txt

FROM python:${RUNTIME_VERSION}-slim-${DISTRO_VERSION}


ARG FUNCTION_DIR
WORKDIR ${FUNCTION_DIR}

# RUN apt install -y lame

COPY --from=build ${FUNCTION_DIR} ${FUNCTION_DIR}
COPY --from=build /usr/bin/lame /usr/bin/lame
COPY --from=build usr/lib/x86_64-linux-gnu/libmp3lame.so.0.0.0 /usr/lib/x86_64-linux-gnu/libmp3lame.so.0
COPY --from=build usr/lib/x86_64-linux-gnu/libsndfile.so.1.0.31 /usr/lib/x86_64-linux-gnu/libsndfile.so.1
COPY --from=build usr/lib/x86_64-linux-gnu/libFLAC.so.8.3.0 /usr/lib/x86_64-linux-gnu/libFLAC.so.8
COPY --from=build usr/lib/x86_64-linux-gnu/libvorbis.so.0.4.9 /usr/lib/x86_64-linux-gnu/libvorbis.so.0
COPY --from=build usr/lib/x86_64-linux-gnu/libvorbisenc.so.2.0.12 /usr/lib/x86_64-linux-gnu/libvorbisenc.so.2

COPY opus/opus_linux/ ./opus/opus_linux/
COPY *.py .

ENV LD_LIBRARY_PATH=./opus/opus_linux/

ENTRYPOINT ["python", "-m", "awslambdaric"]

CMD ["lambda_function.lambda_handler"]
