# Use Node 20+
FROM node:20

WORKDIR /app

# Copy source code
COPY . ./

# Install dependencies
RUN npm install

# Build TypeScript
RUN npm run build

# Expose port
EXPOSE 8080

# Start the application
CMD ["npm", "start"]
