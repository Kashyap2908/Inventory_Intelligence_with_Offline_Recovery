# 📊 Automatic Trend Score System

## Overview
The trend score system automatically calculates and updates product demand scores (0-10 scale) based on real-time activity.

## How It Works

### Automatic Updates
Trend scores are automatically updated when:
1. ✅ **Inventory adds stock** - Updates immediately after stock entry
2. ✅ **Product request created** - Updates when inventory requests product
3. ✅ **Admin approves request** - Updates after approval and billing
4. ✅ **Scheduled updates** - Daily automatic updates at 2 AM

### Score Calculation (0-10 Scale)

**Base Score:** 5.0

**Factors:**
1. **Stock Movement (30% weight)**
   - Tracks how frequently stock is added/removed
   - More movement = Higher demand
   - Last 30 days activity

2. **Sales Frequency (30% weight)**
   - Counts billing frequency
   - More bills = Higher demand
   - Last 30 days activity

3. **Request Frequency (20% weight)**
   - Tracks product requests from inventory users
   - More requests = Higher demand
   - Last 30 days activity

4. **Stock Level (20% weight)**
   - Low stock + High activity = High demand
   - High stock + No activity = Low demand
   - Last 7 days activity

### Score Interpretation

| Score | Category | Meaning |
|-------|----------|---------|
| 8-10 | A - High Value | Very high demand, fast-moving |
| 5-7.9 | B - Medium Value | Moderate demand, steady sales |
| 0-4.9 | C - Low Value | Low demand, slow-moving |

## Manual Commands

### Update All Products
```bash
python manage.py update_trend_scores
```

### Setup Automatic Daily Updates (Windows)
```bash
setup_auto_trend_update.bat
```
(Run as Administrator)

### View Scheduled Task
```bash
schtasks /query /tn "NeuroStock_TrendUpdate"
```

### Delete Scheduled Task
```bash
schtasks /delete /tn "NeuroStock_TrendUpdate" /f
```

## Where to See Trend Scores

### Admin Dashboard
- **Trend Dashboard Tab** - View all products with trend scores
- **Stock Intelligence Tab** - See trend scores with stock analysis
- Scores update automatically in real-time

### Features
- 📈 Visual trend score display (0-10)
- 🎯 ABC classification based on scores
- 📊 Historical trend tracking
- 🔄 Real-time updates on activity

## Benefits

1. **Automatic Analysis** - No manual calculation needed
2. **Real-time Updates** - Scores update with every activity
3. **Data-Driven Decisions** - Make informed inventory decisions
4. **Demand Forecasting** - Predict which products need attention
5. **Stock Optimization** - Identify fast vs slow-moving items

## Technical Details

### Files
- `inventory/trend_calculator.py` - Core calculation logic
- `inventory/management/commands/update_trend_scores.py` - Management command
- `setup_auto_trend_update.bat` - Windows scheduler setup

### Integration Points
- Stock addition (inventory_dashboard view)
- Product requests (inventory_dashboard view)
- Request approval (admin_dashboard view)
- Scheduled updates (Windows Task Scheduler)

## Example Scenarios

### High Demand Product (Score: 9.2)
- 15 stock entries in last 30 days
- 20 bills generated
- 8 product requests
- Low stock (15 units) with high activity

### Low Demand Product (Score: 2.1)
- 1 stock entry in last 30 days
- 0 bills generated
- 0 product requests
- High stock (250 units) with no activity

## Troubleshooting

### Scores not updating?
1. Check if trend_calculator.py exists
2. Run manual update: `python manage.py update_trend_scores`
3. Check server logs for errors

### Scheduled task not running?
1. Verify task exists: `schtasks /query /tn "NeuroStock_TrendUpdate"`
2. Check task history in Task Scheduler
3. Re-run setup_auto_trend_update.bat as Administrator

---

**System is now fully automatic!** Trend scores update in real-time with every activity. 🎉
