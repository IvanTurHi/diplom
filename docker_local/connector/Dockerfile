FROM python:3.8-alpine
WORKDIR /code
ADD requirements.txt requirements.txt
RUN pip install -r requirements.txt
RUN pip install psycopg2-binary
#RUN pip install pandas
COPY toPostgresDB.py toPostgresDB.py
COPY toMongoDB.py toMongoDB.py
COPY apiconnector.py apiconnector.py
