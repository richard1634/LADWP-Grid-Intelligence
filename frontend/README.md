# LADWP Grid Intelligence Dashboard v2.0
## React + TypeScript Frontend with FastAPI Backend

This is the migrated version of the Streamlit dashboard using modern web technologies for better performance and user experience.

## 🏗️ Architecture

**Frontend:**
- React 18 with TypeScript
- Vite for fast development
- Tailwind CSS for styling
- Recharts for data visualization
- TanStack Query for data fetching
- Framer Motion for animations

**Backend:**
- FastAPI (Python)
- Keeps existing CAISO API client logic
- REST API endpoints
- WebSocket support for real-time updates

## 📦 Installation

### 1. Install Backend Dependencies

```bash
# From project root
pip install fastapi uvicorn websockets

# Or add to requirements.txt
fastapi==0.104.1
uvicorn[standard]==0.24.0
websockets==12.0
```

### 2. Install Frontend Dependencies

```bash
cd frontend
npm install
```

## 🚀 Running the Application

### Start Backend (Terminal 1)

```bash
# From project root
python api_server.py
```

The API will be available at:
- API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- WebSocket: ws://localhost:8000/ws/updates

### Start Frontend (Terminal 2)

```bash
cd frontend
npm run dev
```

The frontend will be available at:
- Frontend: http://localhost:5173

## 📁 Project Structure

```
LADWP/
├── api_server.py              # FastAPI backend
├── caiso_api_client.py        # Existing CAISO client (unchanged)
├── models/                    # ML models (unchanged)
├── data/                      # Data files (unchanged)
├── frontend/
│   ├── src/
│   │   ├── api/
│   │   │   └── client.ts      # API client
│   │   ├── components/
│   │   │   ├── ui/            # Reusable UI components
│   │   │   ├── GridStatusCards.tsx
│   │   │   ├── DemandForecastChart.tsx
│   │   │   ├── PriceChart.tsx
│   │   │   ├── MLAnomalyDetection.tsx
│   │   │   ├── SmartRecommendations.tsx
│   │   │   ├── Sidebar.tsx
│   │   │   └── Header.tsx
│   │   ├── pages/
│   │   │   └── Dashboard.tsx  # Main dashboard page
│   │   ├── hooks/
│   │   │   └── useAutoRefresh.ts
│   │   ├── types/
│   │   │   └── index.ts       # TypeScript types
│   │   ├── lib/
│   │   │   └── utils.ts       # Utility functions
│   │   ├── App.tsx            # Root component
│   │   ├── main.tsx           # Entry point
│   │   └── index.css          # Global styles
│   ├── package.json
│   ├── vite.config.ts
│   ├── tsconfig.json
│   └── tailwind.config.js
└── README.md
```

## 🎯 Features Preserved from Streamlit

✅ All current functionality maintained:
- Real-time grid status monitoring
- 48-hour demand forecasts
- Price analysis with spike detection
- ML-powered anomaly detection
- Smart recommendations
- Auto-refresh capability
- Date selection for historical data
- Grid stress scoring

✅ **New improvements:**
- Faster page loads (no full reloads)
- Smooth animations and transitions
- Better mobile responsiveness
- WebSocket support for real-time updates
- Improved error handling
- Better TypeScript type safety
- Modern UI/UX

## 🔧 Development

### Run in Development Mode

```bash
# Backend with auto-reload
python api_server.py

# Frontend with hot module replacement
cd frontend && npm run dev
```

### Build for Production

```bash
cd frontend
npm run build
```

Build output will be in `frontend/dist/`

### Type Checking

```bash
cd frontend
npm run type-check
```

### Linting

```bash
cd frontend
npm run lint
```

## 🌐 API Endpoints

All endpoints return JSON with the structure:
```json
{
  "success": boolean,
  "data": <response data>,
  "count": number (optional),
  "message": string (optional)
}
```

### Available Endpoints:

- `GET /` - API health check
- `GET /api/grid-status` - Current grid status with all metrics
- `GET /api/demand-forecast?date=<ISO-date>` - 48-hour demand forecast
- `GET /api/prices?hours_back=6` - Real-time price data
- `GET /api/ml-predictions?month=<month>` - ML anomaly predictions
- `GET /api/recommendations?month=<month>` - Smart recommendations
- `GET /api/health` - Backend health check
- `WS /ws/updates` - WebSocket for real-time updates

## ⚙️ Configuration

### Environment Variables

Create `frontend/.env`:

```env
VITE_API_URL=http://localhost:8000
```

### API Configuration

Edit `api_server.py` to change:
- Port (default: 8000)
- CORS origins
- Rate limiting
- Cache settings

## 📊 Data Flow

1. Frontend makes API requests via `api/client.ts`
2. TanStack Query manages caching and refetching
3. FastAPI backend processes requests
4. Existing Python logic (CAISO client, ML models) unchanged
5. Data returned as JSON to frontend
6. React components render the data

## 🎨 Customization

### Styling

Edit `frontend/tailwind.config.js` to customize:
- Colors (LADWP brand colors)
- Fonts
- Spacing
- Animations

### Components

All components in `frontend/src/components/` are modular and reusable.

## 🐛 Troubleshooting

**Backend won't start:**
- Check if port 8000 is available
- Verify all Python dependencies installed
- Check `api_server.py` for errors

**Frontend won't start:**
- Run `npm install` in frontend directory
- Check if port 5173 is available
- Clear node_modules and reinstall if needed

**API connection errors:**
- Verify backend is running
- Check CORS settings in `api_server.py`
- Verify API_URL in frontend `.env`

**WebSocket connection fails:**
- Check firewall settings
- Verify backend WebSocket endpoint is running
- Check browser console for errors

## 🚀 Deployment

### Backend Deployment

```bash
# Using gunicorn
pip install gunicorn
gunicorn api_server:app -w 4 -k uvicorn.workers.UvicornWorker
```

### Frontend Deployment

```bash
cd frontend
npm run build
# Deploy dist/ folder to your web server (Nginx, Apache, Vercel, Netlify, etc.)
```

## 📝 Migration Notes

### What Changed:
- Streamlit → React + FastAPI
- Python UI → TypeScript + React components
- Plotly → Recharts
- st.cache → TanStack Query
- Page reloads → SPA with smooth transitions

### What Stayed the Same:
- All Python backend logic
- CAISO API client
- ML models and predictions
- Data processing
- Recommendations engine
- All features and functionality

## 📚 Additional Resources

- [React Documentation](https://react.dev/)
- [TypeScript Handbook](https://www.typescriptlang.org/docs/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [TanStack Query](https://tanstack.com/query/latest)
- [Tailwind CSS](https://tailwindcss.com/)
- [Recharts](https://recharts.org/)

## 🙋 Support

For issues or questions:
1. Check API docs at http://localhost:8000/docs
2. Check browser console for frontend errors
3. Check terminal for backend errors
4. Review this README

## 📄 License

Same as the original LADWP Grid Intelligence Dashboard project.
