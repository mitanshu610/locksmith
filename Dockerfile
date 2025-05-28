FROM ubuntu:22.04

RUN apt-get update -y \
    && apt-get upgrade -y \
    && apt-get dist-upgrade -y \
    && apt-get install -y --no-install-recommends \
    wget \
    python3-pip \
    python3-setuptools \
    && cd /usr/local/bin \
    && pip3 --no-cache-dir install --upgrade pip \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
    curl \
    openssh-server \
    git \
    librdkafka-dev \
    bash \
    g++ \
    build-essential && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

RUN apt-get remove --purge -y linux-libc-dev


WORKDIR /srv/locksmith

COPY ./requirements/requirements.txt .

RUN pip3 install --upgrade pip setuptools wheel && pip3 install -r ./requirements.txt


WORKDIR /srv/almanac
RUN mkdir /srv/almanac/repos
EXPOSE 8000

ENTRYPOINT ["python3", "entrypoint.py"]