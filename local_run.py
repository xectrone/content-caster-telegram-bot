from bot import build_app, start, help_command, schedule, list_schedules, cancel_schedule, info
from bot import build_app, start, help_command

from telegram.ext import CommandHandler

def main():

    app = build_app()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("info", info))
    app.add_handler(CommandHandler("schedule", schedule))
    app.add_handler(CommandHandler("list_schedules", list_schedules))
    app.add_handler(CommandHandler("cancel_schedule", cancel_schedule))
    
    print("✅ Bot running locally (polling mode)")
    app.run_polling()

if __name__ == "__main__":
    main()
   
