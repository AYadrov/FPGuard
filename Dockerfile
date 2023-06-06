FROM ubuntu:focal

MAINTAINER Artem Yadrov

ENV HOME=/home

RUN apt update

RUN pip install --upgrade pip
RUN pip install pyinterval numpy bigfloat sly

WORKDIR /home
RUN git clone https://github.com/AYadrov/FPGuard

ENV SAT_ROOT=$HOME/Satire
