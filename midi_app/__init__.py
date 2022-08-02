from dotenv import load_dotenv

load_dotenv()

import os
from flask import Flask
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
if os.environ["FLASK_ENV"] == "production":
    CORS(app, origins=["https://clicktrack-redux.vercel.app"])

from midi_app import routes
