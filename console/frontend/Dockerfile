# syntax=docker/dockerfile:1
FROM node:20-alpine AS build

WORKDIR /app

# Accept build-time env vars
ARG VITE_API_URL
ARG VITE_DEMO_MODE=false
ENV VITE_API_URL=$VITE_API_URL
ENV VITE_DEMO_MODE=$VITE_DEMO_MODE

COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

# ── Production stage ────────────────────────────────────────────────────────
FROM nginx:1.25-alpine

COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 8080
CMD ["nginx", "-g", "daemon off;"]
