# Phase 1 Quick Start Guide

## Installation

```bash
# Install dependencies
pip install bcrypt flask-socketio python-socketio python-dotenv --break-system-packages

# Upgrade database schema
python database_upgrade.py

# Seed demo data
python seed_demo.py

# Validate installation
python validate_phase1.py
```

## Run Server

```bash
python app.py
```

Visit: http://localhost:5000/login

## Demo Credentials

### Operators
- **demo_operator1** / Operator@123
- **demo_operator2** / Operator@456
- **demo_operator3** / Operator@789

### Citizens
- **demo_citizen1** / Citizen@123
- **demo_citizen2** / Citizen@456
- **demo_citizen3** / Citizen@789
- **demo_citizen4** / Citizen@101
- **demo_citizen5** / Citizen@202

## Key Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/login` | GET | Login page |
| `/auth/login` | POST | Authenticate |
| `/auth/logout` | POST | Logout |
| `/auth/register` | POST | Register (citizens) |
| `/auth/me` | GET | Current user |
| `/health` | GET | System health |
| `/operator/dashboard` | GET | Operator portal |
| `/citizen/dashboard` | GET | Citizen portal |

## SocketIO Namespaces

| Namespace | Purpose |
|-----------|---------|
| `/operator` | Operator connections |
| `/citizen` | Citizen connections |
| `/signals` | Traffic signal broadcasts |
| `/camera` | Camera feed events |
| `/notifications` | System alerts |

## Testing

```bash
# Integration tests
python test_phase1.py

# Validation
python validate_phase1.py
```

## Files Added

- `auth.py` - Authentication & RBAC
- `realtime.py` - SocketIO setup
- `middleware.py` - Security middleware
- `database_upgrade.py` - Schema migration
- `seed_demo.py` - Demo data
- `routes/auth_routes.py` - Auth endpoints
- `routes/operator_routes.py` - Operator stub
- `routes/citizen_routes.py` - Citizen stub
- `static/css/theme.css` - Orange/black theme
- `static/js/theme-utils.js` - UI utilities
- `templates/login.html` - Login page
- `templates/error.html` - Error pages
- `.env.example` - Config template
- `.gitignore` - Git ignore rules

## Database Tables (New)

- `users` - User accounts
- `sessions` - Active sessions
- `intersections` - Traffic intersections
- `traffic_signals` - Signal states
- `appeals` - Violation appeals
- `wallet` - Payment wallets
- `wallet_transactions` - Transaction history
- `audit_logs` - Audit trail

## Theme Colors

- **Primary:** Orange (#ff8c00)
- **Background:** Black (#0a0a0a)
- **Cards:** Dark Gray (#1a1a1a)
- **Success:** Green (#2ecc71)
- **Danger:** Red (#e74c3c)
- **Warning:** Amber (#f39c12)

## Troubleshooting

**Import errors?**
```bash
pip install bcrypt flask-socketio --break-system-packages
```

**Database locked?**
```bash
# Stop any running app instances
pkill -f app.py
```

**Session issues?**
```bash
# Clear browser cookies and restart server
```

## Next Phase

Phase 2 will implement:
- Operator dashboard
- Live intersection monitoring
- Signal override controls
- Network visualization

---

For detailed documentation, see:
- `PHASE1_README.md` - Complete guide
- `PHASE1_SUMMARY.md` - Implementation details
