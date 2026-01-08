# Quick Start Guide

Get up and running with the Intelligent Feed frontend in 3 simple steps.

## Step 1: Install Dependencies

```bash
cd /Users/abhishek/Desktop/Hackthon/frontend
npm install
```

This will install all required packages:
- React 18.2.0
- Vite 5.0.11
- Tailwind CSS 3.4.1
- Recharts 2.10.3
- React Query 5.17.19
- Axios 1.6.5

## Step 2: Ensure Backend is Running

Make sure your backend API is running on `http://localhost:8000`. The frontend expects the following endpoints:

- `POST /analyze` - Main analysis endpoint
- `GET /health` - Health check (optional)

## Step 3: Start Development Server

```bash
npm run dev
```

The application will start at `http://localhost:3000`

## First Steps

1. Open your browser to `http://localhost:3000`
2. You'll see the Intelligent Feed dashboard
3. Enter a question in the text area (or click an example question)
4. Click "Run Analysis" to submit
5. View the results including:
   - Insights with triggered/not triggered status
   - Primary trend line chart
   - Driver impact bar chart
   - Summary and metadata

## Example Questions

Try these example questions to test the system:

- "Why did revenue drop in Q3?"
- "What are the main drivers of customer churn?"
- "Show me sales trends by region"

## Project Structure Overview

```
frontend/
├── src/
│   ├── components/          # UI Components
│   │   ├── QuestionInput.jsx      # Question input form
│   │   ├── InsightCard.jsx        # Insight display cards
│   │   ├── TrendChart.jsx         # Line chart for trends
│   │   └── DriverImpactChart.jsx  # Bar chart for drivers
│   ├── services/
│   │   └── api.js          # API client with axios
│   ├── types/
│   │   └── index.js        # JSDoc type definitions
│   ├── App.jsx             # Main application
│   ├── main.jsx            # Entry point
│   └── index.css           # Tailwind styles
├── package.json            # Dependencies
├── vite.config.js          # Vite config (proxy setup)
└── tailwind.config.js      # Tailwind theme
```

## Available Scripts

- `npm run dev` - Development server (port 3000)
- `npm run build` - Production build
- `npm run preview` - Preview production build
- `npm run lint` - Lint code

## Customization

### Change Backend URL

Edit `vite.config.js`:

```javascript
server: {
  proxy: {
    '/api': {
      target: 'http://your-backend-url:port',
      changeOrigin: true,
    }
  }
}
```

### Modify Color Scheme

Edit `tailwind.config.js` to change the primary colors:

```javascript
theme: {
  extend: {
    colors: {
      primary: {
        // Your custom colors
      }
    }
  }
}
```

### Add New Components

1. Create `src/components/YourComponent.jsx`
2. Import in `App.jsx`: `import YourComponent from './components/YourComponent'`
3. Use in JSX: `<YourComponent />`

## Troubleshooting

### "Cannot connect to backend"

Check:
1. Backend is running: `curl http://localhost:8000/health`
2. Vite proxy is configured correctly
3. No CORS issues

### "Module not found" errors

Run:
```bash
rm -rf node_modules package-lock.json
npm install
```

### Port 3000 already in use

Change port in `vite.config.js`:
```javascript
server: {
  port: 3001,  // or any other port
}
```

## Production Build

Build for production:
```bash
npm run build
```

Preview production build:
```bash
npm run preview
```

The built files will be in the `dist/` directory.

## Next Steps

- Customize the UI components to match your brand
- Add additional chart types if needed
- Implement authentication if required
- Add unit tests with Vitest
- Set up CI/CD pipeline

## Support

For issues or questions, refer to the main README.md or check the component documentation in the source files.
