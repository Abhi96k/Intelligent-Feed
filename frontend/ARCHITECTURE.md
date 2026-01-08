# Frontend Architecture

Visual overview of the Intelligent Feed frontend architecture.

## Component Hierarchy

```
App.jsx (Main Container)
│
├── Header (Built-in)
│   ├── Title: "Intelligent Feed"
│   ├── Subtitle: "AI-powered analytics insights..."
│   └── Status Badge: "Ready"
│
├── Main Content
│   │
│   ├── QuestionInput
│   │   ├── Textarea (question input)
│   │   ├── Character counter
│   │   ├── Buttons
│   │   │   ├── Clear button (conditional)
│   │   │   └── Run Analysis button
│   │   └── Example questions (clickable)
│   │
│   ├── Error Display (conditional)
│   │   └── Error message with details
│   │
│   └── Results Section (conditional, when results available)
│       │
│       ├── Question Echo Card
│       │   └── Shows submitted question
│       │
│       ├── Insights Grid
│       │   └── InsightCard[] (multiple)
│       │       ├── Insight type icon
│       │       ├── Status badge (triggered/not triggered)
│       │       ├── Confidence score
│       │       ├── Title
│       │       ├── Description
│       │       └── Metadata grid
│       │
│       ├── Charts Section
│       │   │
│       │   ├── TrendChart (Primary Trend)
│       │   │   ├── Chart header with metric name
│       │   │   ├── Trend indicator (up/down/stable)
│       │   │   ├── Percentage change
│       │   │   ├── Line chart (Recharts)
│       │   │   └── Anomalies info
│       │   │
│       │   └── DriverImpactChart (Driver Analysis)
│       │       ├── Chart header
│       │       ├── Primary driver label
│       │       ├── Horizontal bar chart (Recharts)
│       │       └── Summary stats (total, positive, negative)
│       │
│       ├── Summary Card
│       │   └── Text summary of analysis
│       │
│       └── Metadata Card
│           └── Analysis timestamp, counts, confidence
│
└── Footer (Built-in)
    └── "Powered by Intelligent Feed Analytics Engine"
```

## Data Flow

```
User Input → QuestionInput
                    ↓
            onClick(question)
                    ↓
            App.handleAnalyze
                    ↓
        analyzeMutation.mutate (React Query)
                    ↓
            services/api.js
                    ↓
        POST /api/analyze (Vite Proxy)
                    ↓
        Backend (localhost:8000)
                    ↓
        Response JSON
                    ↓
        analyzeMutation.onSuccess
                    ↓
        setResults(data)
                    ↓
        Re-render with Results
                    ↓
        Display: Insights, Charts, Summary
```

## State Management

### React Query (Server State)

```javascript
QueryClient
├── Mutations
│   └── analyzeQuestion
│       ├── isPending (loading state)
│       ├── isError (error state)
│       ├── isSuccess (success state)
│       └── data (response data)
│
└── Queries (future)
    ├── healthStatus
    ├── config
    └── history
```

### Local State (useState)

```javascript
App Component
└── results: AnalysisResponse | null
    ├── question: string
    ├── insights: Insight[]
    ├── primary_trend: PrimaryTrend
    ├── driver_impact: DriverImpact
    ├── summary: string
    └── metadata: Metadata

QuestionInput Component
└── question: string (input value)
```

## API Service Layer

```
src/services/api.js
│
├── apiClient (Axios instance)
│   ├── baseURL: '/api'
│   ├── timeout: 30000ms
│   ├── Request Interceptor (logging)
│   └── Response Interceptor (error handling)
│
└── API Functions
    ├── analyzeQuestion(data) → POST /analyze
    ├── getHealthStatus() → GET /health
    ├── getConfig() → GET /config
    ├── getHistory(params) → GET /history
    └── submitFeedback(data) → POST /feedback
```

## Styling Architecture

### Tailwind Configuration

```
tailwind.config.js
│
├── Content Paths
│   ├── ./index.html
│   └── ./src/**/*.{js,jsx}
│
└── Theme Extensions
    ├── Colors
    │   ├── primary (blue shades)
    │   ├── success (green shades)
    │   ├── warning (orange shades)
    │   └── error (red shades)
    │
    └── Fonts
        └── Inter (Google Fonts)
```

