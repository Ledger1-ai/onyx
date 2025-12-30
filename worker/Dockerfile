FROM mcr.microsoft.com/playwright:v1.49.1-jammy

# Ensure node 20+
RUN apt-get update && apt-get install -y curl && \
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y nodejs

WORKDIR /app

COPY package*.json ./

RUN npm install

COPY . .

# Compile TS (or run with ts-node in dev)
# For prod we usually build, but for simplicity in this setup we'll use ts-node or build step
RUN npm run build

CMD ["npm", "start"]
