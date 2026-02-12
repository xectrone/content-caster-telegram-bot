import os
import json
import boto3
from telegram import Bot
from dotenv import load_dotenv

load_dotenv()

dynamodb = boto3.resource("dynamodb")
scheduler = boto3.client("scheduler")

table = dynamodb.Table("scheduled_jobs")

BOT_TOKEN = os.environ["BOT_TOKEN"]
bot = Bot(token=BOT_TOKEN)


def lambda_handler(event, context):

    job_id = event["job_id"]

    response = table.get_item(Key={"job_id": job_id})

    if "Item" not in response:
        return

    job = response["Item"]

    src = int(job["src_chat"])
    dest = int(job["dest_chat"])
    mid = int(job["message_id"])

    try:
        bot.forward_message(chat_id=dest, from_chat_id=src, message_id=mid)
    except Exception:
        pass

    table.delete_item(Key={"job_id": job_id})

    try:
        scheduler.delete_schedule(Name=f"job-{job_id}")
    except Exception:
        pass
