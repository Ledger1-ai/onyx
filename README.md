# BasaltOnyx
>
> **Formerly Project Anubis**

**Autonomous Social Intelligence Platform**

BasaltOnyx is a next-generation social automation platform designed for scale, security, and multi-user collaboration. It replaces the legacy Python-based "Anubis" bot with a unified, high-performance Node.js architecture.

![System Status](https://img.shields.io/badge/System-Online-green) ![Version](https://img.shields.io/badge/Version-2.0-blue)

## 🚀 Key Features

### 🏛️ Multi-Tenant Architecture

- **Team Isolation**: Data and configurations are scoped to Teams.
- **RBAC**: Granular Role-Based Access Control (Super Admin, Admin, Analyst, Operative).
- **User Management**: Create, edit, and manage users via a centralized dashboard.

### � Security & Privacy

- **Browser Isolation**: Each user gets a dedicated, persistent browser profile (cookies/sessions) on the server. Your Twitter session is completely isolated from other users.
- **Gateway Authentication**: Secure login portal (`/underworld/gateway`) with session management.
- **Audit Logging**: Comprehensive activity logs for all actions.

### 🤖 Intelligent Automation

- **Integrated Worker**: No more separate Python scripts. The background worker is integrated directly into the application.
- **Smart Scheduling**: Automated task distribution.
- **Platform Support**:
  - **Twitter (X)**: Full browser automation (Posting, Replying, Following).
  - **LinkedIn**: Browser automation for professional networking.
  - **Meta (FB/IG)**: API-based integration.

## 🛠️ Tech Stack

- **Frontend**: Next.js 14+ (App Router), TailwindCSS, Framer Motion.
- **Backend**: Next.js API Routes + Integrated Express Server.
- **Database**: MongoDB (Mongoose ODM).
- **Deployment**: Optimized for Azure App Service + Cosmos DB.

## 📦 Installation & Setup

### Prerequisites

- Node.js 18+
- MongoDB (Local or Atlas/CosmosDB)

### 1. Clone & Install

```bash
git clone <repo>
cd onyx/frontend
npm install
```

### 2. Configure Environment

Create a `.env` file in the `frontend` directory:

```env
# Database
MONGODB_URI=mongodb://localhost:27017/onyx

# Security
AUTH_SECRET=your_super_secret_key_here

# System
NODE_ENV=development
```

### 3. Run Locally

```bash
npm run dev
```

Visit `http://localhost:3000` to access the platform.

### 4. Access the Underworld

- Navigate to `/underworld/gateway` (or click "INITIALIZE SYSTEM" on the landing page).
- **Default Login**: Use the credentials provided by your system administrator.

## 📂 Project Structure

- `src/app`: Next.js App Router pages (Frontend).
- `src/app/api`: Backend API endpoints.
- `src/worker`: Background automation logic (Scrapers, Processors).
- `src/models`: Mongoose database schemas.
- `src/components`: Reusable UI components.

## 🛡️ "Protocol Mythos" (Afterlife Mode)

The platform includes a "System Safe" / "Afterlife" toggle for emergency shutdown or mode switching. This is controlled via the dashboard header toggles.

---
**BasaltOnyx v2.0** | Built for the Traversing the Underworld.
