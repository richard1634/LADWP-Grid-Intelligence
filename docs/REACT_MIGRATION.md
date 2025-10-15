# 🚀 React Migration Guide
## LADWP Grid Intelligence Dashboard v2.0

This guide will help you migrate from Streamlit to the new React + FastAPI stack.

## ✅ What's Been Set Up

### Backend (FastAPI)
- ✅ `api_server.py` - Complete REST API with all endpoints
- ✅ All existing Python logic preserved
- ✅ WebSocket support for real-time updates
- ✅ CORS configured for local development

### Frontend (React + TypeScript)
- ✅ Complete project structure in `frontend/` directory
- ✅ TypeScript configuration
- ✅ Tailwind CSS for styling
- ✅ API client with Axios
- ✅ React Query for data fetching
- ✅ Reusable UI components
- ✅ Grid Status Cards component (fully functional)
- ✅ Main Dashboard page with all sections

## 📦 Quick Start

### 1. Install Backend Dependencies

```bash
# Make sure you have FastAPI and Uvicorn
pip install fastapi uvicorn[standard] websockets
```

### 2. Install Frontend Dependencies

```bash
cd frontend
npm install
```

This will install:
- React & React DOM
- TypeScript
- Vite (build tool)
- Tailwind CSS
- Recharts (charts)
- TanStack Query (data fetching)
- Framer Motion (animations)
- Lucide React (icons)
- Axios (HTTP client)

### 3. Start the Backend

Open a terminal and run:

```bash
python api_server.py
```

You should see:
```
🚀 Starting LADWP Grid Intelligence API Server...
📊 Backend: Python + FastAPI
🎨 Frontend: React + TypeScript
🌐 API: http://localhost:8000
📚 Docs: http://localhost:8000/docs
```

The backend will be available at **http://localhost:8000**

### 4. Start the Frontend

Open a NEW terminal and run:

```bash
cd frontend
npm run dev
```

You should see:
```
VITE v5.x.x ready in xxx ms

➜  Local:   http://localhost:5173/
➜  Network: use --host to expose
```

The frontend will be available at **http://localhost:5173**

### 5. Open Your Browser

Navigate to **http://localhost:5173**

You should see the LADWP dashboard with:
- Grid Status Cards showing real-time data
- Demand forecast section (placeholder)
- ML anomaly detection section (placeholder)
- Smart recommendations section (placeholder)
- Price analysis section (placeholder)

## 🎯 Current Status

### ✅ Completed:
1. FastAPI backend with all endpoints
2. React project structure
3. TypeScript types and interfaces
4. API client with error handling
5. Grid Status Cards (fully functional!)
6. Loading states and error handling
7. Auto-refresh functionality
8. Responsive layout
9. LADWP branding and styling

### 🔄 In Progress (Placeholders):
The following components show data from the API but need chart implementations:
1. Demand Forecast Chart (data loads, needs Recharts implementation)
2. Price Chart (data loads, needs Recharts implementation)
3. ML Anomaly Detection Chart (data loads, needs visualization)
4. Smart Recommendations UI (data loads, needs cards implementation)

## 📊 What Works Right Now

### Grid Status Section ✅
- Shows real-time demand, price, stress level
- Updates automatically based on refresh interval
- Shows alert banners for high/critical stress
- Fully styled with animations

### Data Fetching ✅
- All API endpoints working
- Data refreshes every 5 minutes (configurable)
- Error handling and loading states
- React Query caching

### UI/UX ✅
- Responsive design
- LADWP color scheme
- Smooth animations
- Loading skeletons

## 🔨 Next Steps to Complete

To finish the migration, you need to implement these chart components:

### 1. Demand Forecast Chart
Create `frontend/src/components/DemandForecastChart.tsx` using Recharts:
- Line chart showing demand over 48 hours
- Separate historical and forecast data
- Peak demand markers
- Statistics sidebar

### 2. Price Chart
Create `frontend/src/components/PriceChart.tsx`:
- Line chart with price over time
- Spike markers (red diamonds)
- Price component breakdown
- Statistics sidebar

### 3. ML Anomaly Detection
Create `frontend/src/components/MLAnomalyDetection.tsx`:
- Scatter plot with anomaly markers
- Color-coded by severity
- Confidence scores
- Anomaly list with details

### 4. Smart Recommendations
Create `frontend/src/components/SmartRecommendations.tsx`:
- Expandable recommendation cards
- Priority badges
- Action items with icons
- Urgency indicators

## 📁 File Structure

