# Twitter Agent Dashboard

A comprehensive web-based dashboard for monitoring and controlling your intelligent Twitter agent. Watch your agent at work, review its activity and progress, and gain insights into its performance in real-time.

## Features

### 📊 Real-Time Monitoring
- **Live Status Updates**: See current activity, progress, and system status
- **Activity Timeline**: Visualize scheduled activities throughout the day
- **Performance Metrics**: Track engagement rates, follower growth, and more
- **WebSocket Integration**: Real-time updates without page refresh

### 📈 Performance Analytics
- **Interactive Charts**: Visualize engagement trends and activity distribution
- **Performance Scores**: Track overall agent effectiveness
- **Historical Data**: Review past performance and trends
- **Optimization Insights**: Get recommendations for improvement

### 🎛️ Control Panel
- **Start/Stop Agent**: Control agent execution
- **Trigger Optimization**: Manually initiate strategy optimization
- **Schedule Overview**: Navigate through daily schedules
- **Activity Logs**: Monitor detailed agent activities

### 📱 Modern UI
- **Responsive Design**: Works on desktop, tablet, and mobile
- **Clean Interface**: Intuitive and user-friendly design
- **Dark/Light Themes**: Comfortable viewing in any environment
- **Notifications**: Real-time alerts and status updates

## Prerequisites

- Python 3.8 or higher
- MongoDB (local or remote instance)
- Modern web browser (Chrome, Firefox, Safari, Edge)

## Quick Start

### Option 1: Easy Launch (Recommended)

1. **Windows Users**: Double-click `run_dashboard.bat`
2. **Mac/Linux Users**: Run `python run_dashboard.py`

The script will automatically install dependencies and start the dashboard.

### Option 2: Manual Setup

1. **Install Dependencies**:
   ```bash
   pip install -r dashboard_requirements.txt
   ```

2. **Start the Dashboard**:
   ```bash
   python dashboard_app.py
   ```

3. **Open Your Browser**:
   Navigate to: `http://localhost:5000`

## Dashboard Overview

### Main Dashboard View

The dashboard is organized into several key sections:

#### 1. System Status Cards (Top Row)
- **Current Activity**: What the agent is currently doing
- **Next Activity**: What's scheduled next
- **Daily Progress**: Completion percentage for today
- **Performance Score**: Overall effectiveness rating

#### 2. Live Metrics Panel
- **Engagement Rate**: Real-time engagement metrics
- **Follower Growth**: New followers gained
- **Tweet Impressions**: Reach and visibility metrics
- **Interaction Quality**: Quality scores for engagements

#### 3. Activity Schedule Timeline
- **Daily View**: See all scheduled activities for the day
- **Status Indicators**: Visual status of each activity
- **Navigation**: Browse different dates
- **Progress Tracking**: See completion status

#### 4. Performance Charts
- **Engagement Trends**: Line chart showing engagement over time
- **Activity Distribution**: Pie chart of activity types
- **Historical Data**: Performance trends over days/weeks

#### 5. Strategy Information
- **Current Strategy**: Active strategy details
- **Activity Distribution**: How time is allocated
- **Optimal Times**: Best posting times identified
- **Recommendations**: Optimization suggestions

#### 6. Activity Logs
- **Recent Sessions**: Latest engagement sessions
- **Performance Analyses**: Daily analysis results
- **Real-time Updates**: Live activity logging

### Control Features

#### Agent Control
- **Start Agent**: Begin automated Twitter activities
- **Stop Agent**: Pause agent execution
- **Trigger Optimization**: Run strategy optimization

#### Data Management
- **Refresh Data**: Update all dashboard data
- **Clear Logs**: Reset activity logs
- **Navigate Dates**: Browse historical schedules

#### Real-time Updates
- **Auto-refresh**: Dashboard updates every 30 seconds
- **Manual Refresh**: Force immediate update
- **Live Notifications**: Toast messages for important events

## Configuration

### Database Connection

By default, the dashboard connects to MongoDB at `mongodb://localhost:27017/`. To use a different database:

1. Edit `dashboard_app.py`
2. Modify the `DatabaseManager` initialization:
   ```python
   self.db_manager = DatabaseManager(
       connection_string="your_mongodb_connection_string",
       database_name="your_database_name"
   )
   ```

### Dashboard Settings

Customize dashboard behavior by modifying these settings in `dashboard_app.py`:

```python
# Update frequency (seconds)
UPDATE_INTERVAL = 30

# Dashboard host and port
HOST = '0.0.0.0'  # Set to '127.0.0.1' for local-only access
PORT = 5000

# Debug mode
DEBUG = False  # Set to True for development
```

### Performance Optimization

For better performance with large datasets:

1. **Enable Database Indexing**: The dashboard automatically creates indexes
2. **Limit Historical Data**: Configure data retention in database settings
3. **Adjust Update Frequency**: Increase `UPDATE_INTERVAL` for less frequent updates

## Troubleshooting

### Common Issues

#### 1. Dashboard Won't Start
- **Check Python Version**: Ensure Python 3.8+ is installed
- **Install Dependencies**: Run `pip install -r dashboard_requirements.txt`
- **Port Already in Use**: Change port in `dashboard_app.py` or stop other services

#### 2. No Data Displayed
- **Database Connection**: Verify MongoDB is running and accessible
- **Agent Not Running**: Start the Twitter agent to generate data
- **Empty Database**: Run the agent for some time to populate data

#### 3. Real-time Updates Not Working
- **WebSocket Issues**: Check browser console for errors
- **Firewall/Proxy**: Ensure WebSocket connections are allowed
- **Browser Compatibility**: Use a modern browser with WebSocket support

