# TripSync - Travel Buddy Finder

TripSync is a full-stack Flask travel companion platform for hosting trips, finding compatible travel partners, exchanging join requests, and chatting in real time.

## Highlights

- Email/password signup with OTP verification
- Profile, image, and ID-proof uploads
- Trip creation and trip discovery
- Host approval workflow for join requests
- Travel-buddy matching and search
- Trip and private real-time chat with Flask-SocketIO
- Reviews and host ratings
- MongoDB-backed persistent storage

## Tech Stack

| Area | Technology |
| --- | --- |
| Backend | Python, Flask, Flask-SocketIO |
| Database | MongoDB |
| Frontend | Jinja templates, HTML, CSS, JavaScript |
| Authentication | Flask sessions, Passlib/PBKDF2-SHA256 |
| Email | Flask-Mail with Gmail SMTP |
| Recommendations | pandas, NumPy, scikit-learn |
| Production Server | Gunicorn with threading workers |

## Project Structure

```text
app.py                 Flask application entry point
extensions.py          MongoDB, mail, and Socket.IO setup
backend/
  user/                Authentication and connections
  trips/               Trip hosting and join management
  apis/                Search, recommendations, and reviews
  chat/                Real-time chat routes and events
templates/             Jinja HTML templates
static/                CSS, JavaScript, and uploaded media
requirements.txt       Python dependencies
```

## Local Setup

### Prerequisites

- Python 3.11 or 3.13
- MongoDB local installation or MongoDB Atlas
- A Gmail account with an App Password for OTP emails

### 1. Create an Environment

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### 2. Configure Environment Variables

Create `.env` in the project root:

```dotenv
MONGODB_URI=mongodb://localhost:27017/
SECRET_KEY=replace-with-a-long-random-value
GMAIL_USER=your-email@gmail.com
GMAIL_PASSWORD=your-gmail-app-password
FLASK_DEBUG=0
```

Generate a secure secret key:

```powershell
python -c "import secrets; print(secrets.token_hex(32))"
```

For MongoDB Atlas, use the connection string from Atlas and ensure the database network-access list allows your host.

### 3. Run Locally

```powershell
python app.py
```

Open `http://localhost:5000`. The health check is available at `http://localhost:5000/health`.

## Production Deployment

### Render

1. Push this repository to GitHub.
2. In Render, create a **Web Service** and connect the repository.
3. Use this runtime configuration:
   - Build command: `pip install -r requirements.txt`
   - Start command: `gunicorn --worker-class gthread --workers 1 --threads 10 app:app`
   - Health check path: `/health`
   - Python version: `3.11`
4. Add these environment variables in the Render dashboard:

| Variable | Value |
| --- | --- |
| `MONGODB_URI` | MongoDB Atlas connection string |
| `SECRET_KEY` | A cryptographically random value |
| `GMAIL_USER` | Gmail address used to send OTP emails |
| `GMAIL_PASSWORD` | Gmail App Password |
| `FLASK_DEBUG` | `0` |

5. Deploy and verify:

```text
https://your-service.onrender.com/
https://your-service.onrender.com/health
```

### Railway or Other Linux Hosts

Use the same environment variables and start command:

```bash
gunicorn --worker-class gthread --workers 1 --threads 10 app:app
```

Set the platform port automatically; the app reads `PORT` when run directly and Gunicorn manages it in production.

## Deployment Notes

- Never commit `.env`, database credentials, Gmail credentials, or the generated secret key.
- MongoDB Atlas IP access must include the hosting provider or use its allowed-network configuration.
- Gmail requires an App Password; ordinary account passwords will not work reliably.
- Uploaded images and ID proofs are stored in `static/uploads/`. Platform local disks are commonly ephemeral. Use an object store such as Cloudinary or AWS S3 with persistent URLs for a durable production deployment.
- Use HTTPS and a restrictive CORS policy before any public release.
- Run one Gunicorn worker with multiple threads for this Socket.IO configuration unless a shared Socket.IO message queue is configured.
- The repository's existing local `.env` is excluded by `.gitignore` and should not be pushed.

## Verification Checklist

- `/health` returns HTTP 200 and `{"status":"ok"}`
- `/` renders the public home page
- `/signup` completes validation and OTP delivery
- `/login` starts a session
- `/find-trips` and `/find-buddy` render search data
- Hosting a trip saves it to MongoDB
- A logged-in user can submit and manage join requests
- Real-time chat works through the deployed WebSocket path
