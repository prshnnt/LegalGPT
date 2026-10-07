# Stage 1: Build Svelte/Vite application
FROM node:20-alpine AS builder

WORKDIR /app

# Copy dependency manifests
COPY package.json package-lock.json ./

# Install dependencies cleanly
RUN npm ci

# Copy application source
COPY . .

# Optional build-time argument for API base URL
ARG VITE_API_BASE_URL
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}

# Build for production
RUN npm run build

# Stage 2: Serve static assets with Nginx
FROM nginx:alpine

# Copy built distribution from builder
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy custom Nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose HTTP port
EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD wget -qO- http://localhost/ || exit 1

# Start Nginx
CMD ["nginx", "-g", "daemon off;"]
