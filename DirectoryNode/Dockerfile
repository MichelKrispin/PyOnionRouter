FROM gcr.io/google.com/cloudsdktool/google-cloud-cli:alpine
RUN apk --update add python3 py3-pip

ENV PYTHONUNBUFFERED True

ENV APP_HOME /app
WORKDIR $APP_HOME
COPY . ./

RUN pip install --no-cache-dir -r requirements.txt

CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 main:app
