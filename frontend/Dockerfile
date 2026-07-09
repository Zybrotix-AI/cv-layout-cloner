FROM node:20-slim AS dev

WORKDIR /app

COPY package.json package-lock.json* ./
RUN npm install

COPY . .

EXPOSE 1111

CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "1111"]
