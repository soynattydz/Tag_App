# Social Activity App - tag
Current state: A FastAPI-based social networking application that helps users find nearby people with similar interests.

## Features
- User authentication with JWT tokens
- User profile management with location data
- Nearby user discovery based on location
- Interest-based matching
- Age and distance preferences

## Tech Stack
- FastAPI - Web framework
- PostgreSQL - Database
- SQLAlchemy - ORM
- PyJWT - JWT token handling
- Passlib - Password hashing
- Python-dotenv - Environment management

## Prerequisites
- Python 3.8+
- PostgreSQL
- pip (Python package manager)

## Installation
1. Clone the repository
git clone [https://github.com/soynattydz/Tag_App]
cd [Tag_App]

2. Create a virtual environment and activate it
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate

3. Install dependencies
pip install -r requirements.txt

4. Create a `.env` file in the root directory with the following content:
DATABASE_URL=postgresql://postgres:your_password@localhost/tag_db
SECRET_KEY=your-generated-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

5. Create the PostgreSQL database
CREATE DATABASE tag_db;


6. Initialize the database
python __init__.py

7. Run the application
uvicorn main:app --reload

The API will be available at `http://localhost:8000`

## API Endpoints

### Authentication
- `POST /register` - Register a new user
  - Required fields: email, password, full_name
- `POST /token` - Login and get access token
  - Required fields: username (email), password

### User Profile
- `GET /users/me` - Get current user information
- `PUT /users/profile` - Update user profile
  - Optional fields:
    - latitude (float: -90 to 90)
    - longitude (float: -180 to 180)
    - interests (list of strings)
    - max_distance (float: 0 to 100 km)
    - preferred_age_range_min (integer: ≥18)
    - preferred_age_range_max (integer: ≥18)
    - age (integer: ≥18)
    - gender (string)

### User Discovery
- `GET /users/nearby` - Get users within specified max_distance
  - Requires user location to be set
  - Uses Haversine formula for distance calculation

## API Documentation
Once the application is running, you can access:
- Interactive API documentation: `http://localhost:8000/docs`
- Alternative API documentation: `http://localhost:8000/redoc`

## Development

### Database Models
The application uses SQLAlchemy models defined in `models.py`:
- User model includes:
  - Basic information (email, password, full name)
  - Location (latitude, longitude)
  - Preferences (max distance, age range)
  - Profile details (age, gender, interests)

### Project Structure
├── __init__.py      # Database initialization
├── main.py          # FastAPI application and endpoints
├── models.py        # Database models
├── database.py      # Database configuration
├── requirements.txt # Project dependencies
├── .env            # Environment variables (not in repo)
└── .gitignore      # Git ignore configuration

## Security Notes
- Passwords are hashed using bcrypt
- Authentication uses JWT tokens
- Environment variables are used for sensitive data
- CORS middleware can be added for frontend integration

## Contributing
1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

