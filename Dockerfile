FROM ubuntu

#Install dependencies necessary for wav synthesis from midi
RUN apt-get update -y \
	#Install dependencies necessary for wav synthesis from midi
	&& apt-get install -y fluidsynth timidity \
	#Install pip for managing pythonpackages
	python3-pip

WORKDIR /app

COPY ./requirements.txt requirements.txt

RUN pip install -r requirements.txt

COPY . .

EXPOSE 5000

#CMD ["python3", "-m" , "flask", "run", "--host=0.0.0.0"]
CMD gunicorn wsgi:app