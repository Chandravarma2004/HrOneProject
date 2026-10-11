
import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from pymongo import AsyncMongoClient

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI")
DATABASE_NAME = os.getenv(
    "MONGODB_DATABASE",
    "hrone_attendance"
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    if not MONGODB_URI:
        raise RuntimeError(
            "MONGODB_URI is missing from the .env file"
        )

    client = AsyncMongoClient(MONGODB_URI)

    try:
        # Check the MongoDB connection
        await client.admin.command("ping")

        # Make the client and database available to FastAPI
        app.state.mongo_client = client
        app.state.db = client[DATABASE_NAME]

        print("MongoDB connected successfully!")

        yield

    finally:
        await client.close()
        print("MongoDB connection closed.")
