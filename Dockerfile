FROM python:3

ENV FILE_NAME output

ADD ensiie_calendar_dl.py /
ADD requirements.txt /

RUN pip install -r requirements.txt

CMD /usr/local/bin/python /ensiie_calendar_dl.py $USER $PASSWORD /cal/$FILE_NAME.ics loop
