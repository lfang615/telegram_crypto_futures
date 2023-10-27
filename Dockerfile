# Use an official Python runtime as a parent image
FROM python:3.9-slim-buster

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Make port 8000 available to the world outside this container
# (Optional, only if your bot needs to expose a port, e.g., for a webhook)
# EXPOSE 8000

# Define environment variable if needed
# ENV NAME World

# Run the bot script when the container launches
CMD ["python", "telegram_bot.py"]
