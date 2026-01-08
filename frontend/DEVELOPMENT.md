# Development Guide

Comprehensive guide for developing and extending the Intelligent Feed frontend.

## Table of Contents

1. [Setup](#setup)
2. [Project Architecture](#project-architecture)
3. [Component Development](#component-development)
4. [API Integration](#api-integration)
5. [Styling Guide](#styling-guide)
6. [Best Practices](#best-practices)
7. [Testing](#testing)
8. [Deployment](#deployment)

## Setup

### Prerequisites

- Node.js 16+ (recommended: 18+)
- npm or yarn
- Git
- VS Code (recommended) with extensions:
  - ESLint
  - Prettier
  - Tailwind CSS IntelliSense

### Initial Setup

```bash
# Clone or navigate to the project
cd /Users/abhishek/Desktop/Hackthon/frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

### Environment Variables

Create `.env.local` for environment-specific settings (optional):

```env
VITE_API_BASE_URL=http://localhost:8000
VITE_API_TIMEOUT=30000
VITE_ENABLE_DEBUG=true
```

## Project Architecture

### Directory Structure

```
frontend/
├── public/                 # Static assets
│   └── vite.svg           # App icon
├── src/
│   ├── components/        # React components
│   │   ├── QuestionInput.jsx
│   │   ├── InsightCard.jsx
│   │   ├── TrendChart.jsx
│   │   └── DriverImpactChart.jsx
│   ├── hooks/             # Custom React hooks
│   │   └── useAnalysis.js
│   ├── services/          # API services
│   │   └── api.js
│   ├── types/             # Type definitions
│   │   └── index.js
│   ├── utils/             # Utility functions
│   │   ├── constants.js
│   │   └── formatters.js
│   ├── App.jsx            # Main app component
│   ├── main.jsx           # Entry point
│   └── index.css          # Global styles
├── index.html             # HTML template
├── package.json           # Dependencies
├── vite.config.js         # Vite configuration
├── tailwind.config.js     # Tailwind configuration
└── postcss.config.js      # PostCSS configuration
```

### Technology Stack

- **React 18**: UI framework with hooks and functional components
- **Vite**: Build tool and dev server (faster than CRA)
- **Tailwind CSS**: Utility-first CSS framework
- **Recharts**: Chart library (lightweight, composable)
- **React Query**: Server state management
- **Axios**: HTTP client

## Component Development

### Creating a New Component

1. Create file in `src/components/`:

```jsx
/**
 * MyComponent - Brief description
 *
 * @param {Object} props
 * @param {string} props.title - Component title
 */
function MyComponent({ title }) {
  return (
    <div className="card">
      <h3 className="card-header">{title}</h3>
    </div>
  )
}

export default MyComponent
```

2. Add JSDoc comments for props
3. Use Tailwind utility classes
4. Follow functional component patterns

### Component Guidelines

- **Naming**: PascalCase for components (e.g., `QuestionInput`)
- **File Structure**: One component per file
- **Props**: Use destructuring and default values
- **State**: Use `useState` and `useEffect` hooks
- **Styling**: Tailwind classes, avoid inline styles

### Example: Creating a Chart Component

```jsx
import { LineChart, Line, XAxis, YAxis } from 'recharts'

function CustomChart({ data, metric }) {
  return (
    <div className="card">
      <h3 className="card-header">{metric}</h3>
      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={data}>
          <XAxis dataKey="date" />
          <YAxis />
          <Line dataKey="value" stroke="#3b82f6" />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}
```

## API Integration

### Adding a New Endpoint

1. Define the API function in `src/services/api.js`:

```javascript
export const getInsightDetails = async (insightId) => {
  const response = await apiClient.get(`/insights/${insightId}`)
  return response.data
}
```

2. Add type definition in `src/types/index.js`:

```javascript
/**
 * @typedef {Object} InsightDetails
 * @property {string} id
 * @property {string} title
 * @property {Object} data
 */
```

3. Create a custom hook in `src/hooks/`:

```javascript
import { useQuery } from '@tanstack/react-query'
import { getInsightDetails } from '../services/api'

export function useInsightDetails(insightId) {
  return useQuery({
    queryKey: ['insight', insightId],
    queryFn: () => getInsightDetails(insightId),
    enabled: !!insightId,
  })
}
```

4. Use in component:

```jsx
import { useInsightDetails } from '../hooks/useInsightDetails'

function InsightDetailsView({ insightId }) {
  const { data, isLoading, error } = useInsightDetails(insightId)

  if (isLoading) return <div>Loading...</div>
  if (error) return <div>Error: {error.message}</div>

  return <div>{data.title}</div>
}
```

### API Response Format

Expected response format (see `SAMPLE_RESPONSE.json`):

```json
{
  "question": "...",
  "insights": [...],
  "primary_trend": {...},
  "driver_impact": {...},
  "summary": "...",
  "metadata": {...}
}
```

## Styling Guide

### Tailwind Utilities

Common patterns used in this project:

```jsx
// Card container
<div className="card">

// Card header
<h3 className="card-header">

// Primary button
<button className="btn-primary">

// Secondary button
<button className="btn-secondary">

// Input field
<input className="input-field" />

// Badges
<span className="badge badge-success">
<span className="badge badge-warning">
```

### Custom Colors

Defined in `tailwind.config.js`:

- `primary-*`: Blue shades (main brand color)
- `success-*`: Green shades (positive states)
- `warning-*`: Orange shades (warnings)
- `error-*`: Red shades (errors)

### Responsive Design

Use Tailwind responsive prefixes:

```jsx
<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3">
  {/* Responsive grid */}
</div>
```

## Best Practices

### Code Style

1. **Use functional components** with hooks
2. **Destructure props** at function signature
3. **Add JSDoc comments** for all components
4. **Handle loading and error states**
5. **Keep components focused** (single responsibility)

### State Management

- **Local state**: `useState` for component-specific state
- **Server state**: React Query for API data
- **Global state**: Context API (if needed)

### Performance

- Use `React.memo()` for expensive components
- Implement proper `key` props in lists
- Avoid inline function definitions in JSX
- Use `useMemo` and `useCallback` when appropriate

### Error Handling

Always handle errors gracefully:

```jsx
function MyComponent() {
  const { data, error, isLoading } = useQuery(...)

  if (isLoading) return <LoadingSpinner />
  if (error) return <ErrorMessage error={error} />
  if (!data) return <EmptyState />

  return <DataView data={data} />
}
```

## Testing

### Unit Testing (Future)

Setup with Vitest:

```bash
npm install -D vitest @testing-library/react @testing-library/jest-dom
```

Example test:

```javascript
import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import QuestionInput from './QuestionInput'

describe('QuestionInput', () => {
  it('renders input field', () => {
    render(<QuestionInput />)
    expect(screen.getByPlaceholderText(/ask a question/i)).toBeInTheDocument()
  })
})
```

### Manual Testing Checklist

- [ ] Question submission works
- [ ] Loading states display correctly
- [ ] Error messages are clear
- [ ] Charts render with data
- [ ] Responsive on mobile
- [ ] Keyboard navigation works
- [ ] All example questions work

## Deployment

### Build for Production

```bash
# Create optimized build
npm run build

# Preview production build locally
npm run preview
```

### Build Output

Files are generated in `dist/`:
- `index.html` - Entry HTML
- `assets/` - JS, CSS, and images

### Deployment Platforms

#### Vercel

```bash
npm install -g vercel
vercel
```

#### Netlify

```bash
npm install -g netlify-cli
netlify deploy --prod
```

#### Docker

Create `Dockerfile`:

```dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build
RUN npm install -g serve
EXPOSE 3000
CMD ["serve", "-s", "dist", "-l", "3000"]
```

Build and run:

```bash
docker build -t intelligent-feed .
docker run -p 3000:3000 intelligent-feed
```

### Environment Configuration

For production, ensure:
1. API proxy points to production backend
2. CORS is configured on backend
3. Environment variables are set
4. SSL/HTTPS is enabled

## Debugging

### Common Issues

**Issue**: "Cannot connect to backend"
- Check backend is running on port 8000
- Verify proxy configuration in `vite.config.js`
- Check browser console for CORS errors

**Issue**: "Module not found"
- Run `npm install`
- Check import paths (case-sensitive)
- Clear node_modules and reinstall

**Issue**: Charts not rendering
- Verify data format matches expected structure
- Check browser console for Recharts errors
- Ensure ResponsiveContainer has parent with height

### Debug Tools

1. **React DevTools**: Install browser extension
2. **React Query DevTools**: Already configured
3. **Network Tab**: Monitor API calls
4. **Console Logs**: Check API interceptor logs

## Contributing

### Code Review Checklist

- [ ] Code follows style guide
- [ ] Components have JSDoc comments
- [ ] No console.log statements (except debug)
- [ ] Error handling is implemented
- [ ] Responsive design tested
- [ ] Accessibility considered (ARIA labels, keyboard nav)
- [ ] No hardcoded values (use constants)

### Git Workflow

```bash
# Create feature branch
git checkout -b feature/my-feature

# Make changes and commit
git add .
git commit -m "feat: add new feature"

# Push and create PR
git push origin feature/my-feature
```

## Resources

- [React Documentation](https://react.dev)
- [Vite Documentation](https://vitejs.dev)
- [Tailwind CSS Documentation](https://tailwindcss.com)
- [Recharts Documentation](https://recharts.org)
- [React Query Documentation](https://tanstack.com/query)

## Support

For questions or issues:
1. Check this guide and README.md
2. Review component source code (well-documented)
3. Check browser console for errors
4. Review `SAMPLE_RESPONSE.json` for API format
