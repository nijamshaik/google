-- File: backend/schema.sql

DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS donor_details;
DROP TABLE IF EXISTS requests;

CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    contact_no TEXT NOT NULL,
    user_type TEXT NOT NULL CHECK(user_type IN ('donor', 'receiver', 'hospital', 'club')),
    hospital_id TEXT -- Only for hospitals
);

CREATE TABLE donor_details (
    user_id INTEGER PRIMARY KEY,
    blood_group TEXT NOT NULL,
    location TEXT,
    age INTEGER,
    last_donation_months INTEGER,
    FOREIGN KEY (user_id) REFERENCES users (id)
);

CREATE TABLE requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    requester_id INTEGER NOT NULL,
    donor_id INTEGER NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending', -- pending, accepted, rejected
    request_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (requester_id) REFERENCES users (id),
    FOREIGN KEY (donor_id) REFERENCES users (id)
);