```
LADWP/
├── api_server.py              ✅ Complete
├── caiso_api_client.py        ✅ Unchanged
├── models/                    ✅ Unchanged
├── data/                      ✅ Unchanged
└── frontend/
    ├── package.json           ✅ Complete
    ├── vite.config.ts         ✅ Complete
    ├── tsconfig.json          ✅ Complete
    ├── tailwind.config.js     ✅ Complete
    ├── postcss.config.js      ✅ Complete
    ├── index.html             ✅ Complete
    ├── src/
    │   ├── main.tsx           ✅ Complete
    │   ├── App.tsx            ✅ Complete
    │   ├── index.css          ✅ Complete
    │   ├── api/
    │   │   └── client.ts      ✅ Complete
    │   ├── types/
    │   │   └── index.ts       ✅ Complete
    │   ├── lib/
    │   │   └── utils.ts       ✅ Complete
    │   ├── components/
    │   │   ├── ui/
    │   │   │   ├── Card.tsx   ✅ Complete
    │   │   │   ├── MetricCard.tsx ✅ Complete
    │   │   │   ├── Badge.tsx  ✅ Complete
    │   │   │   └── Loading.tsx ✅ Complete
    │   │   ├── GridStatusCards.tsx ✅ Complete
    │   │   ├── DemandForecastChart.tsx 🔄 TODO
    │   │   ├── PriceChart.tsx 🔄 TODO
    │   │   ├── MLAnomalyDetection.tsx 🔄 TODO
    │   │   └── SmartRecommendations.tsx 🔄 TODO
    │   └── pages/
    │       └── Dashboard.tsx  ✅ Complete (with placeholders)
    └── README.md              ✅ Complete
```

## 🧪 Testing the Setup

### Test Backend API:
1. Open http://localhost:8000/docs
2. Try the `/api/grid-status` endpoint
3. Should return JSON with demand, price, and stress data

### Test Frontend:
1. Open http://localhost:5173
2. Should see the dashboard load
3. Grid Status section should show real data
4. Refresh interval dropdown should work
5. Data should auto-refresh every 5 minutes

### Test Data Flow:
1. Open browser DevTools (F12)
2. Go to Network tab
3. Should see API requests to http://localhost:8000/api/*
4. Should see successful responses with JSON data

## 🎨 Styling Guide

All components use Tailwind CSS with LADWP brand colors:

```css
--ladwp-blue: #003DA5
--ladwp-light-blue: #0066CC
--ladwp-dark-blue: #002B73
--ladwp-accent: #00A3E0
```

Use these classes:
- `text-ladwp-blue` - Primary blue text
- `bg-ladwp-blue` - Primary blue background
- `border-ladwp-accent` - Accent blue border
- etc.

## 🐛 Troubleshooting

### Backend Issues:

**Port 8000 already in use:**
```bash
# Kill the process or change the port in api_server.py
lsof -ti:8000 | xargs kill -9  # Mac/Linux
netstat -ano | findstr :8000  # Windows (then kill PID)
```

**Module not found:**
```bash
pip install -r requirements.txt
```

### Frontend Issues:

**Node modules issues:**
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
```

**Port 5173 in use:**
```bash
# Vite will automatically try the next available port
```

**TypeScript errors:**
```bash
cd frontend
npm run type-check
```

### CORS Issues:

If you see CORS errors in the browser console:
1. Check that backend is running on port 8000
2. Verify CORS origins in `api_server.py` include `http://localhost:5173`
3. Clear browser cache and reload

## 📚 Learn More

- **React**: https://react.dev/
- **TypeScript**: https://www.typescriptlang.org/
- **Vite**: https://vitejs.dev/
- **Tailwind CSS**: https://tailwindcss.com/
- **TanStack Query**: https://tanstack.com/query/latest
- **Recharts**: https://recharts.org/
- **FastAPI**: https://fastapi.tiangolo.com/

## 💡 Tips

1. **Hot Module Replacement**: Frontend updates instantly when you save files
2. **API Auto-Reload**: Backend reloads automatically when you save Python files
3. **Type Safety**: TypeScript will catch errors before runtime
4. **Dev Tools**: Use React DevTools browser extension
5. **API Docs**: Interactive API documentation at http://localhost:8000/docs

## 🎉 Success!

If you see the Grid Status section with real data updating, congratulations! The core migration is working.

The remaining work is implementing the chart components using Recharts, which will be straightforward following the examples in the Recharts documentation.

## 📞 Next Steps

1. Test the current setup (Grid Status should work)
2. Implement chart components one by one
3. Add any additional features you want
4. Deploy to production when ready

Happy coding! 🚀
