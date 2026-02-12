import json
from bot import build_app, start, help_command, schedule, list_schedules, cancel_schedule
from telegram import Update
from telegram.ext import CommandHandler

app = build_app()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("help", help_command))
app.add_handler(CommandHandler("schedule", schedule))
app.add_handler(CommandHandler("list_schedules", list_schedules))
app.add_handler(CommandHandler("cancel_schedule", cancel_schedule))


def lambda_handler(event, context):
    body = json.loads(event["body"])
    update = Update.de_json(body, app.bot)
    app.process_update(update)
    return {"statusCode": 200, "body": "ok"}
