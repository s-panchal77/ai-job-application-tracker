# =====================================================
# Stage 1: Build React Application
# =====================================================

FROM node:20-alpine AS build

WORKDIR /app

# Copy package files first for better Docker layer caching
COPY package*.json ./

RUN npm install

# Copy application source code
COPY . .

# API URL used by Vite during build time
ARG VITE_API_BASE_URL=http://localhost:8000
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL

# Generate production build
RUN npm run build

# =====================================================
# Stage 2: Serve with Nginx
# =====================================================

FROM nginx:alpine

# Copy built React files from build stage
COPY --from=build /app/dist /usr/share/nginx/html

# Custom Nginx configuration for React Router support
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

# Run Nginx in foreground
CMD ["nginx", "-g", "daemon off;"]