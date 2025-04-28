# 🔒 Locksmith

Team-based Role-Based Access Control (RBAC) system designed to integrate seamlessly with Clerk authentication service.

[![Made with Fynix](https://img.shields.io/badge/Made%20with-Fynix-7B68EE.svg)](https://fynix.ai)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10](https://img.shields.io/badge/Python-3.10-blue.svg)](https://www.python.org/downloads/release/python-3100/)

## 🌟 Features

- **Team Management**: Create, update, and manage teams within your organization
- **Role-Based Access**: Define and assign roles with specific permissions
- **Clerk Integration**: Seamless authentication using Clerk's identity platform
- **RESTful API**: Clean and well-documented API endpoints
- **Async Support**: Built with modern async Python using FastAPI
- **Database Migrations**: Alembic-powered schema management
- **Production Ready**: Docker support, health checks, and monitoring

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- PostgreSQL
- Redis
- Kafka (optional)
- Clerk account and API keys

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/locksmith.git
cd locksmith
```

2. Create and activate virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements/requirements.txt
```

4. Configure environment:
   - Copy `config/default.yaml` to `config/local.yaml`
   - Update configuration values, especially:
     - `clerk_secret_key`
     - `postgres_fynix_locksmith_read_write`
     - `kafka_broker_list` (if using Kafka)

### Running the Service

```bash
uvicorn main:app --host 0.0.0.0 --port 8082 --reload
```

### Using Docker

```bash
docker build -t locksmith .
docker run -p 8082:8082 locksmith
```

## 📚 API Documentation

Once running, access the API documentation at:
- OpenAPI/Swagger UI: `http://localhost:8082/api-reference`
- OpenAPI JSON: `http://localhost:8082/openapi.json`

## 🔑 Key Endpoints

### Teams
- `POST /v1.0/teams/` - Create a new team
- `GET /v1.0/teams/` - List all teams
- `PUT /v1.0/teams/{team_id}` - Update team details
- `DELETE /v1.0/teams/{team_id}` - Delete a team

### Team Members
- `POST /v1.0/teams/{team_id}/members` - Add team member
- `GET /v1.0/teams/{team_id}/members` - List team members
- `DELETE /v1.0/teams/{team_id}/members/{user_id}` - Remove team member

### Roles
- `POST /v1.0/roles/` - Create a role
- `GET /v1.0/roles/` - List all roles

## 🛠️ Development

### Database Migrations

```bash
# Create a new migration
alembic revision --autogenerate -m "description"

# Run migrations
alembic upgrade head
```

### Running Tests

```bash
pytest
```

## 🔐 Security

- Built-in CORS support
- Session middleware
- Clerk authentication integration
- Role-based access control

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## ⭐ Built with Fynix

Locksmith is proudly built using [Fynix](https://fynix.ai), bringing enterprise-grade security and scalability to your applications.

---
Made with ❤️ using Fynix
