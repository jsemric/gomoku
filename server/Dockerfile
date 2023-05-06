FROM python:3.9-slim-bullseye

RUN apt-get update -y && apt-get install -y curl gcc
RUN useradd -m apiuser
USER apiuser
WORKDIR /home/apiuser
ENV PATH="/home/apiuser/.local/bin:$PATH"

COPY --chown=apiuser:apiuser requirements.txt .
RUN pip install --upgrade pip && \
    pip install -r requirements.txt && \
    rm -rf .cache
COPY --chown=apiuser:apiuser src ./src
# RUN cd src && python setup.py build_ext --inplace
COPY --chown=apiuser:apiuser tests ./tests
ENV PYTHONPATH=/home/apiuser/src
