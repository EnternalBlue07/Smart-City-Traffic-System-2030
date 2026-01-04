# Phase 2 Quick Start - Operator Dashboard

## Access the Dashboard

1. **Start the server** (if not already running):
   ```bash
   python app.py
   ```

2. **Login as Operator:**
   - URL: http://localhost:5000/login?portal=operator
   - Username: `demo_operator1`
   - Password: `Operator@123`

3. **Dashboard loads automatically** at `/operator/dashboard`

## Dashboard Features

### Top Bar
- **System Title**: Traffic Control Center
- **User Info**: Shows logged-in operator
- **Logout Button**: End session

### Statistics Cards (Top Row)
- **Active Intersections**: 4/4 intersections online
- **Violations Today**: Real-time count
- **Pending Appeals**: Awaiting operator review
- **Active Signals**: Number of green lights

### Network Map (Left Panel)
- **Orange Markers**: Active intersections
- **Amber Markers**: Warning status
- **Red Markers**: Offline
- **Click Marker**: View intersection details

### Live Violations Feed (Right Panel)
- **Real-time Updates**: New violations appear at top
- **Auto-refresh**: Every 5 seconds
- **Shows**: License plate, violation type, location, camera, fine amount
- **Animation**: Slide-in effect for new items

### Intersection Controls (Bottom Section)
- **Signal Display**: NS/EW directions with colored indicators
  - 🟢 Green circle = Active
  - 🔴 Red circle = Stop
  - 🟠 Amber circle = Caution
- **Countdown Timers**: Shows remaining seconds
- **Control Buttons**:
  - "Control NS" - Override North-South signal
  - "Control EW" - Override East-West signal
  - "Emergency" (red, pulsing) - Emergency preemption

## Manual Signal Override

### Step 1: Click Control Button
- Choose "Control NS" or "Control EW"
- Modal opens with signal options

### Step 2: Select Signal State
- Click one of three options:
  - 🟢 **Green** - Allow traffic flow
  - 🟠 **Amber** - Caution/transition
  - 🔴 **Red** - Stop traffic

### Step 3: Set Duration
- Input field shows default 60 seconds
- Range: 10-300 seconds
- Adjust as needed

### Step 4: Apply Override
- Click "Apply Override" button
- Confirmation toast appears
- Signal updates in UI immediately
- All operators see the change (WebSocket)
- Audit log created automatically

## Emergency Preemption

### When to Use
- Emergency vehicle approaching
- Accident at intersection
- Immediate traffic clearance needed

### How to Activate
1. Click red "Emergency" button on intersection card
2. Confirm the action in dialog
3. **All signals** at intersection turn RED immediately
4. Duration: 120 seconds
5. System broadcasts alert to all operators
6. Audit log created with your user ID

### Result
- All vehicles stop at intersection
- Emergency vehicle can pass safely
- Signals return to auto mode after 120 seconds

## API Endpoints (for testing)

### Get Overview Stats
```bash
curl http://localhost:5000/operator/api/overview \
  -H "Cookie: session_token=YOUR_TOKEN"
```

### List All Intersections
```bash
curl http://localhost:5000/operator/api/intersections \
  -H "Cookie: session_token=YOUR_TOKEN"
```

### Get Intersection Details
```bash
curl http://localhost:5000/operator/api/intersections/1 \
  -H "Cookie: session_token=YOUR_TOKEN"
```

### Override Signal
```bash
curl -X POST http://localhost:5000/operator/api/signals/1/override \
  -H "Content-Type: application/json" \
  -H "Cookie: session_token=YOUR_TOKEN" \
  -d '{"state":"green","duration":60}'
```

### Emergency Preempt
```bash
curl -X POST http://localhost:5000/operator/api/intersections/1/emergency \
  -H "Cookie: session_token=YOUR_TOKEN"
```

### Get Recent Violations
```bash
curl http://localhost:5000/operator/api/violations/recent?limit=10 \
  -H "Cookie: session_token=YOUR_TOKEN"
```

### Get Hourly Analytics
```bash
curl http://localhost:5000/operator/api/analytics/hourly \
  -H "Cookie: session_token=YOUR_TOKEN"
```

## Real-Time Features

### WebSocket Connections
The dashboard automatically connects to:
- `/operator` - Operator events
- `/signals` - Signal state updates
- `/notifications` - System alerts

### Live Updates (No Refresh Needed)
- New violations appear instantly
- Signal overrides by other operators visible
- Emergency preemptions trigger alerts
- Stats refresh every 10 seconds

## Keyboard Shortcuts

- **ESC** - Close open modal
- *More shortcuts coming in Phase 3*

## Troubleshooting

### Dashboard not loading
- Check you're logged in as **operator** (not citizen)
- Clear browser cookies: `document.cookie.split(";").forEach(c => document.cookie = c.trim().split("=")[0] + "=;expires=Thu, 01 Jan 1970 00:00:00 UTC;path=/")`
- Verify session in browser console: `document.cookie`

### Signal override fails
- Check signal ID exists (view intersection details first)
- Verify duration is between 10-300 seconds
- Ensure state is exactly: "green", "red", or "amber"
- Check browser console for errors

### WebSocket not connecting
- Verify server started with `socketio.run()` not `app.run()`
- Check CORS settings in .env
- Look for console errors: `F12 → Console`
- Test connection: `io.connect('/operator')` in browser console

### Stats showing zeros
- Run `python seed_demo.py` to populate data
- Verify database exists: `ls database/violations.db`
- Check if intersections exist: `sqlite3 database/violations.db "SELECT * FROM intersections"`

## Demo Operators

All have same capabilities:

| Username | Password | Email |
|----------|----------|-------|
| demo_operator1 | Operator@123 | operator1@traffic.gov.in |
| demo_operator2 | Operator@456 | operator2@traffic.gov.in |
| demo_operator3 | Operator@789 | operator3@traffic.gov.in |

## Testing Multi-Operator

1. **Browser 1**: Login as demo_operator1
2. **Browser 2**: Login as demo_operator2 (incognito/private mode)
3. **Override signal in Browser 1**
4. **Watch update in Browser 2** (via WebSocket)

## Next Steps

- **Phase 3**: Predictive Traffic Management (ML-based optimization)
- **Phase 4**: Citizen Portal & Payments
- **Phase 5**: Advanced Analytics

## Support

For issues, check:
- `PHASE2_README.md` - Detailed documentation
- `/operator/api/system/status` - System health
- Browser console (F12) - JavaScript errors
- Server logs - Python errors

---

**Phase 2 Status**: ✅ **READY FOR USE**
