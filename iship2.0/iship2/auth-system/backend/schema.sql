-- Blood Donation Management System Database Schema

-- Donors Table
CREATE TABLE IF NOT EXISTS donors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    contact TEXT NOT NULL,
    blood_group TEXT NOT NULL,
    age INTEGER NOT NULL,
    latitude REAL NOT NULL,
    longitude REAL NOT NULL,
    last_donation_month TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Receivers Table
CREATE TABLE IF NOT EXISTS receivers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    contact TEXT NOT NULL,
    hospital_name TEXT NOT NULL,
    latitude REAL NOT NULL,
    longitude REAL NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Hospitals Table
CREATE TABLE IF NOT EXISTS hospitals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    hospital_id TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    contact TEXT NOT NULL,
    latitude REAL NOT NULL,
    longitude REAL NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Requests Table
CREATE TABLE IF NOT EXISTS requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    donor_id INTEGER NOT NULL,
    receiver_id INTEGER NOT NULL,
    status TEXT DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (donor_id) REFERENCES donors(id) ON DELETE CASCADE,
    FOREIGN KEY (receiver_id) REFERENCES receivers(id) ON DELETE CASCADE,
    UNIQUE (donor_id, receiver_id)
);


-- Indexes for better performance
CREATE INDEX IF NOT EXISTS idx_donors_email ON donors(email);
CREATE INDEX IF NOT EXISTS idx_receivers_email ON receivers(email);
CREATE INDEX IF NOT EXISTS idx_hospitals_email ON hospitals(email);
CREATE INDEX IF NOT EXISTS idx_requests_donor ON requests(donor_id);
CREATE INDEX IF NOT EXISTS idx_requests_receiver ON requests(receiver_id);
CREATE INDEX IF NOT EXISTS idx_requests_status ON requests(status);
