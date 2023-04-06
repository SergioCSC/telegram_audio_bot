FROM python:3.12.0a6-slim-bullseye

WORKDIR /opt

COPY requirements.txt .

RUN apt install pip \
    & pip install -r requirements.txt
    # & apt uninstall pip
    # & rm -rf /var/lib/apt/lists/*

COPY opus_linux/ ./opus_linux/
COPY *.py .

ENV LD_LIBRARY_PATH=./opus_linux/

CMD python lambda_function.py
