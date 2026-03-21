import sqlite3
from datetime import datetime

DB_NAME = "smriti.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS topics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            topic_name TEXT NOT NULL,
            subject TEXT NOT NULL,
            understanding_score INTEGER NOT NULL,
            date_learned TEXT NOT NULL,
            last_reviewed TEXT,
            review_count INTEGER DEFAULT 0
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            topic_id INTEGER,
            review_date TEXT,
            retention_score INTEGER,
            FOREIGN KEY (topic_id) REFERENCES topics(id)
        )
    ''')
    conn.commit()
    conn.close()

def add_topic(topic_name, subject, understanding_score, date_learned=None):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    if date_learned is None:
        date_learned = datetime.now().strftime("%Y-%m-%d")
    c.execute('''
        INSERT INTO topics (topic_name, subject, understanding_score, date_learned)
        VALUES (?, ?, ?, ?)
    ''', (topic_name, subject, understanding_score, str(date_learned)))
    conn.commit()
    conn.close()

def get_all_topics():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT * FROM topics ORDER BY date_learned DESC")
    topics = c.fetchall()
    conn.close()
    return topics

def add_review(topic_id, retention_score):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    today = datetime.now().strftime("%Y-%m-%d")
    c.execute('''
        INSERT INTO reviews (topic_id, review_date, retention_score)
        VALUES (?, ?, ?)
    ''', (topic_id, today, retention_score))
    c.execute('''
        UPDATE topics SET last_reviewed = ?, review_count = review_count + 1
        WHERE id = ?
    ''', (today, topic_id))
    conn.commit()
    conn.close()

def get_reviews(topic_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT * FROM reviews WHERE topic_id = ?", (topic_id,))
    reviews = c.fetchall()
    conn.close()
    return reviews
