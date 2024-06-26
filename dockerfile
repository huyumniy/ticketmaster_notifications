# Use an official Python runtime as a parent image
FROM python:3.8

ENV PYTHONUNBUFFERED=1

# Set the working directory in the container
WORKDIR /code

# Copy the current directory contents into the container at /app
COPY requirements.txt .

COPY . /code

# Install dependencies
RUN python -m venv venv && pip install -r requirements.txt

# Make port 80 available to the world outside this container
EXPOSE 5000

# Run app.py when the container launches
CMD ["python", "main.py"]
