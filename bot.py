import os
import uuid
import json
import boto3
from datetime import datetime, timedelta, timezone
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
)
from dotenv import load_dotenv

load_dotenv()

dynamodb = boto3.resource("dynamodb")
scheduler = boto3.client("scheduler")

TABLE_NAME = "scheduled_jobs"
table = dynamodb.Table(TABLE_NAME)

BOT_TOKEN = os.environ["BOT_TOKEN"]
ADMIN_IDS = [int(x) for x in os.environ["ADMIN_IDS"].split(",")]

LAMBDA_ARN = os.environ["SENDER_LAMBDA_ARN"]
ROLE_ARN = os.environ["EVENTBRIDGE_ROLE_ARN"]


def create_one_time_schedule(job_id, send_at):
    scheduler.create_schedule(
        Name=f"job-{job_id}",
        ScheduleExpression=f"at({send_at})",
        Target={
            "Arn": LAMBDA_ARN,
            "RoleArn": ROLE_ARN,
            "Input": json.dumps({"job_id": job_id}),
        },
        FlexibleTimeWindow={"Mode": "OFF"},
    )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Hello! I'm Content Caster Bot 🚀\nUse /help to see commands."
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "/schedule <src_chat> <dest_chat> <start_id> <end_id> "
        "<YYYY-MM-DD-HH:MM:SS> <interval_hrs>\n"
        "/list_schedules\n"
        "/cancel_schedule <job_id>"
    )

async def info(update, context):
    message = update.message
    chat = update.effective_chat
    user = update.effective_user

    text = (
        f"📌 **Chat Info**\n\n"
        f"**Chat ID:** `{chat.id}`\n"
        f"**Chat Type:** `{chat.type}`\n"
        f"**Your User ID:** `{user.id}`\n"
    )

    if message.reply_to_message:
        text += f"**Replied Message ID:** `{message.reply_to_message.id}`\n"

    await message.reply_text(text, parse_mode="Markdown")

async def list_schedules(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if user_id not in ADMIN_IDS:
        await update.message.reply_text("Not authorized")
        return

    response = table.scan(
        FilterExpression="created_by = :uid",
        ExpressionAttributeValues={":uid": user_id},
    )

    items = response.get("Items", [])

    if not items:
        await update.message.reply_text("No active schedules.")
        return

    text = "📋 Active Schedules:\n\n"

    for item in items[:20]:
        text += (
            f"Job ID: `{item['job_id']}`\n"
            f"{item['src_chat']} → {item['dest_chat']}\n"
            f"Msg ID: {item['message_id']}\n"
            f"At: {item['send_at']}\n\n"
        )

    await update.message.reply_text(text, parse_mode="Markdown")


async def cancel_schedule(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if user_id not in ADMIN_IDS:
        await update.message.reply_text("Not authorized")
        return

    if len(context.args) != 1:
        await update.message.reply_text("Usage: /cancel_schedule <job_id>")
        return

    job_id = context.args[0]

    table.delete_item(Key={"job_id": job_id})

    try:
        scheduler.delete_schedule(Name=f"job-{job_id}")
    except Exception:
        pass

    await update.message.reply_text("✅ Schedule cancelled.")


async def schedule(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    user_id = update.effective_user.id

    if user_id not in ADMIN_IDS:
        await message.reply_text("Not authorized")
        return

    try:
        args = context.args

        src = int(args[0])
        dest = int(args[1])
        start_id = int(args[2])
        end_id = int(args[3])
        start_time = datetime.strptime(args[4], "%Y-%m-%d-%H:%M:%S")
        interval = timedelta(hours=int(args[5]))

        current_time = start_time.replace(tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)

        await message.reply_text("Scheduling started...")

        for mid in range(start_id, end_id + 1):

            job_id = str(uuid.uuid4())
            send_time = current_time

            if send_time <= now:
                send_time = now + timedelta(seconds=5)

            table.put_item(Item={
                "job_id": job_id,
                "src_chat": str(src),
                "dest_chat": str(dest),
                "message_id": mid,
                "send_at": send_time.isoformat(),
                "created_by": user_id,
            })

            create_one_time_schedule(
                job_id,
                send_time.strftime("%Y-%m-%dT%H:%M:%S")
            )

            current_time += interval

    except Exception as e:
        await message.reply_text(f"Error: {e}")


def build_app():
    return (
        ApplicationBuilder()
        .token(BOT_TOKEN)
        .build()
    )
