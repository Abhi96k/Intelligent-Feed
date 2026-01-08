# Get Started with Intelligent Feed Frontend

Welcome! This guide will get you up and running in under 5 minutes.

## Prerequisites Check

Before starting, ensure you have:
- ✅ Node.js 16+ installed (`node --version`)
- ✅ npm installed (`npm --version`)
- ✅ Backend API running on http://localhost:8000

## Option 1: Automated Setup (Recommended)

Run the setup script:

```bash
cd /Users/abhishek/Desktop/Hackthon/frontend
./setup.sh
```

This will:
1. Check Node.js version
2. Verify backend connectivity
3. Install all dependencies
4. Create environment file
5. Show next steps

## Option 2: Manual Setup

### Step 1: Install Dependencies

```bash
cd /Users/abhishek/Desktop/Hackthon/frontend
npm install
```

This installs:
- React 18.2.0
- Vite 5.0.11
- Tailwind CSS 3.4.1
- Recharts 2.10.3
- React Query 5.17.19
- Axios 1.6.5

### Step 2: Start Development Server

```bash
npm run dev
```

Output should show:
```
  VITE v5.0.11  ready in 500 ms

  ➜  Local:   http://localhost:3000/
  ➜  Network: use --host to expose
```

### Step 3: Open in Browser

Navigate to: http://localhost:3000

## What You'll See

1. **Header**: "Intelligent Feed" with status indicator
2. **Question Input**: Text area with example questions
3. **Empty State**: Prompt to enter a question

## Try It Out

### Example 1: Simple Question

1. Click on example question: "Why did revenue drop in Q3?"
2. Click "Run Analysis"
3. Wait for results (loading spinner appears)
4. View:
   - Triggered insights with confidence scores
   - Line chart showing revenue trend
   - Bar chart showing driver impacts
   - Summary text

### Example 2: Custom Question

1. Type your own question:
   ```
   What are the main drivers of customer churn?
   ```
2. Click "Run Analysis"
3. Explore the results

### Example 3: Clear and Retry

1. Click "Clear" button
2. Try another example question
3. Compare results

## Project Structure Quick Reference

```
frontend/
├── src/
│   ├── components/        # React UI components
│   ├── services/api.js    # Backend API client
│   ├── App.jsx           # Main application
│   └── main.jsx          # Entry point
├── package.json          # Dependencies
└── vite.config.js        # Build configuration
```

## Available Commands

```bash
npm run dev      # Start development server (port 3000)
npm run build    # Build for production
npm run preview  # Preview production build
npm run lint     # Check code quality
```

## Troubleshooting

### "Cannot connect to backend"

**Problem**: Frontend can't reach the backend API

**Solution**:
```bash
# Check if backend is running
curl http://localhost:8000/health

# Should return: {"status": "healthy"}
```

If not running, start your backend first.

### "Port 3000 already in use"

**Problem**: Another app is using port 3000

**Solution**: Edit `vite.config.js`:
```javascript
server: {
  port: 3001,  // Change to any available port
}
```

### "Module not found" errors

**Problem**: Dependencies not installed properly

**Solution**:
```bash
rm -rf node_modules package-lock.json
npm install
```

### Charts not displaying

**Problem**: Data format mismatch

**Solution**: Check `SAMPLE_RESPONSE.json` for expected format

## Understanding the UI

### Question Input Area
- **Text Area**: Enter your analytics question
- **Character Counter**: Shows input length
- **Example Questions**: Click to auto-fill
- **Run Button**: Submit for analysis
- **Clear Button**: Reset the form

### Results Display

#### Insight Cards
- **Green Border**: Insight triggered (relevant to question)
- **Gray Border**: Insight not triggered
- **Badge**: Shows triggered status
- **Confidence**: Percentage (0-100%)
- **Metadata**: Additional context

#### Trend Chart
- **Line Graph**: Time series visualization
- **Trend Arrow**: Up/down/stable indicator
- **Percentage**: Overall change
- **Hover**: See exact values

#### Driver Impact Chart
- **Horizontal Bars**: Impact magnitude
- **Green Bars**: Positive impact
- **Red Bars**: Negative impact
- **Blue Bars**: Primary driver