#### 4. Performance Issues
- **Large Dataset**: Implement data pagination or archival
- **Browser Memory**: Refresh the page periodically
- **Database Performance**: Ensure MongoDB has adequate resources

### Debug Mode

Enable debug mode for troubleshooting:

1. Edit `dashboard_app.py`
2. Set `debug=True` in the `run()` method
3. Check console output for detailed error messages

### Logs

Dashboard logs are output to the console. For persistent logging:

```python
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('dashboard.log'),
        logging.StreamHandler()
    ]
)
```

## API Endpoints

The dashboard provides REST API endpoints for external integrations:

### Status Endpoints
- `GET /api/status` - Current system status
- `GET /api/schedule?date=YYYY-MM-DD` - Schedule for specific date
- `GET /api/performance?days=N` - Performance data for N days
- `GET /api/optimization` - Strategy and optimization data
- `GET /api/logs?limit=N` - Recent activity logs

### Control Endpoints
- `POST /api/control/start` - Start the agent
- `POST /api/control/stop` - Stop the agent
- `POST /api/control/optimize` - Trigger optimization

### Example Usage

```bash
# Get current status
curl http://localhost:5000/api/status

# Get today's schedule
curl http://localhost:5000/api/schedule?date=2024-01-01

# Start the agent
curl -X POST http://localhost:5000/api/control/start
```

## Security Considerations

### Production Deployment

When deploying in production:

1. **Change Secret Key**: Update `SECRET_KEY` in `dashboard_app.py`
2. **Use HTTPS**: Configure SSL/TLS certificates
3. **Restrict Access**: Use firewall rules or authentication
4. **Database Security**: Secure MongoDB with authentication
5. **Regular Updates**: Keep dependencies updated

### Access Control

The dashboard currently doesn't include authentication. For secure environments:

1. **Add Authentication**: Implement login system
2. **Use Reverse Proxy**: Deploy behind nginx/Apache with auth
3. **VPN Access**: Restrict access to VPN users only
4. **API Keys**: Secure API endpoints with authentication

## Customization

### Styling

The dashboard uses Tailwind CSS for styling. To customize:

### Adaptive Dashboard Widgets

The dashboard now supports an adaptive widget system to ensure columns are filled perfectly across desktop, tablet, and mobile.

- Widget classes
  - Use `widget widget-fixed` for panels that should keep their natural height.
  - Use `widget widget-fluid` for panels that should consume remaining column height.
- Auto-fit behavior
  - Fluid widgets fill remaining column space and auto-resize their text using CSS container queries and a per-widget scale variable.
  - A `ResizeObserver` computes `--widget-scale` to minimize overflow or empty space by gently shrinking/growing text inside each widget.
- Container queries and fluid typography
  - Typography scales with `clamp()` and container queries so narrow widgets automatically tighten spacing and font sizes.
  - The computed CSS variable `--widget-scale` is applied to key text sizes to fit content.

Markup examples:

Fluid widget that fills remaining column space (recommended to include a scrollable body for long content):
```html
<div class="bg-gray-800 glass-panel rounded-lg p-3 widget widget-fluid">
  <div class="card-body-scroll">
    <!-- content -->
  </div>
</div>
```

Fixed widget that keeps natural size:
```html
<div class="bg-gray-800 glass-panel rounded-lg p-3 widget widget-fixed">
  <!-- content -->
</div>
```

Guidelines:
- Prefer one or two `widget-fluid` panels per column to avoid excessive content compression.
- If a panel contains long lists or timelines, wrap the list in `.card-body-scroll` to allow internal scrolling while the panel itself fills the column.
- You can lock scaling by setting `style="--widget-scale: 1"` on a widget if needed.
- Columns stack vertically on narrow screens (≤ 1280px). Fluid widgets will fill available vertical space; container queries ensure readable typography automatically.

Developer notes:
- The adaptive logic observes each `.widget` and sets `--widget-scale` based on the ratio of container height to content height.
- The schedule renderer triggers a refresh of adaptive sizing after updates so the timeline fits responsively.

1. Edit `templates/dashboard.html` for layout changes
2. Modify `static/css/dashboard.css` for custom styles
3. Update color schemes by changing CSS variables

### Adding Features

To extend the dashboard:

1. **New API Endpoints**: Add routes in `dashboard_app.py`
2. **Frontend Components**: Add HTML/JavaScript in templates
3. **Real-time Data**: Use Socket.IO events for live updates
4. **Charts**: Integrate Chart.js for new visualizations

### Integration

The dashboard can be integrated with:

- **Slack**: Send notifications to Slack channels
- **Email**: Automated performance reports
- **External APIs**: Export data to analytics platforms
- **Mobile Apps**: Use API endpoints for mobile interfaces

## Support

### Documentation
- **Code Comments**: Detailed inline documentation
- **Type Hints**: Python type annotations throughout
- **API Documentation**: Built-in endpoint documentation

### Community
- **GitHub Issues**: Report bugs and feature requests
- **Discussions**: Community support and questions
- **Contributions**: Pull requests welcome

### Professional Support
For enterprise deployments or custom development, consider:
- **Custom Features**: Tailored functionality development
- **Performance Optimization**: Large-scale deployment optimization
- **Training**: Team training on dashboard usage and customization

## License

This dashboard is part of the Intelligent Twitter Agent project. See the main project license for terms and conditions.

---

## Getting Started Checklist

- [ ] Python 3.8+ installed
- [ ] MongoDB running
- [ ] Dependencies installed (`pip install -r dashboard_requirements.txt`)
- [ ] Dashboard started (`python run_dashboard.py`)
- [ ] Browser opened to `http://localhost:5000`
- [ ] Twitter agent running (to see data)

**🎉 Enjoy monitoring your intelligent Twitter agent!**
