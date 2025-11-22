# Sleep Tracking Application

## Overview
This is a comprehensive sleep tracking and analysis web application built with Django. The application allows users to track their sleep patterns, analyze sleep quality, and receive personalized recommendations for improving sleep hygiene.

## Features

### User Management
- User registration and authentication
- Profile management with personal details (age, weight, height, gender)
- Password reset functionality

### Sleep Tracking
- Manual sleep data entry
- Bulk import of sleep data from CSV files
- Automatic sleep phase detection and analysis
- Sleep duration and quality metrics
- Heart rate monitoring during sleep

### Sleep Analysis
- Sleep efficiency calculation
- Sleep phase distribution (light, deep, REM, awake)
- Sleep fragmentation index
- Calorie burn estimation during sleep
- Chronotype assessment (morning/evening person)
- Sleep regularity scoring

### Data Visualization
- Interactive charts for sleep trends
- Sleep phase distribution pie charts
- Heart rate variability analysis
- Sleep duration and efficiency trends over time

## Technology Stack

### Backend
- **Python 3.10+**
- **Django 4.2.11** - Web framework
- **Celery** - Asynchronous task queue
- **Redis** - Message broker and cache
- **PostgreSQL** - Database
- **Gunicorn** - WSGI HTTP Server (for production)

### Frontend
- **HTML5, CSS3, JavaScript**
- **Bootstrap 5** - Responsive design
- **Chart.js** - Interactive data visualization
- **jQuery** - DOM manipulation and AJAX

### Development Tools
- **Poetry** - Dependency management
- **Docker** - Containerization
- **Django Debug Toolbar** - Development debugging
- **Black** - Code formatting
- **isort** - Import sorting

## Project Structure

```
sleepproject/
├── .github/                  # GitHub configurations and workflows
├── alertmanager/             # Alertmanager configuration for monitoring
├── grafana/                  # Grafana dashboards and configuration
├── loki/                     # Loki logging configuration
├── nginx/                    # Nginx web server configuration
├── prometheus/               # Prometheus monitoring configuration
├── sleep_tracking_app/       # Main Django application
│   ├── migrations/           # Database migrations
│   ├── static/               # Static files (CSS, JS, images)
│   ├── templates/            # HTML templates
│   ├── sleep_statistic/      # Sleep analysis and statistics logic
│   ├── admin.py              # Admin interface configuration
│   ├── apps.py               # App configuration
│   ├── calculations.py       # Core calculation logic
│   ├── csv_data_extraction.py # CSV import/export utilities
│   ├── forms.py              # Form definitions
│   ├── models.py             # Database models
│   ├── tasks.py              # Celery tasks for async processing
│   ├── tests.py              # Test cases
│   ├── urls.py               # URL routing
│   └── views.py              # Request handlers
├── sleepproject/             # Project configuration
│   ├── __init__.py
│   ├── asgi.py              # ASGI configuration
│   ├── settings.py          # Django settings
│   ├── urls.py             # Root URL configuration
│   └── wsgi.py             # WSGI configuration
├── .env                     # Environment variables
├── .gitignore
├── docker-compose.yml       # Main Docker Compose configuration
├── docker-compose-logging.yml # Logging services configuration
├── docker-compose-monitoring.yml # Monitoring services configuration
├── Dockerfile               # Docker configuration for the web application
├── manage.py                # Django management script
├── poetry.lock             # Poetry lock file
└── pyproject.toml          # Project dependencies and configuration
```

### Key Components:

- **Docker & Docker Compose**: Containerization and orchestration
- **Celery**: Asynchronous task queue
- **Redis**: Caching and message broker for Celery
- **Nginx**: Web server and reverse proxy
- **Monitoring Stack**:
  - Prometheus: Metrics collection and monitoring
  - Grafana: Visualization dashboards
  - Loki: Log aggregation
  - Alertmanager: Alert management
- **Django**: Web framework
- **PostgreSQL**: Primary database (configured in docker-compose)

## Data Models

### UserData
Stores additional user information:
- Date of birth
- Weight and height
- Gender
- Activity status

### SleepRecord
Tracks individual sleep sessions:
- Sleep start and end times
- Sleep phases duration (light, deep, REM)
- Heart rate metrics
- Awake periods
- Device-specific data

### SleepStatistics
Aggregated sleep analysis:
- Sleep efficiency
- Sleep fragmentation index
- Calorie burn
- Sleep quality score
- Health impact assessment

### SleepSegment
Detailed sleep phase tracking:
- Start and end times
- Sleep phase type (light, deep, REM, awake)

### NightHeartRateEntry
Heart rate data during sleep:
- Timestamp
- Beats per minute (BPM)

## Key Features Implementation

### Sleep Analysis
- **Sleep Efficiency**: Calculated as (Total Sleep Time / Time in Bed) * 100
- **Sleep Phases**: Analyzed based on movement and heart rate patterns
- **Chronotype**: Determined using sleep midpoint and sleep duration patterns
- **Calorie Burn**: Estimated using the Mifflin-St Jeor equation adjusted for sleep

### Data Import
- Supports bulk import from CSV files
- Processes sleep data asynchronously using Celery
- Validates and normalizes imported data

### Performance Optimizations
- Database indexing for frequent queries
- Caching of computed statistics
- Asynchronous task processing
- Bulk database operations

## Setup Instructions

### Prerequisites
- Python 3.10+
- PostgreSQL
- Redis
- Node.js (for frontend assets)

### Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd sleepproject
   ```

2. Set up a virtual environment and install dependencies:
   ```bash
   poetry install
   ```

3. Create a `.env` file with your configuration:
   ```env
   DJANGO_SECRET_KEY=your-secret-key
   DEBUG=True
   BD_NAME=sleep_db
   BD_USER=postgres
   BD_PASSWORD=your-password
   CELERY_BROKER_URL=redis://localhost:6379/0
   ```

4. Apply database migrations:
   ```bash
   python manage.py migrate
   ```

5. Start the development server:
   ```bash
   python manage.py runserver
   ```

6. Start Celery worker (in a separate terminal):
   ```bash
   celery -A sleepproject worker -l info
   ```

## Usage

1. Register a new account or log in
2. Complete your profile with personal details
3. Add sleep data manually or import from a CSV file
4. View your sleep statistics and recommendations
5. Track your sleep patterns over time

## API Endpoints

The application provides REST API endpoints for data access (documentation available at `/api/docs/` when running locally).

## Testing

Run the test suite with:
```bash
python manage.py test
```

## Deployment

For production deployment, it's recommended to use:
- Gunicorn as the application server
- Nginx as a reverse proxy
- PostgreSQL as the database
- Redis for caching and message brokering
- Supervisor for process management

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## Acknowledgements
- [Django](https://www.djangoproject.com/)
- [Celery](https://docs.celeryproject.org/)
- [Redis](https://redis.io/)
- [Bootstrap](https://getbootstrap.com/)
- [Chart.js](https://www.chartjs.org/)
