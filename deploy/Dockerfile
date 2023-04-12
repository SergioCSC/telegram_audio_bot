ARG RUNTIME_VERSION="3.12.0a6"
ARG DISTRO_VERSION="bullseye"

FROM python:${RUNTIME_VERSION}-slim-${DISTRO_VERSION}

RUN apt update && apt install -y libstdc++6 build-essential libtool autoconf cmake lame

COPY deploy/requirements.txt .
RUN python${RUNTIME_VERSION} -m pip install awslambdaric
RUN python${RUNTIME_VERSION} -m pip install -r requirements.txt

WORKDIR ${LAMBDA_TASK_ROOT}

COPY opus/opus_linux/ ./opus/opus_linux/
COPY *.py .

ENV LD_LIBRARY_PATH=./opus/opus_linux/

ENTRYPOINT ["python", "-m", "awslambdaric"]

CMD ["lambda_function.lambda_handler"]
