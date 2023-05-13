FROM python:3.10-slim-bullseye

RUN apt-get update -y && apt-get install -y curl
RUN useradd -m apiuser
USER apiuser
WORKDIR /home/apiuser
ENV PATH="/home/apiuser/.local/bin:$PATH"

COPY --chown=apiuser:apiuser requirements.txt .
RUN pip install --upgrade pip && \
    pip install -r requirements.txt && \
    rm -rf .cache
COPY --chown=apiuser:apiuser src ./src
COPY --chown=apiuser:apiuser tests ./tests
ENV PYTHONPATH=/home/apiuser/src
