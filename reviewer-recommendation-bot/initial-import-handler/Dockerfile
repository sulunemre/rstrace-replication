FROM python:3.7.3
COPY . /initial-import-handler/
RUN cd initial-import-handler && pip install -r requirements.txt
CMD cd initial-import-handler && \
    python import.py