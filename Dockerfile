# Use the official Python 3 Alpine image as the base image
FROM python:3.9

# Set environment variables
ENV SERVER_TO_MODERATION_CHANNEL=1:1

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements.txt file to the container
COPY requirements.txt .

# Install the dependencies from requirements.txt
RUN pip install -r requirements.txt

# Copy the rest of the application code to the container
COPY . .

# Run the application using the Python command
CMD ["python", "-m", "src.main"]