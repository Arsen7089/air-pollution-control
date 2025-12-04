````markdown
# Pollution Control by Identifying Area for Afforestation

This project is a Flask-based web application that analyzes satellite or aerial images to identify areas of trees and fields within a city. It outputs a color-coded image and a table indicating how many trees need to be planted and with what density for afforestation.

---

## Prerequisites

Make sure you have installed:

- [Docker](https://docs.docker.com/get-docker/)
- [Docker Compose](https://docs.docker.com/compose/install/)

---

## Environment Variables

Create a `.env` file in the project root with the following variables:

```env
# Web server
WEB_IP=0.0.0.0
WEB_PORT=8000

# MongoDB
MONGO_IP=mongo
MONGO_PORT=27017
MONGO_USER=your_mongo_user
MONGO_PASS=your_mongo_password

# Admin
ADMIN_USER=admin
ADMIN_PASS=secret

# OpenWeatherMap API
OWM_API=Your_Open_Weather_Map_API_key
```

---

## Build and Run

To build the Docker images and start the containers:

```bash
docker-compose up --build -d
```

To start the project without rebuilding (useful if nothing changed):

```bash
docker-compose up -d
```

To stop and remove the containers:

```bash
docker-compose down
```

---

## Access the Application

* **Web interface:** [http://localhost:8000](http://localhost:8000)
* **Admin panel:** [http://localhost:8000/admin](http://localhost:8000/admin)
  Login with credentials from `.env` file (`ADMIN_USER` / `ADMIN_PASS`).

---

## Notes

* The first time you start, MongoDB will initialize with the provided credentials.
* If the admin panel doesn’t ask for a password, try opening it in an incognito window to bypass cached authentication.
* Logs can be viewed with:

```bash
docker-compose logs -f
```
````

