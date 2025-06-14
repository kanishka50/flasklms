
```
university-grade-prediction-system
├─ backend
│  ├─ api
│  │  ├─ admin
│  │  │  ├─ routes.py
│  │  │  └─ __init__.py
│  │  ├─ auth
│  │  │  ├─ routes.py
│  │  │  └─ __init__.py
│  │  ├─ common
│  │  │  ├─ routes.py
│  │  │  └─ __init__.py
│  │  ├─ faculty
│  │  │  ├─ routes.py
│  │  │  └─ __init__.py
│  │  ├─ prediction
│  │  │  ├─ routes.py
│  │  │  └─ __init__.py
│  │  ├─ student
│  │  │  ├─ routes.py
│  │  │  └─ __init__.py
│  │  └─ __init__.py
│  ├─ app.py
│  ├─ extensions.py
│  ├─ middleware
│  │  ├─ error_handler.py
│  │  └─ __init__.py
│  ├─ ml_integration
│  │  └─ __init__.py
│  ├─ models
│  │  └─ __init__.py
│  ├─ services
│  │  └─ __init__.py
│  ├─ tasks
│  ├─ utils
│  │  ├─ logger.py
│  │  └─ __init__.py
│  └─ __init__.py
├─ config.py
├─ database
│  ├─ migrations
│  ├─ procedures
│  ├─ schema
│  └─ seeds
├─ deployment
│  ├─ kubernetes
│  ├─ nginx
│  ├─ systemd
│  └─ terraform
├─ docs
│  ├─ api
│  ├─ guides
│  ├─ images
│  └─ technical
├─ frontend
│  ├─ public
│  ├─ src
│  │  ├─ assets
│  │  │  ├─ fonts
│  │  │  ├─ images
│  │  │  └─ vendor
│  │  ├─ css
│  │  └─ js
│  │     ├─ api
│  │     ├─ auth
│  │     ├─ components
│  │     ├─ pages
│  │     └─ utils
│  └─ templates
│     ├─ admin
│     ├─ auth
│     ├─ components
│     ├─ errors
│     ├─ faculty
│     ├─ layouts
│     └─ student
├─ ml_models
├─ package.json
├─ README.md
├─ requirements.txt
├─ scripts
│  ├─ data
│  ├─ deployment
│  ├─ maintenance
│  └─ setup
├─ setup_project.py
├─ tests
│  ├─ e2e
│  ├─ fixtures
│  ├─ integration
│  └─ unit
└─ wsgi.py

```
```
university-grade-prediction-system
├─ backend
│  ├─ api
│  │  ├─ admin
│  │  │  ├─ routes.py
│  │  │  └─ __init__.py
│  │  ├─ auth
│  │  │  ├─ routes.py
│  │  │  └─ __init__.py
│  │  ├─ common
│  │  │  ├─ routes.py
│  │  │  └─ __init__.py
│  │  ├─ faculty
│  │  │  ├─ routes.py
│  │  │  └─ __init__.py
│  │  ├─ prediction
│  │  │  ├─ routes.py
│  │  │  └─ __init__.py
│  │  ├─ student
│  │  │  ├─ routes.py
│  │  │  └─ __init__.py
│  │  └─ __init__.py
│  ├─ app.py
│  ├─ extensions.py
│  ├─ middleware
│  │  ├─ error_handler.py
│  │  └─ __init__.py
│  ├─ ml_integration
│  │  └─ __init__.py
│  ├─ models
│  │  ├─ academic.py
│  │  ├─ alert.py
│  │  ├─ assessment.py
│  │  ├─ prediction.py
│  │  ├─ system.py
│  │  ├─ tracking.py
│  │  ├─ user.py
│  │  └─ __init__.py
│  ├─ services
│  │  └─ __init__.py
│  ├─ tasks
│  ├─ utils
│  │  ├─ logger.py
│  │  └─ __init__.py
│  └─ __init__.py
├─ config.py
├─ database
│  ├─ migrations
│  ├─ procedures
│  ├─ schema
│  └─ seeds
│     ├─ 01_users.sql
│     ├─ 02_academic.sql
│     └─ 03_assessment_types.sql
├─ deployment
│  ├─ kubernetes
│  ├─ nginx
│  ├─ systemd
│  └─ terraform
├─ docs
│  ├─ api
│  ├─ guides
│  ├─ images
│  └─ technical
├─ frontend
│  ├─ public
│  ├─ src
│  │  ├─ assets
│  │  │  ├─ fonts
│  │  │  ├─ images
│  │  │  └─ vendor
│  │  ├─ css
│  │  └─ js
│  │     ├─ api
│  │     ├─ auth
│  │     ├─ components
│  │     ├─ pages
│  │     └─ utils
│  └─ templates
│     ├─ admin
│     ├─ auth
│     ├─ components
│     ├─ errors
│     ├─ faculty
│     ├─ layouts
│     └─ student
├─ ml_models
├─ package.json
├─ README.md
├─ requirements.txt
├─ scripts
│  ├─ data
│  ├─ deployment
│  ├─ maintenance
│  └─ setup
│     ├─ initialize_db.py
│     └─ setup_database.py
├─ setup_project.py
├─ tests
│  ├─ e2e
│  ├─ fixtures
│  ├─ integration
│  └─ unit
└─ wsgi.py

```
```
university-grade-prediction-system
├─ backend
│  ├─ api
│  │  ├─ admin
│  │  │  ├─ routes.py
│  │  │  └─ __init__.py
│  │  ├─ auth
│  │  │  ├─ routes.py
│  │  │  └─ __init__.py
│  │  ├─ common
│  │  │  ├─ routes.py
│  │  │  └─ __init__.py
│  │  ├─ faculty
│  │  │  ├─ routes.py
│  │  │  └─ __init__.py
│  │  ├─ prediction
│  │  │  ├─ routes.py
│  │  │  └─ __init__.py
│  │  ├─ student
│  │  │  ├─ routes.py
│  │  │  └─ __init__.py
│  │  └─ __init__.py
│  ├─ app.py
│  ├─ extensions.py
│  ├─ middleware
│  │  ├─ auth_middleware.py
│  │  ├─ error_handler.py
│  │  └─ __init__.py
│  ├─ ml_integration
│  │  └─ __init__.py
│  ├─ models
│  │  ├─ academic.py
│  │  ├─ alert.py
│  │  ├─ assessment.py
│  │  ├─ prediction.py
│  │  ├─ system.py
│  │  ├─ tracking.py
│  │  ├─ user.py
│  │  └─ __init__.py
│  ├─ services
│  │  ├─ auth_service.py
│  │  └─ __init__.py
│  ├─ tasks
│  ├─ utils
│  │  ├─ api.py
│  │  ├─ cors.py
│  │  ├─ logger.py
│  │  ├─ security.py
│  │  └─ __init__.py
│  └─ __init__.py
├─ config.py
├─ database
│  ├─ migrations
│  ├─ procedures
│  ├─ schema
│  └─ seeds
├─ deployment
│  ├─ kubernetes
│  ├─ nginx
│  ├─ systemd
│  └─ terraform
├─ docs
│  ├─ api
│  ├─ guides
│  ├─ images
│  └─ technical
├─ frontend
│  ├─ package-lock.json
│  ├─ package.json
│  ├─ public
│  ├─ src
│  │  ├─ assets
│  │  │  ├─ fonts
│  │  │  ├─ images
│  │  │  └─ vendor
│  │  ├─ css
│  │  │  ├─ main.css
│  │  │  ├─ tailwind-input.css
│  │  │  └─ tailwind.css
│  │  ├─ faculty
│  │  │  └─ dashboard.html
│  │  ├─ index.html
│  │  ├─ js
│  │  │  ├─ api
│  │  │  │  ├─ auth.js
│  │  │  │  ├─ client.js
│  │  │  │  ├─ main.js
│  │  │  │  └─ mock-data.js
│  │  │  ├─ auth
│  │  │  ├─ components
│  │  │  ├─ faculty
│  │  │  │  └─ dashboard.js
│  │  │  ├─ pages
│  │  │  ├─ register.js
│  │  │  ├─ student
│  │  │  │  └─ dashboard.js
│  │  │  └─ utils
│  │  │     └─ auth-guard.js
│  │  ├─ register.html
│  │  └─ student
│  │     └─ dashboard.html
│  ├─ tailwind.config.js
│  └─ templates
│     ├─ admin
│     ├─ auth
│     ├─ components
│     ├─ errors
│     ├─ faculty
│     ├─ layouts
│     └─ student
├─ ml_models
├─ package.json
├─ README.md
├─ requirements.txt
├─ scripts
│  ├─ data
│  ├─ database
│  │  ├─ schema
│  │  │  ├─ 01_users.sql
│  │  │  ├─ 02_academic.sql
│  │  │  ├─ 03_tracking.sql
│  │  │  ├─ 04_assessment.sql
│  │  │  ├─ 05_prediction.sql
│  │  │  ├─ 06_alerts.sql
│  │  │  └─ 07_system.sql
│  │  └─ seeds
│  │     ├─ 01_users.sql
│  │     ├─ 02_academic.sql
│  │     └─ 03_assessment_types.sql
│  ├─ deployment
│  ├─ maintenance
│  └─ setup
│     ├─ initialize_db.py
│     └─ setup_database.py
├─ setup_project.py
├─ tests
│  ├─ e2e
│  ├─ fixtures
│  ├─ integration
│  └─ unit
└─ wsgi.py

```
```
university-grade-prediction-system
├─ backend
│  ├─ api
│  │  ├─ admin
│  │  │  ├─ routes.py
│  │  │  └─ __init__.py
│  │  ├─ auth
│  │  │  ├─ routes.py
│  │  │  └─ __init__.py
│  │  ├─ common
│  │  │  ├─ routes.py
│  │  │  └─ __init__.py
│  │  ├─ faculty
│  │  │  ├─ routes.py
│  │  │  └─ __init__.py
│  │  ├─ prediction
│  │  │  ├─ routes.py
│  │  │  └─ __init__.py
│  │  ├─ student
│  │  │  ├─ routes.py
│  │  │  └─ __init__.py
│  │  └─ __init__.py
│  ├─ app.py
│  ├─ extensions.py
│  ├─ middleware
│  │  ├─ auth_middleware.py
│  │  ├─ error_handler.py
│  │  └─ __init__.py
│  ├─ ml_integration
│  │  └─ __init__.py
│  ├─ models
│  │  ├─ academic.py
│  │  ├─ alert.py
│  │  ├─ assessment.py
│  │  ├─ prediction.py
│  │  ├─ system.py
│  │  ├─ tracking.py
│  │  ├─ user.py
│  │  └─ __init__.py
│  ├─ services
│  │  ├─ auth_service.py
│  │  ├─ faculty_service.py
│  │  ├─ student_service.py
│  │  └─ __init__.py
│  ├─ tasks
│  ├─ utils
│  │  ├─ api.py
│  │  ├─ cors.py
│  │  ├─ logger.py
│  │  ├─ security.py
│  │  └─ __init__.py
│  └─ __init__.py
├─ config.py
├─ database
│  ├─ migrations
│  ├─ procedures
│  ├─ schema
│  └─ seeds
├─ deployment
│  ├─ kubernetes
│  ├─ nginx
│  ├─ systemd
│  └─ terraform
├─ docs
│  ├─ api
│  ├─ guides
│  ├─ images
│  └─ technical
├─ frontend
│  ├─ package-lock.json
│  ├─ package.json
│  ├─ public
│  ├─ src
│  │  ├─ assets
│  │  │  ├─ fonts
│  │  │  ├─ images
│  │  │  └─ vendor
│  │  ├─ css
│  │  │  ├─ main.css
│  │  │  ├─ tailwind-input.css
│  │  │  └─ tailwind.css
│  │  ├─ faculty
│  │  │  └─ dashboard.html
│  │  ├─ index.html
│  │  ├─ js
│  │  │  ├─ api
│  │  │  │  ├─ auth.js
│  │  │  │  ├─ client.js
│  │  │  │  ├─ main.js
│  │  │  │  └─ mock-data.js
│  │  │  ├─ auth
│  │  │  ├─ components
│  │  │  ├─ faculty
│  │  │  │  └─ dashboard.js
│  │  │  ├─ homepage.js
│  │  │  ├─ login.js
│  │  │  ├─ pages
│  │  │  ├─ register.js
│  │  │  ├─ student
│  │  │  │  └─ dashboard.js
│  │  │  └─ utils
│  │  │     └─ auth-guard.js
│  │  ├─ login.html
│  │  ├─ register.html
│  │  └─ student
│  │     └─ dashboard.html
│  ├─ tailwind.config.js
│  └─ templates
│     ├─ admin
│     ├─ auth
│     ├─ components
│     ├─ errors
│     ├─ faculty
│     ├─ layouts
│     └─ student
├─ ml_models
├─ package.json
├─ README.md
├─ requirements.txt
├─ scripts
│  ├─ clean_database.py
│  ├─ data
│  ├─ database
│  │  ├─ schema
│  │  │  ├─ 01_users.sql
│  │  │  ├─ 02_academic.sql
│  │  │  ├─ 03_tracking.sql
│  │  │  ├─ 04_assessment.sql
│  │  │  ├─ 05_prediction.sql
│  │  │  ├─ 06_alerts.sql
│  │  │  └─ 07_system.sql
│  │  └─ seeds
│  │     ├─ 01_users.sql
│  │     ├─ 02_academic.sql
│  │     └─ 03_assessment_types.sql
│  ├─ deployment
│  ├─ maintenance
│  ├─ seed_database.py
│  └─ setup
│     ├─ initialize_db.py
│     └─ setup_database.py
├─ setup_project.py
├─ tests
│  ├─ e2e
│  ├─ fixtures
│  ├─ integration
│  └─ unit
└─ wsgi.py

```
```
university-grade-prediction-system
├─ backend
│  ├─ api
│  │  ├─ admin
│  │  │  ├─ routes.py
│  │  │  └─ __init__.py
│  │  ├─ auth
│  │  │  ├─ routes.py
│  │  │  └─ __init__.py
│  │  ├─ common
│  │  │  ├─ routes.py
│  │  │  └─ __init__.py
│  │  ├─ faculty
│  │  │  ├─ attendance_routes.py
│  │  │  ├─ routes.py
│  │  │  └─ __init__.py
│  │  ├─ prediction
│  │  │  ├─ routes.py
│  │  │  └─ __init__.py
│  │  ├─ student
│  │  │  ├─ routes.py
│  │  │  └─ __init__.py
│  │  └─ __init__.py
│  ├─ app.py
│  ├─ extensions.py
│  ├─ middleware
│  │  ├─ auth_middleware.py
│  │  ├─ error_handler.py
│  │  └─ __init__.py
│  ├─ ml_integration
│  │  └─ __init__.py
│  ├─ models
│  │  ├─ academic.py
│  │  ├─ alert.py
│  │  ├─ assessment.py
│  │  ├─ prediction.py
│  │  ├─ system.py
│  │  ├─ tracking.py
│  │  ├─ user.py
│  │  └─ __init__.py
│  ├─ services
│  │  ├─ assessment_service.py
│  │  ├─ attendance_service.py
│  │  ├─ auth_service.py
│  │  ├─ faculty_service.py
│  │  ├─ student_service.py
│  │  └─ __init__.py
│  ├─ tasks
│  ├─ utils
│  │  ├─ api.py
│  │  ├─ cors.py
│  │  ├─ logger.py
│  │  ├─ security.py
│  │  └─ __init__.py
│  └─ __init__.py
├─ config.py
├─ database
│  ├─ migrations
│  ├─ procedures
│  ├─ schema
│  └─ seeds
├─ deployment
│  ├─ kubernetes
│  ├─ nginx
│  ├─ systemd
│  └─ terraform
├─ docs
│  ├─ api
│  ├─ guides
│  ├─ images
│  └─ technical
├─ frontend
│  ├─ package-lock.json
│  ├─ package.json
│  ├─ public
│  ├─ src
│  │  ├─ assets
│  │  │  ├─ fonts
│  │  │  ├─ images
│  │  │  └─ vendor
│  │  ├─ css
│  │  │  ├─ main.css
│  │  │  ├─ tailwind-input.css
│  │  │  └─ tailwind.css
│  │  ├─ faculty
│  │  │  ├─ assessment-create.html
│  │  │  ├─ assessment-grade.html
│  │  │  ├─ attendance.html
│  │  │  └─ dashboard.html
│  │  ├─ index.html
│  │  ├─ js
│  │  │  ├─ api
│  │  │  │  ├─ auth.js
│  │  │  │  ├─ client.js
│  │  │  │  ├─ main.js
│  │  │  │  └─ mock-data.js
│  │  │  ├─ auth
│  │  │  ├─ components
│  │  │  ├─ faculty
│  │  │  │  ├─ assessment-create.js
│  │  │  │  ├─ assessment-grade.js
│  │  │  │  ├─ attendance.js
│  │  │  │  └─ dashboard.js
│  │  │  ├─ homepage.js
│  │  │  ├─ login.js
│  │  │  ├─ pages
│  │  │  ├─ register.js
│  │  │  ├─ student
│  │  │  │  └─ dashboard.js
│  │  │  └─ utils
│  │  │     └─ auth-guard.js
│  │  ├─ login.html
│  │  ├─ register.html
│  │  └─ student
│  │     └─ dashboard.html
│  ├─ tailwind.config.js
│  └─ templates
│     ├─ admin
│     ├─ auth
│     ├─ components
│     ├─ errors
│     ├─ faculty
│     ├─ layouts
│     └─ student
├─ ml_models
├─ package.json
├─ README.md
├─ requirements.txt
├─ scripts
│  ├─ clean_database.py
│  ├─ data
│  ├─ database
│  │  ├─ schema
│  │  │  ├─ 01_users.sql
│  │  │  ├─ 02_academic.sql
│  │  │  ├─ 03_tracking.sql
│  │  │  ├─ 04_assessment.sql
│  │  │  ├─ 05_prediction.sql
│  │  │  ├─ 06_alerts.sql
│  │  │  └─ 07_system.sql
│  │  └─ seeds
│  │     ├─ 01_users.sql
│  │     ├─ 02_academic.sql
│  │     └─ 03_assessment_types.sql
│  ├─ deployment
│  ├─ maintenance
│  ├─ seed_database.py
│  └─ setup
│     ├─ initialize_db.py
│     └─ setup_database.py
├─ setup_project.py
├─ tests
│  ├─ e2e
│  ├─ fixtures
│  ├─ integration
│  └─ unit
└─ wsgi.py

```
```
university-grade-prediction-system
├─ backend
│  ├─ api
│  │  ├─ admin
│  │  │  ├─ routes.py
│  │  │  └─ __init__.py
│  │  ├─ alert
│  │  │  ├─ routes.py
│  │  │  └─ __init__.py
│  │  ├─ auth
│  │  │  ├─ routes.py
│  │  │  └─ __init__.py
│  │  ├─ common
│  │  │  ├─ routes.py
│  │  │  └─ __init__.py
│  │  ├─ faculty
│  │  │  ├─ attendance_routes.py
│  │  │  ├─ routes.py
│  │  │  └─ __init__.py
│  │  ├─ prediction
│  │  │  ├─ routes.py
│  │  │  └─ __init__.py
│  │  ├─ student
│  │  │  ├─ attendance_routes.py
│  │  │  ├─ routes.py
│  │  │  └─ __init__.py
│  │  └─ __init__.py
│  ├─ app.py
│  ├─ commands.py
│  ├─ extensions.py
│  ├─ middleware
│  │  ├─ activity_tracker.py
│  │  ├─ auth_middleware.py
│  │  ├─ error_handler.py
│  │  └─ __init__.py
│  ├─ migrations
│  │  └─ add_submission_fields.py
│  ├─ ml_integration
│  │  └─ __init__.py
│  ├─ models
│  │  ├─ academic.py
│  │  ├─ alert.py
│  │  ├─ assessment.py
│  │  ├─ attendance.py
│  │  ├─ prediction.py
│  │  ├─ system.py
│  │  ├─ tracking.py
│  │  ├─ user.py
│  │  └─ __init__.py
│  ├─ services
│  │  ├─ alert_service.py
│  │  ├─ assessment_service.py
│  │  ├─ attendance_service.py
│  │  ├─ auth_service.py
│  │  ├─ course_service.py
│  │  ├─ email_service.py
│  │  ├─ faculty_service.py
│  │  ├─ feature_calculator_service.py
│  │  ├─ file_service.py
│  │  ├─ lms_summary_service.py
│  │  ├─ model_service.py
│  │  ├─ prediction_service.py
│  │  ├─ production_mapper.py
│  │  ├─ student_service.py
│  │  ├─ unified_feature_calculator.py
│  │  └─ __init__.py
│  ├─ tasks
│  │  └─ scheduled_tasks.py
│  ├─ utils
│  │  ├─ api.py
│  │  ├─ cors.py
│  │  ├─ decorators.py
│  │  ├─ helpers.py
│  │  ├─ logger.py
│  │  ├─ security.py
│  │  └─ __init__.py
│  └─ __init__.py
├─ config.py
├─ database
│  ├─ migrations
│  ├─ procedures
│  ├─ schema
│  └─ seeds
├─ deployment
│  ├─ kubernetes
│  ├─ nginx
│  ├─ systemd
│  └─ terraform
├─ docs
│  ├─ api
│  ├─ guides
│  ├─ images
│  └─ technical
├─ frontend
│  ├─ package-lock.json
│  ├─ package.json
│  ├─ public
│  │  └─ js
│  │     └─ components
│  │        └─ alerts.js
│  ├─ src
│  │  ├─ assets
│  │  │  ├─ fonts
│  │  │  ├─ images
│  │  │  └─ vendor
│  │  ├─ css
│  │  │  ├─ main.css
│  │  │  ├─ tailwind-input.css
│  │  │  └─ tailwind.css
│  │  ├─ faculty
│  │  │  ├─ assessment-create.html
│  │  │  ├─ assessment-edit.html
│  │  │  ├─ assessment-grade.html
│  │  │  ├─ assessment-submissions.html
│  │  │  ├─ assessments.html
│  │  │  ├─ at-risk-students.html
│  │  │  ├─ attendance.html
│  │  │  ├─ courses.html
│  │  │  ├─ dashboard.html
│  │  │  ├─ profile.html
│  │  │  ├─ student-detail.html
│  │  │  └─ students.html
│  │  ├─ index.html
│  │  ├─ js
│  │  │  ├─ api
│  │  │  │  ├─ auth.js
│  │  │  │  ├─ client.js
│  │  │  │  ├─ faculty.js
│  │  │  │  ├─ main.js
│  │  │  │  ├─ mock-data.js
│  │  │  │  └─ student.js
│  │  │  ├─ auth
│  │  │  ├─ components
│  │  │  ├─ faculty
│  │  │  │  ├─ assessment-create.js
│  │  │  │  ├─ assessment-edit.js
│  │  │  │  ├─ assessment-grade.js
│  │  │  │  ├─ assessment-submissions.js
│  │  │  │  ├─ assessments.js
│  │  │  │  ├─ at-risk-students.js
│  │  │  │  ├─ attendance.js
│  │  │  │  ├─ courses.js
│  │  │  │  ├─ dashboard.js
│  │  │  │  ├─ student-detail.js
│  │  │  │  └─ students.js
│  │  │  ├─ homepage.js
│  │  │  ├─ login.js
│  │  │  ├─ pages
│  │  │  ├─ register.js
│  │  │  ├─ student
│  │  │  │  ├─ assessment-submit.js
│  │  │  │  ├─ assessments.js
│  │  │  │  ├─ attendance.js
│  │  │  │  ├─ course-enrollment.js
│  │  │  │  ├─ courses.js
│  │  │  │  ├─ dashboard.js
│  │  │  │  ├─ grades.js
│  │  │  │  ├─ predictions.js
│  │  │  │  └─ profile.js
│  │  │  └─ utils
│  │  │     └─ auth-guard.js
│  │  ├─ login.html
│  │  ├─ register.html
│  │  └─ student
│  │     ├─ assessment-submit.html
│  │     ├─ assessments.html
│  │     ├─ attendance.html
│  │     ├─ course-enrollment.html
│  │     ├─ courses.html
│  │     ├─ dashboard.html
│  │     ├─ grades.html
│  │     ├─ predictions.html
│  │     └─ profile.html
│  ├─ tailwind.config.js
│  └─ templates
│     ├─ admin
│     ├─ auth
│     ├─ components
│     ├─ errors
│     ├─ faculty
│     ├─ layouts
│     └─ student
├─ migrations
│  ├─ alembic.ini
│  ├─ env.py
│  ├─ README
│  ├─ script.py.mako
│  └─ versions
│     └─ b5d0d9eed142_basic_structure_completed_with_some_.py
├─ ml_models
│  ├─ feature_list.json
│  ├─ feature_mapping.yaml
│  ├─ grade_predictor.pkl
│  ├─ model_metadata.json
│  ├─ scaler.pkl
│  └─ validate_model.py
├─ package.json
├─ README.md
├─ requirements.txt
├─ scripts
│  ├─ add_profile_columns.py
│  ├─ add_profile_fields.py
│  ├─ add_submission_columns.py
│  ├─ batch_prediction_processor.py
│  ├─ clean_database.py
│  ├─ data
│  ├─ database
│  │  ├─ schema
│  │  │  ├─ 01_users.sql
│  │  │  ├─ 02_academic.sql
│  │  │  ├─ 03_tracking.sql
│  │  │  ├─ 04_assessment.sql
│  │  │  ├─ 05_prediction.sql
│  │  │  ├─ 06_alerts.sql
│  │  │  └─ 07_system.sql
│  │  └─ seeds
│  │     ├─ 01_users.sql
│  │     ├─ 02_academic.sql
│  │     └─ 03_assessment_types.sql
│  ├─ deployment
│  ├─ init_database.py
│  ├─ integrate_ml_model.py
│  ├─ maintenance
│  ├─ populate_test_data.py
│  ├─ seed_database.py
│  ├─ setup
│  │  ├─ initialize_db.py
│  │  └─ setup_database.py
│  ├─ test_model.py
│  └─ verify_features.py
├─ setup_project.py
├─ tests
│  ├─ e2e
│  ├─ fixtures
│  ├─ integration
│  └─ unit
├─ test_pickle_versions.py
└─ wsgi.py

```