# Lex Bot Interaction Lambda Function

This repository contains an AWS Lambda function designed to handle interactions with an Amazon Lex bot. The function provides a multi-step interaction flow by delegating actions between dialog hooks and fulfillment hooks. It also integrates with AWS Kendra for document retrieval and uses a hosted Large Language Model (LLM) server for generating dynamic, context-aware responses.

## Features

- **Amazon Lex Integration**: The Lambda function processes Lex bot requests, determining whether the interaction is at the dialog or fulfillment stage.
- **Amazon Kendra Integration**: The function queries an Amazon Kendra index to retrieve relevant information to fulfill user intents.
- **LLM Interaction**: A hosted LLM server (using OpenAI) is leveraged to generate human-like responses for complex user queries.
- **Slot Validation**: Custom logic for slot validation and elicit prompts.
- **Support for Multiple Intents**: The function supports various intents like Outlook delegate access setup, laptop password reset, and phone setup, with more intents easily configurable.
- **Fallback Handling**: Provides a fallback mechanism to guide users through additional steps if the initial interaction fails.

## Prerequisites

- **Amazon Lex Bot**: A configured Lex bot with the necessary intents and slots.
- **Amazon Kendra**: A Kendra index set up to handle document queries.
- **LLM Server**: A hosted LLM server for generating responses.

## Setup

### AWS Resources

1. **Amazon Lex**: Ensure that your Lex bot is configured with the necessary intents and slots. Example intents included:
   - `OutlookDelegateAccess`
   - `ResetLaptopPassword`
   - `SetupPhone`
   - `FallbackIntent`

2. **Amazon Kendra**: 
   - Replace the placeholder value for `KENDRA_INDEX_ID` with your actual Kendra index ID.

3. **LLM Server**: 
   - Define the public DNS of your hosted LLM server in the `LLM_Server_Public_IPv4_DNS` constant in the code. This server should be capable of processing LLM requests.
   - You need to specify the model you are using in the `query_llm()` function (e.g., `hugging-quants/Meta-Llama-3.1-8B-Instruct-AWQ-INT4`).

### AWS Lambda Deployment

1. Zip the Python file and dependencies, and upload it to your AWS Lambda function.
2. Attach the necessary IAM roles and policies to allow the Lambda function to access Amazon Lex, Kendra, and your hosted LLM service.
3. Configure the function to trigger on Lex bot events.

## Function Overview

### `lambda_handler(event, context)`
This is the main entry point. The handler inspects the event payload from the Lex bot, checking whether it's in the dialog phase (`DialogCodeHook`) or fulfillment phase (`FulfillmentCodeHook`).

### Dialog and Fulfillment Logic
The Lambda function provides two distinct phases:

- **Dialog Phase**: Handled by `handle_dialog_code_hook()`. This phase is responsible for managing slots, validating them, and determining whether more information is required from the user.
- **Fulfillment Phase**: Handled by `handle_fulfillment_code_hook()`. This phase completes the user's request by querying Amazon Kendra and generating a response using an LLM.

### Intents
The function supports several intents:

1. **OutlookDelegateAccess**: Helps users set up delegate access in Outlook.
2. **ResetLaptopPassword**: Assists with resetting laptop passwords.
3. **SetupPhone**: Guides users through various phone setup tasks.
4. **FallbackIntent**: A fallback mechanism for incomplete or unrecognized user requests.

### Key Helper Functions

- **`query_kendra()`**: Queries the Amazon Kendra index for documents relevant to the user's query.
- **`query_llm()`**: Sends requests to the LLM server to generate responses for user intents.
- **`handle_fallback_intent()`**: Provides guidance if a fallback scenario occurs during interaction.

### Response Structure
Responses returned to Lex include text responses generated by the LLM, and they are broken down into manageable chunks (each containing no more than 100 words) to ensure smooth interaction with the Lex bot.

## Customization

### Adding New Intents
1. Define the new intent in the Lex bot.
2. Add a case for the new intent in the `fulfill_intent()` function.
3. Customize the response generation, slot validation, and Kendra queries for the new intent.

### Slot Validation
You can modify the `validate_slots()` function to add custom validation logic for each intent.

### LLM Integration
The LLM server integration can be customized based on your specific model and requirements. The system message defines the role and behavior of the LLM, which can be tailored per intent.


By following this guide, you will be able to handle interactions between an Amazon Lex bot, Amazon Kendra, and a hosted LLM, creating a robust conversational experience for your users.
