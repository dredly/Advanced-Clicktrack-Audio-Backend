import cloudinary
import cloudinary.uploader
import cloudinary.api

from dotenv import load_dotenv

load_dotenv()

config = cloudinary.config(secure=True)


def upload_file(filename: str) -> str:
    """Returns the https url of the file once it is uploaded to cloudinary"""

    # Cloudinary considers audio to be a subset of the video resource type
    upload_response = cloudinary.uploader.upload(
        filename, resource_type="video", folder="clicktracks"
    )

    try:
        return upload_response["secure_url"]
    except:
        return "error"
