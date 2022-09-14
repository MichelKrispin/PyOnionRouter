#!/usr/bin/sh
for SERVICE in $(gcloud run services list --format='value(name)')
do
    gcloud run services delete $SERVICE -q --region europe-west3
done