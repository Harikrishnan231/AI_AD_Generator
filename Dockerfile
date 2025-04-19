# Use a base image that has Python pre-installed
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /app

# Install system dependencies (ffmpeg, espeak)
RUN apt-get update && apt-get install -y \
    ffmpeg \
    espeak \
    && apt-get clean

# Copy the application files into the container
COPY . .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose the port Streamlit will run on
EXPOSE 8501

# Start the Streamlit app
CMD ["streamlit", "run", "your_streamlit_script.py"]
