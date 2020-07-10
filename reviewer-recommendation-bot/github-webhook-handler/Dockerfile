FROM node:12.1.0
COPY . github-webhook-handler
RUN cd github-webhook-handler && npm install
CMD cd github-webhook-handler && npm start