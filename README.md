# RackOps

RackOps is a straightforward, modern tool for managing your data center infrastructure. It gives you a clear visual for sites, racks, and hardware without the bloat of traditional DCIM software.

![Login](screenshots/login.png)
![Dashboard](screenshots/dashboard.png)
![Rackview](screenshots/rack.png)

## 🚀 What's Inside

- **Rack Elevations**: See exactly what's in your racks with front and back views.
- **Flexible Layouts**: Supports both full-depth and half-depth equipment. You can even mount two half-depth items in the same U (one front, one back).
- **Detailed Asset Tracking**: Keep tabs on your hardware with fields for Asset Tags, Serial Numbers, Operating Systems, and Management (OOB) IPs.
- **Audit Logs**: A full history of every change. Know exactly who updated a device or moved a rack.
- **Role-Based Access**: 
    - **Viewers**: Can look but not touch.
    - **Operators**: Handle the day-to-day (add/edit/move equipment).
    - **Admins**: Full control over users and system settings.
- **Quick Search**: Find anything instantly by hostname, IP, or serial number.
- **Dark & Light Mode**: A clean, modern interface that works wherever you do.
- **Pro-Level API**: Fully documented endpoints if you want to automate your workflow.

## 🛠️ Built With

- **Backend**: Python 3.12, FastAPI, SQLAlchemy
- **Frontend**: Tailwind CSS, Jinja2, Chart.js
- **Environment**: Docker, SQLite (default), with support for PostgreSQL and MySQL.

## ⚙️ How to Configure

RackOps uses environment variables. Just copy the sample file and fill in your details:

```bash
cp .env-sample .env
```

| Variable | What it does | Default |
|----------|-------------|---------|
| `DATABASE_URL` | Database connection string | `sqlite:///./dcim.db` |
| `AUTH_MODE` | How users log in (`LOCAL` or `AZURE`) | `LOCAL` |
| `SECRET_KEY` | **Required** - Used to sign login tokens | - |
| `ALLOWED_ORIGINS` | Which web addresses can talk to the API | `http://localhost:8000` |
| `SEED_DEFAULT_ADMIN`| Create a default 'admin' user if the DB is new | `auto` |
| `AZURE_CLIENT_ID` | Your Azure App Client ID | - |
| `AZURE_TENANT_ID` | Your Azure Tenant ID | - |
| `AZURE_OPERATORS_GROUP_ID`| Azure Group for Operators | - |
| `AZURE_VIEWERS_GROUP_ID` | Azure Group for Viewers | - |

> [!IMPORTANT]
> You **must** set a `SECRET_KEY`. The app won't start without one. Use a long, random string.

> [!NOTE]
> If you're using `LOCAL` auth and the database is empty, the app creates a default user: `admin` / `adminpassword`. Change this as soon as you log in.

## 🚀 Using a Production Database

If you're moving beyond a small lab, you should use **PostgreSQL** or **MySQL**.

1. **PostgreSQL**: Set `DATABASE_URL=postgresql://user:password@host:5432/db`.
2. **Handle Migrations**: We use **Alembic** to keep the database in sync.
   - **Update your schema**: `python -m alembic upgrade head`
   - **Create a new migration**: `python -m alembic revision --autogenerate -m "description"`

## 🔐 Azure AD Integration

If you want to use your existing Azure/Office 365 logins:

1. **Register the App**: In the Azure portal, create a new App Registration.
   - Add your Web redirect URI.
   - Make sure "groups" are included in the token.
2. **Map Your Groups**: Find the Object IDs for your "Operators" and "Viewers" groups in Azure.
3. **Finish Setup**: Set `AUTH_MODE=AZURE` and paste your IDs into the `.env` file.

> [!WARNING]
> Once Azure mode is on, local logins are disabled for security. Make sure your Azure setup works before flipping the switch!

## 📋 Getting Started

### The Docker Way (Recommended)

1. Clone the repo and set up your `.env`:
   ```env
   SECRET_KEY=something-random-and-long
   SEED_DEFAULT_ADMIN=True
   ```
2. Spin it up:
   ```bash
   docker compose up -d
   ```
3. Open `http://localhost:8000` in your browser.

### Manual Setup (Windows/IIS or Linux)

#### 🐧 Linux (managed with systemd)
1. **Prepare the app**:
   ```bash
   git clone <repo-url> dcim
   cd dcim
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```
2. **Initialize**:
   ```bash
   export SECRET_KEY=your-key
   python3 -m alembic upgrade head
   ```
3. **Run it**: Use **Gunicorn** with **Uvicorn** workers for a stable deployment.

#### 🪟 Windows (IIS)
1. **Requirements**: 
   - Enable "CGI" in Windows Features.
   - Install the **HttpPlatformHandler**.
2. **Setup**:
   - Create a virtual environment and install dependencies.
   - Run the Alembic upgrade to prep the database.
   - Configure your `web.config` to point to the virtual environment's Python executable.

## 📜 API Docs

Explore the API and try out endpoints directly:
- **Swagger**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

---
*Built for speed, clarity, and getting things done.*

