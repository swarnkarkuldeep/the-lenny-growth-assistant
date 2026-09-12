FROM node:18-alpine

WORKDIR /app

COPY package.json .

RUN npm install --legacy-peer-deps 2>/dev/null || true

EXPOSE 5173

CMD ["npm", "run", "dev"]
