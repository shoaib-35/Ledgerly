# Ledgerly - Personal Finance Management System

Ledgerly is a personal finance management web application developed to help
users manage their financial accounts, transactions, money transfers, credit
cards, and personal ledgers in one place.

The application provides a simple and responsive interface for monitoring
financial activity and maintaining an organized record of transactions.

## Features

- Financial dashboard with an overview of current finances
- Bank account and financial account management
- Credit card management
- Transaction management
- Money transfers between accounts
- Transfers between accounts and cards
- Card payment management
- People and family ledger management
- Financial position overview
- Transaction history
- Import transactions from CSV and Excel files
- Export transactions to CSV and Excel files
- User profile management
- Change name and email
- Change password
- Currency preferences
- Date format preferences
- Light theme
- Dark theme
- System theme
- Responsive desktop, tablet, and mobile interface

## Technologies Used

- Python
- Django
- HTML
- CSS
- JavaScript
- SQLite

## Project Structure

```text
Ledgerly/
│
├── core/
│   ├── templates/
│   ├── static/
│   ├── views/
│   └── ...
│
├── manage.py
├── requirements.txt
└── README.md
```
## Installation

1. Clone the repository
```
git clone https://github.com/shoaib-35/ledgerly.git
```
3. Navigate to the project directory
```
cd ledgerly
```
5. Create a virtual environment
```
python -m venv venv
```
7. Activate the virtual environment
(a) Windows
```
venv\Scripts\activate
```
(b) Linux / macOS
```
source venv/bin/activate
```
9. Install the required packages
```
pip install -r requirements.txt
```
11. Run database migrations
```
python manage.py migrate
```
13. Start the development server
```
python manage.py runserver
```

The application will then be available at:
```
http://127.0.0.1:8000/
```
## Transaction Import Format

Ledgerly supports importing transactions from CSV and Excel files.

The recommended format is:

| Date       | Description      | Amount | Type    | Account   | Person | Category |
| ---------- | ---------------- | -----: | ------- | --------- | ------ | -------- |
| 01/09/2026 | Grocery Shopping |   1500 | Expense | HDFC Bank | Self   | Food     |
| 03/09/2026 | Salary           |  45000 | Income  | HDFC Bank | Self   | Salary   |

### Important

The column names and values should follow the format expected by the
application to prevent errors during import.

### Project Status

This project is currently under development.

New features, improvements, and UI enhancements may be added in future
versions.

```
This project is provided for viewing purposes only.

No permission is granted to copy, modify, distribute, or use this software
without explicit permission from the author.

© 2026 Mohammed Shoaib. All rights reserved.
```
