FROM python:3.10-slim-bullseye

RUN apt-get update -y && apt-get install -y curl gcc
RUN useradd -m apiuser
USER apiuser
WORKDIR /home/apiuser
ENV PATH="/home/apiuser/.local/bin:$PATH"

COPY --chown=apiuser:apiuser requirements.txt .
RUN pip install --upgrade pip && \
    pip install -r requirements.txt && \
    rm -rf .cache
COPY --chown=apiuser:apiuser setup.py ./
COPY --chown=apiuser:apiuser gomoku ./gomoku
COPY --chown=apiuser:apiuser tests ./tests
RUN python setup.py build_ext
ENV PYTHONPATH=/home/apiuser/gomoku
EXPOSE 8000
CMD ["uvicorn",  "gomoku.app:create_app", "--port", "8000", "--host", "0.0.0.0"]
