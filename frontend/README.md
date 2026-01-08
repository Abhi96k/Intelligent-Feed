# Intelligent Feed Frontend

A modern React-based frontend for the Intelligent Feed analytics system. This application provides an intuitive interface for asking questions about data and receiving AI-powered insights, trends, and driver analysis.

## Features

- **Question-based Analysis**: Ask natural language questions about your data
- **Intelligent Insights**: View triggered insights with confidence scores
- **Trend Visualization**: Interactive line charts showing metric trends over time
- **Driver Impact Analysis**: Bar charts displaying key drivers and their impact
- **Real-time Updates**: Powered by React Query for efficient state management
- **Responsive Design**: Clean, professional UI built with Tailwind CSS
- **Type Safety**: JSDoc type definitions for better development experience

## Tech Stack

- **React 18**: Modern React with hooks and functional components
- **Vite**: Fast build tool and development server
- **Tailwind CSS**: Utility-first CSS framework
- **Recharts**: Composable charting library
- **React Query**: Powerful data synchronization
- **Axios**: HTTP client for API communication

## Prerequisites

- Node.js 16+ and npm/yarn
- Backend API running on http://localhost:8000

## Installation

1. Install dependencies:
```bash
npm install
```

2. Start the development server:
```bash
npm run dev
```

The application will be available at http://localhost:3000

## Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run lint` - Run ESLint

## Project Structure

```
frontend/
├── public/              # Static assets
├── src/
│   ├── components/      # React components
│   │   ├── QuestionInput.jsx
│   │   ├── InsightCard.jsx
│   │   ├── TrendChart.jsx
│   │   └── DriverImpactChart.jsx
│   ├── services/        # API services
│   │   └── api.js
│   ├── types/           # Type definitions
│   │   └── index.js
│   ├── App.jsx          # Main app component
│   ├── main.jsx         # Entry point
│   └── index.css        # Global styles
├── index.html           # HTML template
├── package.json         # Dependencies
├── vite.config.js       # Vite configuration
└── tailwind.config.js   # Tailwind configuration
```

## API Integration

The frontend communicates with the backend through a Vite proxy configured in `vite.config.js`:

- Frontend requests to `/api/*` are proxied to `http://localhost:8000/*`
- Example: `POST /api/analyze` → `http://localhost:8000/analyze`

## Components

### QuestionInput
Input component for entering questions with Run and Clear buttons. Includes example questions and character counter.

### InsightCard
Displays individual insights with status badges, confidence scores, and metadata. Supports different insight types (anomaly, trend, correlation, etc.).

### TrendChart
Line chart component using Recharts to visualize time series data with trend direction indicators.

### DriverImpactChart
Horizontal bar chart showing driver impact analysis with positive/negative impact indicators.

## Styling

The application uses a professional data analytics aesthetic with:
- Clean white/blue color scheme
- Inter font family
- Consistent spacing and typography
- Responsive grid layouts
- Custom Tailwind utilities

## Development

### Adding New Components

1. Create component in `src/components/`
2. Import and use in `App.jsx`
3. Add JSDoc comments for props

### Updating API Endpoints

1. Add new API functions in `src/services/api.js`
2. Define types in `src/types/index.js`
3. Use with React Query hooks

### Customizing Styles

1. Update Tailwind theme in `tailwind.config.js`
2. Add custom utilities in `src/index.css`
3. Use Tailwind classes in components

## Browser Support

- Chrome (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)

## Troubleshooting

### Backend Connection Issues

If you see "No response from server" errors:
1. Verify backend is running on port 8000
2. Check Vite proxy configuration
3. Ensure CORS is properly configured on backend

### Build Errors

If build fails:
1. Delete `node_modules` and reinstall: `rm -rf node_modules && npm install`
2. Clear Vite cache: `rm -rf node_modules/.vite`
3. Check Node.js version: `node --version`

## License

MIT
