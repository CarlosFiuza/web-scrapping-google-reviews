#!/bin/bash

sudo docker build -t google-scraping .

sudo docker tag google-scraping:latest 044063568858.dkr.ecr.sa-east-1.amazonaws.com/google-review-scraping

sudo docker push 044063568858.dkr.ecr.sa-east-1.amazonaws.com/google-review-scraping

# tete local
# sudo docker run --platform linux/amd64 -p 9000:8080 google-scraping

# simula evento
# curl "http://localhost:9000/2015-03-31/functions/function/invocations" -d '{"store_id": 1}'