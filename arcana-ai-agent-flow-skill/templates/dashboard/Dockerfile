# Arcana Workflow Monitor — multi-stage build (Angular 21 → nginx).
# Uses `npm install` (not `npm ci`) so platform-specific optional native deps
# (lightningcss / esbuild / @emnapi for linux-musl) resolve inside the image.
FROM node:24-alpine AS builder
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm install --no-audit --no-fund
COPY . .
RUN npx ng build --configuration=production

FROM nginx:1.27-alpine
COPY --from=builder /app/dist/arcana-angular/browser /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
