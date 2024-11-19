FROM ubuntu:22.04
ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    software-properties-common \
    tzdata \
    && ln -fs /usr/share/zoneinfo/Etc/UTC /etc/localtime \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

RUN add-apt-repository ppa:deadsnakes/ppa \
    && apt-get update \
    && apt-get install -y python3.11 python3.11-venv python3.11-dev python3-pip \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /url-shortener

COPY . /url-shortener

RUN pip3 install --no-cache-dir -r requirements.txt
RUN pip3 install --no-cache-dir gunicorn

RUN groupadd -g 201 mts \
    && useradd -u 175345366 -g mts -d /url-shortener xl061876 \
    && chown xl061876:mts -R /url-shortener

USER xl061876

ENV FLASK_APP=/url-shortener/app.py
ENV REDIS_OM_URL=redis://shorturl:shorturl@redis-stack-server-master.vsandevstg-shorturl.svc.cluster.local:6379

CMD ["gunicorn", "-w", "2", "-k", "sync", "-b", "0.0.0.0:5000", "app:app"]
