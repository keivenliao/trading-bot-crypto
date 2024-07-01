import smtplib
from email.mime.text import MIMEText
from config import SMTP_SERVER, SMTP_PORT, EMAIL_USER, EMAIL_PASS

def send_email(subject, body, to):
    try:
        msg = MIMEText(body)
        msg['Subject'] = subject
        msg['From'] = EMAIL_USER
        msg['To'] = to

        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.login(EMAIL_USER, EMAIL_PASS)
            server.sendmail(EMAIL_USER, to, msg.as_string())

        print(f"Email successfully sent to {to}")
    except smtplib.SMTPException as e:
        print(f"Failed to send email: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

# Example usage:
if __name__ == "__main__":
    subject = "Test Email"
    body = "This is a test email sent from Python."
    to = "recipient@example.com"

    send_email(subject, body, to)


# utils.py

import pandas as pd
import numpy as np
import ta

def calculate_sma(df, window):
    return df['close'].rolling(window=window).mean()

def calculate_rsi(df, period=14):
    return ta.momentum.RSIIndicator(close=df['close'], window=period).rsi()

def calculate_macd(df, fast=12, slow=26, signal=9):
    macd = ta.trend.MACD(close=df['close'], window_slow=slow, window_fast=fast, window_sign=signal)
    return macd.macd(), macd.macd_signal()

def calculate_bollinger_bands(df, length=20, std=2):
    bbands = ta.volatility.BollingerBands(close=df['close'], window=length, window_dev=std)
    return bbands.bollinger_hband(), bbands.bollinger_mavg(), bbands.bollinger_lband()

def calculate_atr(df, length=14):
    atr = ta.volatility.AverageTrueRange(high=df['high'], low=df['low'], close=df['close'], window=length)
    return atr.average_true_range()
