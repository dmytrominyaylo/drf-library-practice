import sys
import os
import django
import datetime
import logging
from os import getenv
from dotenv import load_dotenv
from asgiref.sync import sync_to_async
from telegram import Bot, Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "library_service.settings")
django.setup()

from borrowings.models import Borrowing  # noqa: E402
from payments.models import Payment  # noqa: E402
from django.contrib.auth import get_user_model  # noqa: E402
User = get_user_model()

load_dotenv()

TOKEN = getenv("BOT_TOKEN")
CHAT_ID = getenv("CHAT_ID")

bot = Bot(token=TOKEN)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)


def send_notification(message: str):
    try:
        bot.send_message(chat_id=CHAT_ID, text=message, parse_mode="HTML")
        logging.info("Message sent to Telegram")
    except Exception as e:
        logging.error(f"Failed to send Telegram message: {e}")


def borrowing_create_notification(borrowing: Borrowing):
    user = borrowing.user
    book = borrowing.book
    message = (
        f"<b>New borrowing created!</b>\n"
        f"User: {user.email}\n"
        f"Book: {book.title} ({book.inventory - 1} left)\n"
        f"Expected return date: {borrowing.expected_return_date}\n"
    )
    send_notification(message)


def check_overdue_borrowings():
    today = datetime.date.today()
    logging.info(f"Checking overdue borrowings for date: {today}")

    overdue_borrowings = Borrowing.objects.filter(
        expected_return_date__lt=today,
        actual_return_date__isnull=True,
    )

    logging.info(f"Found {overdue_borrowings.count()} overdue borrowings")

    if overdue_borrowings.exists():
        for borrowing in overdue_borrowings:
            message = (
                f"<b>Overdue borrowing alert!</b>\n"
                f"User: {borrowing.user.email}\n"
                f"Book: {borrowing.book.title}\n"
                f"Expected return: {borrowing.expected_return_date}"
            )
            logging.info(f"Sending notification: {message}")
            send_notification(message)
    else:
        logging.info("No overdue borrowings found, sending no-overdue message")
        send_notification("📢 No borrowings overdue today!")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hello! I'm your library bot.")


@sync_to_async
def run_check():
    check_overdue_borrowings()


async def handle_checkoverdue(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await run_check()
    await update.message.reply_text("✅ Overdue books check sent to the admin.")


async def getchatid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    await update.message.reply_text(f"Your chat ID is: {chat_id}")


async def testchat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    await update.message.reply_text(f"Your chat id is {chat_id}")
    global CHAT_ID
    CHAT_ID = chat_id
    logging.info(f"Chat ID set to {CHAT_ID}")


async def hello(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hello from test command!")


async def mybooks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = update.message.from_user.id
    try:
        user = await sync_to_async(User.objects.get)(telegram_id=telegram_id)
    except User.DoesNotExist:
        await update.message.reply_text(
            "Sorry, you are not found in the system. Please register or contact the admin."
        )
        return

    borrowings = await sync_to_async(
        lambda: list(
            Borrowing.objects.filter(user=user, actual_return_date__isnull=True).select_related("book")
        )
    )()

    if not borrowings:
        await update.message.reply_text("You have no borrowed books.")
        return

    response_text = "Your borrowed books:\n"
    for borrowing in borrowings:
        def is_paid(borrowing):
            return Payment.objects.filter(
                borrowing=borrowing,
                type_field="PAYMENT",
                status="PAID"
            ).exists()

        paid = await sync_to_async(is_paid)(borrowing)
        paid_text = "paid" if paid else "not paid"
        response_text += f"- {borrowing.book.title} (Payment status: {paid_text})\n"

    await update.message.reply_text(response_text)


async def fines(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = update.message.from_user.id
    try:
        user = await sync_to_async(User.objects.get)(telegram_id=telegram_id)
    except User.DoesNotExist:
        await update.message.reply_text(
            "Sorry, you are not found in the system. Please register or contact the admin."
        )
        return

    payments = await sync_to_async(
        lambda: list(Payment.objects.filter(
            borrowing__user=user,
            type_field="FINE"
        ).select_related("borrowing", "borrowing__book"))
    )()

    if not payments:
        await update.message.reply_text("You have no fines.")
        return

    response_text = "Your fines:\n"
    for payment in payments:
        paid_text = "paid" if payment.status == "PAID" else "not paid"
        response_text += f"- {payment.borrowing.book.title}: {payment.money_to_pay} USD ({paid_text})\n"

    await update.message.reply_text(response_text)


async def register(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_user = update.message.from_user
    telegram_id = telegram_user.id

    if not context.args:
        await update.message.reply_text(
            "Please use the command as:\n/register your_email@example.com"
        )
        return

    email = context.args[0]

    try:
        user = await sync_to_async(User.objects.get)(email=email)
        user.telegram_id = telegram_id
        await sync_to_async(user.save)()
        await update.message.reply_text("✅ You have been registered successfully!")
    except User.DoesNotExist:
        await update.message.reply_text(
            "❌ No user found with email: {email}. Please contact the admin."
        )


def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("checkoverdue", handle_checkoverdue))
    app.add_handler(CommandHandler("getchatid", getchatid))
    app.add_handler(CommandHandler("testchat", testchat))
    app.add_handler(CommandHandler("hello", hello))
    app.add_handler(CommandHandler("mybooks", mybooks))
    app.add_handler(CommandHandler("fines", fines))
    app.add_handler(CommandHandler("register", register))

    print("✅ All handlers registered. Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()
