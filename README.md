# 🚀 Scalable User Management System

A simple full-stack system demonstrating scalable backend architecture using FastAPI, RabbitMQ, and PostgreSQL with load balancing via NGINX.

---

## 🏗️ Architecture Overview

- **NGINX**: Load balancer
- **FastAPI**: Backend API (stateless, scalable)
- **RabbitMQ**: Message queue for async processing
- **Worker**: Background consumers
- **PostgreSQL**: Database

---

## ⚙️ Tech Stack

- Backend: Python (FastAPI)
- Queue: RabbitMQ
- Database: PostgreSQL
- Load Balancer: NGINX
- Containerization: Docker, Docker Compose
- CI/CD: GitHub Actions

---

## 📌 Features

- Upload CSV file to insert user data
- Asynchronous processing using message queue
- Scalable backend and worker services
- Load balancing with NGINX
- CI pipeline with build & test

---

## 🚀 Getting Started

### 1. Clone repository
```bash
git clone https://github.com/kengljr/coraline-example.git
cd coraline-example
```

### 2. Run with Docker Compose
```bash
docker compose up -d --build --scale backend=3 --scale worker=3
```
