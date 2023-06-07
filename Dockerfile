FROM ubuntu:focal

MAINTAINER Artem Yadrov

ENV HOME=/home

ARG DEBIAN_FRONTEND=noninteractive
ENV TZ=US

RUN apt update
RUN apt-get install -y python2.7 flex bison gcc g++ make pkg-config libmpfr-dev git python3 wget vim python3-pip

RUN pip install --upgrade pip
RUN pip install pyinterval numpy bigfloat sly symengine sympy ply

WORKDIR /home
RUN git clone https://github.com/AYadrov/FPGuard

ENV SAT_ROOT=$HOME/FPGuard
