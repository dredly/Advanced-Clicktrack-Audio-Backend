#!/bin/sh
docker build -t ubuntu-audio-backend .
docker run -p 5000:5000 ubuntu-audio-backend