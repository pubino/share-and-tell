FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml README.md LICENSE ./
COPY src ./src

RUN pip install --no-cache-dir .

VOLUME ["/share", "/output"]

ENTRYPOINT ["share-and-tell"]
CMD ["--help"]
