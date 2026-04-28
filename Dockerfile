FROM python:3.13.13-slim-bookworm

# 设置时区和编码环境变量
ENV TZ=Asia/Shanghai \
    LC_ALL=C.UTF-8 \
    LANG=C.UTF-8 \
    # 禁用 PIP 进度条
    PIP_PROGRESS_BAR=off \
    # 设置非交互模式，避免安装时的交互提示
    DEBIAN_FRONTEND=noninteractive

WORKDIR /data/solve-backend

ARG INDEX_URL="https://pypi.org/simple/"
ARG TRUSTED_HOST="pypi.org"

RUN ln -fs /usr/share/zoneinfo/Asia/Shanghai /etc/localtime && \
    echo "Asia/Shanghai" > /etc/timezone

COPY requirements3.13.txt ./
RUN pip install --no-cache-dir \
    -r requirements3.13.txt \
    --index-url ${INDEX_URL} \
    --trusted-host ${TRUSTED_HOST} \
    || echo "install complete"

COPY . .

RUN cp deploy.conf.sample deploy.conf && \
    mv db.sqlite3.demo db.sqlite3

RUN chmod 755 docker-entrypoint.sh && \
    ln -s /data/solve-backend/docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh

ENV REDIS_HOST=127.0.0.1 \
    REDIS_PORT=6379
    # REDIS_PASSWORD=xxx

EXPOSE 8000

CMD ["docker-entrypoint.sh"]
