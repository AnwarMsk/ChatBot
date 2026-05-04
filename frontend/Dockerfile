# Stage 1: Build the Angular application
FROM node:20-alpine AS builder

WORKDIR /app

# Copy package.json and package-lock.json
COPY package*.json ./

# Install dependencies
RUN npm ci

# Copy the rest of the application code
COPY . .

# Build the application
RUN npm run build --configuration=production

# Prepare the final distribution folder to handle both application builder outputs and legacy outputs
RUN mkdir -p /app/dist-final && \
    (cp -R /app/dist/emi-chatbot/browser/* /app/dist-final/ 2>/dev/null || cp -R /app/dist/emi-chatbot/* /app/dist-final/)

# Stage 2: Serve the application with Nginx
FROM nginx:alpine

# Remove default nginx website
RUN rm -rf /usr/share/nginx/html/*

# Copy the build output
COPY --from=builder /app/dist-final /usr/share/nginx/html

# Add custom Nginx configuration to support Angular routing (fallback to index.html)
RUN echo 'server { \
    listen 80; \
    server_name localhost; \
    location / { \
        root /usr/share/nginx/html; \
        index index.html index.htm; \
        try_files $uri $uri/ /index.html; \
    } \
}' > /etc/nginx/conf.d/default.conf

# Expose port 80
EXPOSE 80

# Start Nginx server
CMD ["nginx", "-g", "daemon off;"]