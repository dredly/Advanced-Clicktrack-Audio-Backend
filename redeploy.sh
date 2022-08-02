#!/bin/sh
heroku container:login
heroku container:push web --app clicktrack-audio-backend
heroku container:release web --app clicktrack-audio-backend
