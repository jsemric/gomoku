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
COPY --chown=apiuser:apiuser src ./src
COPY --chown=apiuser:apiuser tests ./tests
RUN cd src && python setup.py build_ext --inplace
ENV PYTHONPATH=/home/apiuser/src
EXPOSE 8000
CMD ["uvicorn",  "src.app:create_app", "--port", "8000", "--host", "0.0.0.0"]
