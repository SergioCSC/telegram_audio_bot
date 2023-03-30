FROM public.ecr.aws/lambda/python:3.10

WORKDIR ${LAMBDA_TASK_ROOT}

COPY requirements.txt .

RUN apt install pip \
    & pip install -r requirements.txt
    # & apt uninstall pip
    # & rm -rf /var/lib/apt/lists/*

COPY opus_linux/ ./opus_linux/
COPY *.py .

ENV LD_LIBRARY_PATH=./opus_linux/

#COPY entry.sh .
#RUN chmod 755 ./entry.sh
#ENTRYPOINT [ "./entry.sh" ]
CMD ["lambda_function.lambda_handler"]
#CMD ["sh"]
