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

# RUN pip3 install gunicorn

WORKDIR /app

COPY . /app

RUN pip3 install -r requirements.txt

RUN useradd -u 175345366 xl061876
RUN groupadd -g 201 mts
RUN usermod -d /app xl061876
RUN usermod -g mts xl061876
RUN chown xl061876:mts -R /app
USER xl061876

ENV FLASK_APP=/app/app.py
ENV REDIS_OM_URL=redis://shorturl:shorturl@vsanperf-shorturl-db.vdp.lvn.broadcom.net:6379

CMD ["flask", "run", "--host", "0.0.0.0", "--port", "5000"]

# CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
