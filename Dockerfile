# Use an official Python runtime as a parent image
FROM python:3.11-slim-bookworm

# Set the working directory in the container
WORKDIR /MoneyPrinterTurbo

# 设置/MoneyPrinterTurbo目录权限为777
RUN chmod 777 /MoneyPrinterTurbo

ENV PYTHONPATH="/MoneyPrinterTurbo"

# 本地用户默认继续优先使用国内镜像；GitHub Actions 发布 GHCR 镜像时使用 default，
# 避免海外 runner 访问国内镜像过慢导致镜像发布长时间卡住。
ARG DOCKER_BUILD_MIRROR=china
ARG PIP_USE_OFFICIAL=0

# Install system dependencies with retry logic
# The previous version of this step ended each attempt with
# `... && break || echo "retrying"`, so when every attempt failed the `echo`
# still returned 0 and the whole RUN succeeded. imagemagick was then absent,
# and the build died further down on a sed against a policy file that had
# never been created -- an error that pointed nowhere near the real cause.
# Track success explicitly and fail the build where the failure happens.
RUN set -eu; \
    apt_install() { \
        apt-get update && apt-get install -y --no-install-recommends \
            git imagemagick ffmpeg; \
    }; \
    if [ "$DOCKER_BUILD_MIRROR" = "china" ]; then \
        echo "deb http://mirrors.aliyun.com/debian bookworm main" > /etc/apt/sources.list; \
        echo "deb http://mirrors.aliyun.com/debian-security bookworm-security main" >> /etc/apt/sources.list; \
    else \
        echo "Using default Debian mirrors"; \
    fi; \
    installed=0; \
    for i in 1 2 3; do \
        echo "Attempt $i: installing system dependencies"; \
        if apt_install; then installed=1; break; fi; \
        echo "Attempt $i failed."; \
        if [ "$DOCKER_BUILD_MIRROR" = "china" ] && [ "$i" -eq 1 ]; then \
            echo "Switching to Tsinghua mirror"; \
            sed -i 's/mirrors.aliyun.com/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list; \
        elif [ "$DOCKER_BUILD_MIRROR" = "china" ] && [ "$i" -eq 2 ]; then \
            echo "Switching to default Debian mirrors"; \
            echo "deb http://deb.debian.org/debian bookworm main" > /etc/apt/sources.list; \
            echo "deb http://security.debian.org/debian-security bookworm-security main" >> /etc/apt/sources.list; \
        fi; \
        sleep 5; \
    done; \
    if [ "$installed" -ne 1 ]; then \
        echo "FATAL: could not install git/imagemagick/ffmpeg after 3 attempts." >&2; \
        exit 1; \
    fi; \
    rm -rf /var/lib/apt/lists/*

# Fix security policy for ImageMagick (MoviePy writes text via @-files, which
# the stock policy blocks). Debian 12 still ships ImageMagick 6; if a future
# base image moves to 7 this path changes, so say so rather than failing on a
# bare "sed: exit 2".
RUN policy=/etc/ImageMagick-6/policy.xml; \
    if [ ! -f "$policy" ]; then \
        echo "FATAL: $policy not found -- is imagemagick installed, and still v6?" >&2; \
        exit 1; \
    fi; \
    sed -i '/<policy domain="path" rights="none" pattern="@\*"/d' "$policy"

# Copy only the requirements.txt first to leverage Docker cache
COPY requirements.txt ./

# 本地默认优先国内 PyPI 镜像；GHCR 发布使用官方 PyPI，避免海外 runner 因跨境镜像访问变慢。
RUN if [ "$PIP_USE_OFFICIAL" = "1" ]; then \
        pip install --no-cache-dir --retries 3 --timeout 60 -r requirements.txt; \
    else \
        pip install --no-cache-dir -i https://mirrors.aliyun.com/pypi/simple/ --trusted-host mirrors.aliyun.com --retries 3 --timeout 60 -r requirements.txt || \
        pip install --no-cache-dir -i https://mirrors.tuna.tsinghua.edu.cn/pypi/web/simple/ --trusted-host mirrors.tuna.tsinghua.edu.cn --retries 3 --timeout 60 -r requirements.txt || \
        pip install --no-cache-dir --retries 3 --timeout 60 -r requirements.txt; \
    fi

# Now copy the rest of the codebase into the image
COPY . .

# Expose the port the app runs on
EXPOSE 8501

# Command to run the application
CMD ["streamlit", "run", "./webui/Main.py","--browser.serverAddress=127.0.0.1","--server.enableCORS=True","--browser.gatherUsageStats=False","--server.showEmailPrompt=False"]

# 1. Build the Docker image using the following command
# docker build -t moneyprinterturbo .

# 2. Run the Docker container using the following command
## For Linux or MacOS:
# docker run -v $(pwd)/config.toml:/MoneyPrinterTurbo/config.toml -v $(pwd)/storage:/MoneyPrinterTurbo/storage -p 127.0.0.1:8501:8501 moneyprinterturbo
## For Windows:
# docker run -v ${PWD}/config.toml:/MoneyPrinterTurbo/config.toml -v ${PWD}/storage:/MoneyPrinterTurbo/storage -p 127.0.0.1:8501:8501 moneyprinterturbo
