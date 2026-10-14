# HROne Employee Attendance & Analytics API

A RESTful API built with **Python, FastAPI, and MongoDB Atlas** to manage employee attendance, track punch-in and punch-out times, handle attendance corrections with audit logs, and generate attendance analytics.

## 🚀 Features

- **Employee Punch-In:** Record an employee's attendance start time.
- **Employee Punch-Out:** Record an employee's attendance end time.
- **Attendance Records:** Retrieve attendance records through REST API endpoints.
- **Attendance Corrections:** Update punch-in or punch-out timestamps with a correction reason and an audit log.
- **Attendance Summary:** Generate overall attendance analytics.
- **Employee Analytics:** Retrieve attendance statistics for an individual employee.
- **Daily Analytics:** Aggregate attendance data by day.
- **Database Health Check:** Check MongoDB connectivity.
- **Interactive API Documentation:** Test endpoints using FastAPI Swagger UI.
- **Docker Support:** Build and run the application in a container.

## 🛠️ Tech Stack

| Technology | Purpose |
|---|---|
| Python 3.12 | Backend programming |
| FastAPI | REST API framework |
| MongoDB Atlas | Cloud database |
| PyMongo Async | Asynchronous database operations |
| Pydantic | Request validation |
| Uvicorn | ASGI server |
| uv | Python dependency management |
| Docker | Containerization |
| Swagger UI | API documentation and testing |

## 📁 Project Structure

```text
HrOneProject/
├── src/
│   └── hroneproject/
│       ├── __init__.py
│       ├── app.py
│       ├── db.py
│       └── requestModel.py
├── .env
├── .dockerignore
├── Dockerfile
├── pyproject.toml
├── uv.lock
└── README.md
```

## ⚙️ Prerequisites

Before running the application, install or configure:

- Python 3.12 or compatible version
- uv package manager
- MongoDB Atlas account and database user
- Docker Desktop (optional, for containerized execution)

## 🔧 Installation and Setup

### 1. Clone the repository

```bash
git clone <YOUR_GITHUB_REPOSITORY_URL>
cd HrOneProject
```

Replace the repository URL with your actual GitHub repository URL.

### 2. Configure environment variables

Create a `.env` file in the project root:

```dotenv
MONGODB_URI=mongodb+srv://<USERNAME>:<PASSWORD>@<CLUSTER_HOST>/?retryWrites=true&w=majority
MONGODB_DATABASE=hrone_attendance
```

Replace the placeholders with your MongoDB Atlas connection details.

**Security:** Never commit `.env` or expose database credentials in your repository.

### 3. Install dependencies

```bash
uv sync
```

### 4. Start the FastAPI server

```bash
uv run uvicorn hroneproject.app:app --reload --app-dir src
```

The application will run locally at:

```text
http://127.0.0.1:8000
```

### 5. Open API documentation

Visit:

- **Swagger UI:** http://127.0.0.1:8000/docs
- **ReDoc:** http://127.0.0.1:8000/redoc

Use Swagger UI to inspect and test the API endpoints interactively.

## 🐳 Run with Docker

### 1. Build the Docker image

Run this command from the project root:

```bash
docker build -t hrone-attendance-api .
```

### 2. Start the container

```bash
docker run --env-file .env -p 8000:8000 hrone-attendance-api
```

### 3. Access the API

Open http://localhost:8000/docs in your browser.

Ensure MongoDB Atlas network access rules allow connections from the environment running the container.

## 📡 API Endpoints

Base URL: `http://localhost:8000`

| Method | Endpoint | Description |
|---|---|---|
| GET | `/` | Root endpoint |
| GET | `/health/db` | Check database connectivity |
| POST | `/attendance/punch-in` | Record employee punch-in |
| POST | `/attendance/punch-out` | Record employee punch-out |
| GET | `/attendance` | Retrieve attendance records |
| PATCH | `/attendance/{attendance_id}/correction` | Correct an attendance timestamp and record the audit log |
| GET | `/analytics/summary` | Retrieve overall attendance analytics |
| GET | `/analytics/employee/{employee_id}` | Retrieve analytics for a specific employee |
| GET | `/analytics/daily` | Retrieve daily attendance analytics |

*Note: Request fields, query parameters, and response formats depend on the implementation in `app.py`. The Swagger UI provides the definitive endpoint schemas.*

## 🧪 Testing the API

1. Start the application.
2. Open `/docs` in your browser.
3. Select an endpoint.
4. Click **Try it out**.
5. Enter the required request data.
6. Click **Execute** to inspect the response.

For attendance operations, use an employee ID in the format expected by the API.

## 🗄️ Database

The project uses MongoDB Atlas as its cloud database. The application connects through PyMongo's asynchronous client.

The database stores attendance information and supports analytics through MongoDB aggregation pipelines. Attendance corrections also generate audit log entries to record correction details.

The database and collection names should match the configuration and implementation in `db.py` and `app.py`.

## 🔒 Security Considerations

- Store MongoDB credentials in environment variables.
- Add `.env` to `.gitignore`.
- Avoid committing secrets to GitHub.
- Restrict MongoDB Atlas network access to trusted IP addresses whenever possible.
- Validate incoming API requests using Pydantic.
- Restrict access to attendance correction endpoints in production using authentication and authorization.

## 🔮 Future Enhancements

- Employee authentication and role-based access control.
- Late-arrival and early-departure detection.
- Monthly attendance reports.
- CSV and Excel export.
- Automated API tests with Pytest.
- CI/CD integration.
- Production deployment with HTTPS and centralized logging.

## 👨‍💻 Author

**Kandula Lohith Chandra Varma**

Project: HROne Employee Attendance & Analytics API

## 📄 License

This project is intended for learning, development, and assessment purposes. Add a specific open-source license if you plan to distribute it publicly.
