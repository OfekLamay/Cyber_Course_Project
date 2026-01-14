# Communication_LTD — Secure and Vulnerable Editions

Submitted by:

- Ofek Lamay 31928567
- Michael Israeli 211785936
- Sean Pesis 322854290
- Doron Shapira 208105080
- Adi Zalesky 323134239
- Nimrod Nehemia 208494328

This repository contains two Django web applications that implement an employee portal and a customer database.

- Cyber_Course_Project/ — secure, production-style implementation
- Cyber_Course_Project_Vulnerable/ — intentionally vulnerable implementation for training and demos

Both apps include:
- Sign-Up, Sign-In, and Sign-Out flows
- Customer management (list, add, edit, delete, detail)
- Change Password
- Forgot Password (email reset code + verification + reset)

Never deploy the vulnerable project anywhere public. It is intentionally unsafe.

## Key differences: secure vs. vulnerable

Secure project (Cyber_Course_Project)
- Uses Django ORM and server-side validation to avoid SQL injection.
- Escapes user-controlled content in templates.
- Enforces password policy from config/password_config.json in sign-up and reset.
- Lockdown/anti-bruteforce logic in sign-in (per your configuration).

Vulnerable project (Cyber_Course_Project_Vulnerable)
- Kept intentionally vulnerable for practice:
  - SQL injection exposure in register, login, and customers pages.
  - Stored XSS exposure on customers pages (user content rendered without safe escaping).
- Forgot Password is implemented but kept minimal so it doesn’t change the above vulnerabilities.
- Do not harden this project unless you are done demonstrating attacks.

## Prerequisites

- Windows with Python 3.11+ (3.13 works)
- Git (optional)
- Email SMTP account for sending reset codes

Both projects expect a .env file next to manage.py. Example:

```
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@example.com
SMTP_PASSWORD=your_app_password
SMTP_USE_TLS=true
FROM_EMAIL=security@example.com
# Optional: used to build absolute links in emails
```

The .env is kept out of Git.

## How to run (secure project)

CMD:
```
cd Cyber_Course_Project
python -m venv .venv
.venv\Scripts\activate.bat
pip install django python-dotenv
python manage.py migrate
python manage.py runserver # Uses port 8000, add a port number to make it run there
```

## How to run (vulnerable project)

CMD:
```
cd Cyber_Course_Project_Vulnerable
python -m venv .venv
.venv\Scripts\activate.bat
pip install django python-dotenv
python manage.py migrate
python manage.py runserver # Uses port 8000, add a port number to make it run there
```

## App overview and usage

- Home: http://127.0.0.1:8000/ 
- Sign Up: /Sign_Up/ — create an account (secure project validates strongly; vulnerable project is intentionally weak)
- Sign In: /Sign_In/ — log in to access customers
  - The secure project accepts username or email.
- Customers: /customers/ — list, add, edit, delete, and view customers
  - Secure project: inputs validated and output escaped.
  - Vulnerable project: intentionally allows stored XSS on customer fields and uses unsafe query patterns for practice.
- Change Password: /change-password/ or the “Change Password” button in the header (secure project enforces password policy).
- Forgot Password:
  1) Go to /Forgot_Password/forgot-password/
  2) Send Reset Code to your email
  3) Verify code on the same page or click the link in the email
  4) Reset password on /Forgot_Password/reset-password/
  - Secure project enforces password policy; vulnerable project only checks that the two passwords match.

## Project layout (root)

- Cyber_Course_Project/ — secure app
  - Cyber_Course_Project/templates/ — all HTML templates (Sign_In.html, Sign_Up.html, customers pages, forgot/reset pages)
  - Forgot_Password/ — app that serves forgot/verify/reset endpoints
  - Sign_In/, Sign_Up/, Sign_Out/ — authentication-related apps
  - config/password_config.json — password policy used by the secure project
- Cyber_Course_Project_Vulnerable/ — intentionally insecure app
  - Same structure; Forgot_Password is included but other parts remain vulnerable by design.

## Notes and tips

- Stop a running server with Ctrl+C. Restart after changing .env or settings.
- Admin panel (optional): create a superuser and visit /admin/.
- If you see a redirect to /accounts/login/, set these in settings.py of each project:
  - LOGIN_URL='Sign_In', LOGIN_REDIRECT_URL='customer_system', LOGOUT_REDIRECT_URL='home'
- Do not expose the vulnerable project publicly.