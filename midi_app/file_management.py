import cloudinary
import cloudinary.uploader
import cloudinary.api

import multiprocessing as mp
import time

from dotenv import load_dotenv

from .log import log

load_dotenv()

config = cloudinary.config(secure=True)


DELETE_TIMEOUT = 15 * 60 # Automatically deletes the track from cloudinary after 15 minutes

def delete_file_after_timeout(public_id):
    time.sleep(DELETE_TIMEOUT)
    cloudinary.uploader.destroy(public_id, resource_type = 'video')
    log(f'Deleted {public_id}')
    return

def upload_file(filename: str) -> str:
    """Returns the https url of the file once it is uploaded to cloudinary"""

    print("Uploading file", filename)
    # Cloudinary considers audio to be a subset of the video resource type
    upload_response = cloudinary.uploader.upload(
        filename, resource_type="video", folder="clicktracks"
    )

    mp.Process(target=delete_file_after_timeout, args=(upload_response['public_id'],)).start()

    try:
        return upload_response["secure_url"]
    except:
        return "error"