#### Summary Section
- **Text**: Natural language summary
- **Metadata**: Analysis details

## Next Steps

### 1. Explore the Code

Start with these files:
- `src/App.jsx` - Main application logic
- `src/components/QuestionInput.jsx` - Input component
- `src/services/api.js` - API integration

### 2. Customize the UI

- **Colors**: Edit `tailwind.config.js`
- **Examples**: Modify example questions in `QuestionInput.jsx`
- **Layout**: Adjust grid in `App.jsx`

### 3. Add Features

Ideas to extend:
- Save favorite questions
- Export charts as images
- Add more chart types
- Implement user preferences

### 4. Read Documentation

- `README.md` - Project overview
- `DEVELOPMENT.md` - Development guide
- `ARCHITECTURE.md` - System architecture
- `SAMPLE_RESPONSE.json` - API format

## Common Workflows

### Making UI Changes

1. Edit component in `src/components/`
2. Save file
3. Browser auto-refreshes (HMR)
4. See changes immediately

### Testing Different Data

1. Modify backend response format
2. Restart frontend dev server
3. Run analysis
4. Verify display

### Adding New Component

1. Create `src/components/MyComponent.jsx`
2. Add JSDoc comments
3. Import in `App.jsx`
4. Use in JSX: `<MyComponent />`

## Tips for Success

1. **Keep Backend Running**: Frontend needs backend for API calls
2. **Check Browser Console**: Errors appear here first
3. **Use React DevTools**: Install browser extension
4. **Read JSDoc Comments**: All props are documented
5. **Start Simple**: Modify existing before creating new

## Getting Help

If stuck, check:
1. Browser console for errors
2. Network tab for API calls
3. `SAMPLE_RESPONSE.json` for expected format
4. Component source code (well-documented)
5. `DEVELOPMENT.md` for advanced topics

## Production Deployment

When ready to deploy:

```bash
# Build optimized version
npm run build

# Test production build
npm run preview

# Deploy dist/ folder to:
# - Vercel
# - Netlify
# - Your hosting provider
```

## Key Features Checklist

Try these features:
- [ ] Submit a question
- [ ] View triggered insights
- [ ] Hover over chart data points
- [ ] Click example questions
- [ ] Use Clear button
- [ ] View different insight types
- [ ] Check metadata section
- [ ] Test on mobile/tablet
- [ ] Try different questions

## Performance Notes

- **First Load**: ~500ms (Vite is fast!)
- **HMR Updates**: < 100ms
- **API Response**: Depends on backend
- **Chart Rendering**: < 200ms

## Browser Support

Tested on:
- ✅ Chrome 120+
- ✅ Firefox 120+
- ✅ Safari 17+
- ✅ Edge 120+

## Development Environment

Recommended setup:
- **Editor**: VS Code
- **Extensions**: ESLint, Tailwind CSS IntelliSense
- **Terminal**: iTerm2 or VS Code integrated
- **Browser**: Chrome with React DevTools

## Success Indicators

You're ready when:
- ✅ `npm run dev` starts without errors
- ✅ Browser shows Intelligent Feed UI
- ✅ Can submit questions successfully
- ✅ Charts display properly
- ✅ No console errors

## What's Included

This frontend provides:
- ✅ Modern React 18 with hooks
- ✅ Vite for fast development
- ✅ Tailwind for beautiful UI
- ✅ Recharts for visualizations
- ✅ React Query for data fetching
- ✅ Responsive design
- ✅ Error handling
- ✅ Loading states
- ✅ Type safety (JSDoc)
- ✅ Comprehensive documentation

## Ready to Code!

You now have everything you need to:
1. Run the frontend
2. Submit questions
3. View insights and charts
4. Customize the UI
5. Extend functionality

Happy coding! 🚀

---

**Quick Links:**
- [README](README.md) - Project overview
- [Quick Start](QUICKSTART.md) - 3-step setup
- [Development](DEVELOPMENT.md) - Full dev guide
- [Architecture](ARCHITECTURE.md) - System design

**Need Help?**
Check the documentation or review the well-commented source code!
