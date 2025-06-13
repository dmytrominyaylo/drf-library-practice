# 📕 Library Service API

A comprehensive digital library service offering seamless book borrowing, secure payment processing, and instant user notifications via Telegram integration.

## 📌 Features

- 📖 Book rental system with availability tracking
- 💳 Payment integration via Stripe (simplified checkout)
- 📨 Telegram notifications to admin on new borrowings
- 🔐 JWT authentication (login via email)
- 🧑‍ Role-based access (Admin / User)
- 🛠️ Admin panel for management
- 📃 API documentation with Swagger (drf-spectacular)
- 🐳 Docker-based deployment

##  ⚙️️ Technologies Used

- 🐍 Python, Django, Django REST Framework
- 🐘 PostgreSQL
- 🐳 Docker, Docker Compose
- 🤖 python-telegram-bot
- 📜 drf-spectacular for API schema / Swagger documentation

## 🐳 Setup with Docker

1. **Clone the repository**
```
git clone https://github.com/dmytrominyaylo/drf-library-practice.git
cd drf-library-practice
```
2. **Create and configure .env file**
```bash
cp .env.sample .env
# Fill in the required variables (Stripe keys, Telegram token, DB config, etc.)
```
3. **Build and run containers**
```bash
docker-compose up --build
```
The following services will run:
* web – Main Django app
* db – PostgreSQL database

4. **Create a superuser**
```bash
docker-compose exec web python manage.py createsuperuser
```
Now the API is available at http://localhost:8000/ and admin panel at http://localhost:8000/admin/.

## 📦 Main Models
* **User** – Custom user model with email login
* **Book** – Books with title, author, inventory, and daily fee
* **Borrowing** – Links user to rented book and manages return
* **Payment** – Stripe session information for borrowings

## 🔐 Authentication
Authentication is done via JWT. Users register and log in using their email.

To get tokens, visit:
```
http://localhost:8000/api/users/token/ 
```

## 💳 Stripe Integration
* Stripe session is automatically created when a borrowing is made.
* User is redirected to Stripe's hosted checkout via success URL.
* No webhooks are used for simplicity.
* If a book is returned late, a penalty payment is automatically generated.

## 🔁 Book Return Logic
* Send a POST request to /api/borrowings/<id>/return/
* If the return is not overdue, it is processed instantly.
* If overdue, a fine payment is created and must be paid.

## 🔔 Notifications
* On new borrowings, a Telegram message is sent to the admin chat.
* Daily scheduled task checks for overdue books and notifies admin.
* Notifications are powered by python-telegram-bot.

## 📃 API Documentation
After running the app to see full API documentation visit:
```
http://localhost:8000/api/doc/swagger/
```
## 🧪 Running Tests

To run the tests with coverage, use the following commands:
```bash
docker-compose exec web coverage run manage.py test
```
