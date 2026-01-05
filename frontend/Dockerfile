FROM node:20-alpine
WORKDIR /app
RUN npm i -g pnpm
EXPOSE 5173
CMD ["sh", "-c", "pnpm install && pnpm dev --host 0.0.0.0 --port 5173"]
