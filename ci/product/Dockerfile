FROM ubuntu:22.04
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y \
    software-properties-common \
    tzdata \
    && ln -fs /usr/share/zoneinfo/Etc/UTC /etc/localtime \
    && dpkg-reconfigure --frontend noninteractive tzdata \
    && add-apt-repository ppa:deadsnakes/ppa \
    && apt-get update \
    && apt-get install -y python3.11 python3.11-venv python3.11-dev python3-pip

WORKDIR /app

COPY . /app

RUN pip3 install -r requirements.txt
RUN pip3 install gunicorn

RUN groupadd -g 201 mts \
    && useradd -u 175345366 -g mts -d /app xl061876 \
    && chown xl061876:mts -R /app

USER xl061876

ENV FLASK_APP=/app/app.py
ENV REDIS_OM_URL=redis://shorturl:shorturl@redis-stack-server-master.vsanperf-shorturl.svc.cluster.local:6379

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