### CSS Layers

```
src/index.css
│
├── @tailwind base
│   └── body styles
│
├── @tailwind components
│   ├── .btn-primary
│   ├── .btn-secondary
│   ├── .input-field
│   ├── .card
│   ├── .card-header
│   └── .badge-* (success, warning, error, info)
│
└── @tailwind utilities
    ├── Custom scrollbar
    └── Animations
```

## Type System (JSDoc)

```
src/types/index.js
│
├── Core Types
│   ├── Insight
│   ├── TimeSeriesPoint
│   ├── PrimaryTrend
│   ├── Driver
│   └── DriverImpact
│
├── API Types
│   ├── AnalysisRequest
│   ├── AnalysisResponse
│   ├── HealthStatus
│   └── ApiError
│
└── Metadata Types
    └── AnalysisMetadata
```

## Build & Dev Flow

```
Development:
npm run dev
    ↓
Vite Dev Server (port 3000)
    ├── Hot Module Replacement (HMR)
    ├── Fast Refresh (React)
    ├── Proxy /api → http://localhost:8000
    └── Tailwind JIT compilation

Production:
npm run build
    ↓
Vite Build Process
    ├── Rollup bundling
    ├── Minification
    ├── Tree shaking
    ├── Code splitting
    └── dist/ folder
        ├── index.html
        └── assets/
            ├── index-[hash].js
            └── index-[hash].css
```

## Responsive Breakpoints

```
Tailwind Breakpoints:
├── sm:  640px  (small tablets)
├── md:  768px  (tablets)
├── lg:  1024px (small laptops)
├── xl:  1280px (laptops)
└── 2xl: 1536px (desktops)

Component Behavior:
├── Mobile (< 768px)
│   └── Single column layout
│
├── Tablet (768px - 1024px)
│   └── 2-column grid for insights
│
└── Desktop (> 1024px)
    └── Full-width charts, 2-column insights
```

## Error Handling Flow

```
API Error
    ↓
Axios Response Interceptor
    ↓
Enhanced Error Object
    ├── message (user-friendly)
    ├── response.data.error
    └── original error
    ↓
React Query Error State
    ↓
Component Error Display
    ├── Error icon
    ├── Error title
    └── Error message
```

## Performance Optimizations

1. **React Query Caching**
   - 5-minute stale time
   - Automatic background refetching
   - Deduplication of requests

2. **Code Splitting**
   - Dynamic imports (future)
   - Route-based splitting (future)

3. **Bundle Optimization**
   - Vite tree shaking
   - Minification
   - Gzip compression

4. **Chart Performance**
   - ResponsiveContainer for dynamic sizing
   - Limited data points display
   - Debounced resize events

## Security Considerations

1. **API Communication**
   - HTTPS in production
   - No sensitive data in localStorage
   - CORS configured on backend

2. **Input Validation**
   - Client-side length limits
   - XSS prevention (React auto-escaping)
   - No eval() or innerHTML

3. **Dependencies**
   - Regular npm audit
   - Known vulnerabilities patched
   - Minimal dependency footprint

## Extensibility Points

### Easy to Add:

1. **New Chart Type**
   - Create component in `src/components/`
   - Import Recharts chart type
   - Add to App.jsx results section

2. **New API Endpoint**
   - Add function to `src/services/api.js`
   - Create custom hook in `src/hooks/`
   - Use in component

3. **New Insight Type**
   - Update INSIGHT_TYPES in constants
   - Add icon case in InsightCard
   - Backend returns new type

4. **User Preferences**
   - Add localStorage utilities
   - Create preferences context
   - Implement settings UI

## Future Enhancements

- [ ] Authentication & user accounts
- [ ] Saved questions/favorites
- [ ] Export charts as images
- [ ] Dark mode toggle
- [ ] Advanced filtering
- [ ] Real-time updates (WebSocket)
- [ ] Collaborative features
- [ ] Custom dashboards
- [ ] A/B testing framework
- [ ] Analytics tracking
