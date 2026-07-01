FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml README.md LICENSE ./
COPY src ./src

RUN python -m pip install --no-cache-dir .

USER 10001:10001

ENTRYPOINT ["tracebench"]
CMD ["--help"]
