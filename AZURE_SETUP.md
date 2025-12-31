# Azure Database Setup Guide (MongoDB Only)

Since we refactored the application, you **NO LONGER** need Redis. You only need **Azure Cosmos DB**.

## 1. Create Azure Cosmos DB for MongoDB

1. Log in to the [Azure Portal](https://portal.azure.com).
2. In the search bar, type **Azure Cosmos DB** and select it.
3. Click **+ Create**.
4. **CRITICAL STEP**: You will see several tiles.
    * Find **Azure Cosmos DB for MongoDB**.
    * You will likely see two sub-options: "vCore cluster" and "Request Unit (RU)".
    * **Select: vCore cluster** (Recommended).
        * *Why?* It offers full MongoDB compatibility (better for Mongoose) and has a permanent Free Tier.
5. **Basics Tab Configuration**:
    * **Subscription**: Select yours.
    * **Resource Group**: Select existing (e.g., `onyx-rg`) or create new.
    * **Cluster Name**: e.g., `onyx-mongo`.
    * **Region**: Same as your App Service (e.g., East US).
    * **Tier / Size**: Look for a checkbox or dropdown that says **"Free/Trial"** or select the smallest tier (**High Performance** not needed).
        * *Note*: If "Free Tier" isn't explicitly shown on the vCore creation page, check the "Request Unit" option instead.
        * **Alternative (Safe Bet for Free Tier)**: If you are unsure, go back and select **Request Unit (RU)**.
            * Select **Capacity mode**: "Provisioned throughput".
            * Check **"Apply Free Tier Discount"** (1000 RU/s free).
            * This is the classic "Free Forever" option.
6. **Networking**:
    * Select **"Allow public access from Azure services"**. This is required for your App Service to connect.
7. **Security**:
    * Create a **Username** (e.g., `onyxadmin`) and **Password**. **WRITE THESE DOWN.**
8. Click **Review + create**, then **Create**. (Takes ~5-10 mins).

## 2. Get Connection String

1. Once created, go to the resource.
2. On the left menu, select **Connection strings** (or "Settings" > "Connection strings").
3. Copy the **PRIMARY CONNECTION STRING**.
    * It looks like: `mongodb+srv://<user>:<password>@<host>...`

## 3. Configure App Service

1. Go to your **App Service**.
2. **Settings** > **Environment variables**.
3. Add/Update:
    * `MONGODB_URI`: Paste the connection string.
        * **Important**: If the string has `<password>`, replace it with your actual password.
    * `NODE_ENV`: `production`
4. **Delete** the `REDIS_URL` variable if it exists (no longer needed).
5. **Save** and **Restart** the app.

## 4. Verify

1. Go to your deployed site.
2. Open the **Log Stream** in Azure.
3. You should see: `✅ Connected to MongoDB`.
