# 7H Stock Analyzer - Lambda Specification

- lambda function that runs the stock analyzer runs on demand and on a cron schedule from event bridge
- lambda saves the recommendations to S3, that can be consumed by the frontend UI (S3 bucket is already created)
- lambda sends push notifications via pushover for significant recommendations
- lambda has a health check endpoint
- lambda has a run-now endpoint
- lambda has an endpoint to update watchlist, portfolio, us stocks, etfs, configurations,etc.,

- UI consumes the recommendations from S3 and displays them
- Recommendations are stored in S3 with a timestamp, with price and change percentage and target price and stop loss price
- UI can fetch recommendations from S3 and display them
- UI can trigger a manual run of the lambda function

## Recommendations 

- For Sell recommendations, provide a threshold price (stop loss)
    - include this for stocks with recommended buy or hold
- For Buy recommendations, provide a target price (current price + 10%)
- For Hold recommendations, provide a target price (current price)
- For Strong Buy recommendations, provide a target price (current price + 20%)
- For Strong Sell recommendations, provide a target price (current price - 20%)
- For the recommendations done, show the reason for the recommendation
- For the recommendations done, show the confidence level
- For the recommendations done, show the technical indicators used
- for the recommendations done, show the price chart

## Recon
- For the recommendations done, do a recon once a day on target price met or stop loss hit and # of days it took to reach there

## Purge
- For the recommendations done, purge the recommendations after 1000 days

## Scalability
- The lambda function should be able to handle multiple stocks at once
- The lambda function should be able to handle multiple recommendations at once
- The lambda function should be able to handle multiple technical indicators at once
- The lambda function should be able to handle multiple configurations at once
- The lambda function should be able to handle multiple watchlists at once
- The lambda function should be able to handle multiple portfolios at once
- The lambda function should be able to handle multiple us stocks at once
- The lambda function should be able to handle multiple etfs at once

## Security
- The lambda function should be secured with API keys
- The lambda function should be secured with IAM roles
- The lambda function should be secured with VPC
- The lambda function should be secured with environment variables
- The s3 bucket should be secured with bucket policies with super minimal permissions - for read and write
- The s3 bucket should be secured with IAM roles from lambda function
- The s3 bucket should be secured with encryption - without increasing the cost

# Logging

- The lambda function should log activities meaningfully without increasing the cost
- The lambda function should log all errors without increasing the cost
- The lambda function should log all warnings without increasing the cost
- The lambda function should log all info without increasing the cost

## Config data
- The config data should be stored in S3
- The config data should be updated via the UI
- The config data should be used by the lambda function