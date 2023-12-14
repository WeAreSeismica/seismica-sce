FROM pandoc/core:3.1-ubuntu

ENV PYTHONUNBUFFERED=1
RUN apt update && apt install -y \
	software-properties-common \
	git \
	gcc \
	ruby-dev \
	libmagic1 \
	&& add-apt-repository ppa:deadsnakes/ppa \
	&& apt update && apt install -y \
	python3.10 \
	python3-distutils \
	python3-pip \
	python3-apt

RUN gem install anystyle-cli
RUN python3 -m pip install pip --upgrade pip
RUN python3 -m pip install pip --upgrade --no-cache \
	pip \
	setuptools \
	numpy \
        habanero \
        python-dateutil \
	git+https://github.com/WeAreSeismica/biblib

WORKDIR /data
