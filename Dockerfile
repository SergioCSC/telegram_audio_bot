# Define global args
ARG RUNTIME_VERSION="3.12.0a6"
ARG DISTRO_VERSION="bullseye"

FROM python:${RUNTIME_VERSION}-slim-${DISTRO_VERSION}

RUN apt update && apt install -y libstdc++6 build-essential libtool autoconf cmake && rm -rf /var/lib/apt/lists/*
#    libstdc++ \
#    build-base \ +
#    libtool \
#    autoconf \
#    automake \ +
#    make \ +
#    cmake \
#    libcurl +

ARG FUNCTION_DIR="/home/app/"

RUN mkdir -p ${FUNCTION_DIR}

RUN python${RUNTIME_VERSION} -m pip install awslambdaric  # --target ${FUNCTION_DIR}

COPY requirements.txt .
RUN python${RUNTIME_VERSION} -m pip install -r requirements.txt # --target ${FUNCTION_DIR}

COPY *.py ${FUNCTION_DIR}

WORKDIR ${LAMBDA_TASK_ROOT}

#RUN apt install pip \
#    & pip install -r requirements.txt
    # & apt uninstall pip
    # & rm -rf /var/lib/apt/lists/*

COPY opus/opus_linux/ ./opus/opus_linux/
COPY *.py .

ENV LD_LIBRARY_PATH=./opus/opus_linux/

ENTRYPOINT ["python", "-m", "awslambdaric"]

#COPY entry.sh /
#RUN chmod 755 /entry.sh
#ENTRYPOINT [ "./entry.sh" ]
CMD ["lambda_function.lambda_handler"]
#CMD ["sh"]
