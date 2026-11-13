# RepoMind Frontend Dockerfile
FROM node:20-alpine

# Set working directory
WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci

# Copy application code
COPY . .

# Build the application
RUN npm run build

# Expose port
EXPOSE 5173

# Run the preview server (for production)
CMD ["npm", "run", "preview", "--", "--host", "0.0.0.0", "--port", "5173"]