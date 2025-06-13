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
            send_notification(message)
    else:
        send_notification("📢 No borrowings overdue today!")


@sync_to_async
def run_check():
    check_overdue_borrowings()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_user = update.message.from_user
    telegram_id = telegram_user.id

    if not context.args:
        await update.message.reply_text(
            "👋 Welcome! To log in, use:\n/start your_email@example.com"
        )
        return

    email = context.args[0]

    try:
        user = await sync_to_async(User.objects.get)(email=email)
        user.telegram_id = telegram_id
        await sync_to_async(user.save)()
        await update.message.reply_text(f"✅ Login successful! Welcome, {user.email}.")
    except User.DoesNotExist:
        await update.message.reply_text(
            f"❌ No user found with email {email}. Please contact the administrator."
        )


async def borrowings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = update.message.from_user.id
    try:
        user = await sync_to_async(User.objects.get)(telegram_id=telegram_id)
    except User.DoesNotExist:
        await update.message.reply_text(
            "❌ You are not logged in. Please use /start your_email"
        )
        return

    borrowings = await sync_to_async(
        lambda: list(Borrowing.objects.filter(user=user).select_related("book"))
    )()

    if not borrowings:
        await update.message.reply_text("📚 You have no borrowings.")
        return

    active_section = ""
    all_section = "📖 Your borrowings:\n"

    for borrowing in borrowings:
        book = borrowing.book
        is_returned = borrowing.actual_return_date is not None
        paid = await sync_to_async(lambda: Payment.objects.filter(
            borrowing=borrowing,
            type_field="PAYMENT",
            status="PAID"
        ).exists())()
        paid_text = "paid" if paid else "not paid"

        if not is_returned:
            active_section += (
                "📌 <b>You have a new borrowing:</b>\n"
                f"Book Title: {book.title}\n"
                f"Author: {book.author}\n"
                f"Expected return date: {borrowing.expected_return_date}\n"
                f"Price per day: {book.daily_fee} USD\n\n"
            )

        all_section += (
            f"- {book.title}\n"
            f"  Return status: {'returned' if is_returned else 'not returned'}\n"
            f"  Payment: {paid_text}\n\n"
        )

    message = (active_section + all_section).strip()
    await update.message.reply_text(message, parse_mode="HTML")


async def payments(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = update.message.from_user.id
    try:
        user = await sync_to_async(User.objects.get)(telegram_id=telegram_id)
    except User.DoesNotExist:
        await update.message.reply_text(
            "❌ You are not logged in. Please use /start your_email"
        )
        return

    payments = await sync_to_async(
        lambda: list(Payment.objects.filter(
            borrowing__user=user,
            type_field="PAYMENT",
            status="PAID"
        ).select_related("borrowing__book"))
    )()

    if not payments:
        await update.message.reply_text("💸 You have no successful payments.")
        return

    response_text = "✅ Your successful payments:\n"
    for payment in payments:
        response_text += f"- {payment.borrowing.book.title}: {payment.money_to_pay} USD\n"

    await update.message.reply_text(response_text)


def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("borrowings", borrowings))
    app.add_handler(CommandHandler("payments", payments))

    print("✅ All handlers registered. Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()
