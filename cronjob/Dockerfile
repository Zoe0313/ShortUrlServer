FROM ubuntu:22.04
ENV DEBIAN_FRONTEND=noninteractive

# Install required tools: curl, python3, pip, and kubectl
RUN apt-get update && apt-get install -y \
    curl \
    python3 \
    python3-pip \
    && apt-get clean

# Download and install kubectl
RUN curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl" && \
    install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl && \
        rm kubectl

# Set environment to avoid pip warnings
ENV PIP_ROOT_USER_ACTION=ignore

# upgrade python, install python lib
RUN python3 -m pip install --upgrade pip

# set work directory
WORKDIR /url-shortener
ENV PYTHONPATH /url-shortener/
COPY . /url-shortener

RUN groupadd -g 201 mts \
    && useradd -u 175345366 -g mts -d /url-shortener xl061876 \
    && chown xl061876:mts -R /url-shortener

USER xl061876

CMD ["/bin/bash"]
