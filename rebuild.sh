#!/bin/sh
docker build -t ubuntu-audio-backend .
docker run -p 5001:5000 ubuntu-audio-backend