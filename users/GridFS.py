from mongoengine import GridFSProxy
import requests
from io import BytesIO

# Connect to the 'Recipe-z' database

class MediaFile:
    def __init__(self, file=None):
        self.file = file
        self.gridfs = GridFSProxy()

    def save(self, filename):
        """Save the file in GridFS and return the file_id."""
        if not self.file:
            raise ValueError("No file provided to save.")
        file_id = self.gridfs.put(self.file, filename=filename)
        return file_id

    def get(self, file_id):
        """Retrieve the file from GridFS using file_id."""
        file = self.gridfs.get(file_id)
        return file.read()

def download_and_store_image(url, filename):
    """Download an image from a URL and store it in GridFS."""

    # Download the image
    response = requests.get(url)
    response.raise_for_status()  # Ensure the request was successful

    # Save the image in GridFS
    image_data = BytesIO(response.content)
    media_file = MediaFile(file=image_data)
    file_id = media_file.save(filename)

    return media_file  # Return the MediaFile instance with the stored image
