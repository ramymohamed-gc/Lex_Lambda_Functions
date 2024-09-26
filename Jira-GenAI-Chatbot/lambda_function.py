import json
import boto3
from openai import OpenAI
import os

# Define the public DNS of your LLM server
LLM_Server_Public_IP=os.getenv('LLM_Server_Public_IP') 

# Kendra settings

    
def lambda_handler(event, context):
    # print("Event:")
    # print(event)  
          
    # Determine if this is a DialogCodeHook or FulfillmentCodeHook
    invocation_source = event['invocationSource']
    
    if invocation_source == 'DialogCodeHook':
        response = handle_dialog_code_hook(event)
    elif invocation_source == 'FulfillmentCodeHook':
        response = handle_fulfillment_code_hook(event)
    
    # print("Response:")
    # print(response)
    return response

def handle_dialog_code_hook(event):
    # Extract the intent and slots
    intent_name = event['sessionState']['intent']['name']
    slots = event['sessionState']['intent']['slots']  
    session_attributes=event['sessionState']['sessionAttributes']
    # Set a flag in session attributes to indicate that we are in the middle of a fallback flow
    
    if intent_name == 'FallbackIntent':
        
        #TODO: Modify this part (fallback_in_progress when it is not there)
        if 'fallback_in_progress' in session_attributes and session_attributes['fallback_in_progress'] == 'true':
            session_attributes['fallback_in_progress'] = 'false'
            
        if session_attributes['fallback_in_progress'] == 'true':
            session_attributes['fallback_in_progress'] = 'false'
            fallback_result = handle_fallback_intent(event)    
            # Return the fulfillment result
            return close(
                session_attributes, intent_name, slots, 'InProgress', 'ElicitIntent', {'contentType': 'PlainText', 'content': fallback_result}
            )
        else:
            session_attributes['fallback_in_progress'] = 'true'
    
    
    else:   
         
        # TODO: Implement slot validation (The part is commented)
        # # Perform slot validation
        # validation_result = validate_slots(intent_name, slots)
        # if not validation_result['isValid']:
        #     # Return ElicitSlot to prompt the user for correct input
        #     return elicit_slot(
        #         event['sessionState']['sessionAttributes'],
        #         intent_name,
        #         slots,
        #         validation_result['violatedSlot'],
        #         validation_result['message']
        #     )
        
        # If slots are valid, delegate control back to Lex to continue the dialog
        return delegate(event['sessionState']['sessionAttributes'], intent_name, slots)     #Assume all slots are valid for now

def handle_fulfillment_code_hook(event):
    # Extract the intent and slots
    intent_name = event['sessionState']['intent']['name']
    slots = event['sessionState']['intent']['slots']
    # Implement the logic to fulfill the user's intent
    fulfillment_result = fulfill_intent(event, intent_name, slots)
    session_attributes = event['sessionState']['sessionAttributes']
    
    # message contains all llm response as one string
    message = [{'contentType': 'PlainText', 'content': fulfillment_result}]
    
    # Split the fulfillment result into sections based on ***
    fulfillment_sections = fulfillment_result.split('***')
    
    # Create a list of messages from the sections
    messages = [{'contentType': 'PlainText', 'content': section.strip()} for section in fulfillment_sections if section.strip()]
    
    
    
    # # Split the fulfillment result into smaller chunks
    # chunk_size = 500  # Adjust the chunk size as needed
    # fulfillment_chunks = [fulfillment_result[i:i+chunk_size] for i in range(0, len(fulfillment_result), chunk_size)]
    # # Create a list of messages from the chunks
    # messages = [{'contentType': 'PlainText', 'content': chunk} for chunk in fulfillment_chunks]
    
    
    # Return the fulfillment result
    return close(session_attributes, intent_name, slots, 'Fulfilled', 'Close', messages)

def validate_slots(intent_name, slots):
    """
    Perform validation on the slot values. Customize this function based on your specific slots and validation logic.
    """
    # TODO: Perform validation on the slot values.  
    # Always Assume valid slots for now
    return build_validation_result(True, None, None)

def fulfill_intent(event, intent_name, slots):
    """
    Fulfill the user's intent. Customize this function based on your specific intents and fulfillment logic.
    """
    # Example
    if intent_name == 'ProjectUpdate':
        ProjectName = slots['ProjectName']['value']['interpretedValue']
        
        # Define the user's query based on collected slots
        user_query = (
            f"I need update regarding this project: {ProjectName}. "
        )
        
        # Define the system message for the LLM

        
        system_message_content = (
                "You are a virtual assistant specializing in providing updates of current projects."
            )
        
        # Define a system message that sets the role of the AI
        system_message = {
            "role": "system",
            "content": system_message_content
        }
        
        # Define the user message for the LLM
        user_message = {
            "role": "user",
            "content": user_query
        }
        
        # print(f"User Message: {user_query} \n")
        # print(f"System Message: {system_message_content} \n")
        
        llm_answer = query_llm(system_message, user_message)
        
        guide_message = llm_answer

        return guide_message
    
    # Add additional intent fulfillment logic as needed
    return "Intent fulfilled."

def handle_fallback_intent(event):
    intent_name = event['sessionState']['intent']['name']
    if intent_name == 'FallbackIntent':
        inputTranscript = event['inputTranscript']
        # Define the user's query based on collected slots
        user_query = (
            f"{inputTranscript}. "
        )
        
        # Query Amazon Kendra first to get relevant information from data sources
        kendra_query_response = query_kendra(user_query)
        top_n=3
        kendra_answer = process_kendra_response(kendra_query_response, top_n)
        
        # Define the system message for the LLM, including Kendra's answer if available
        if kendra_answer:
            system_message_content = (
                "You are a virtual assistant specializing in helping users with technical tasks"
                "Here is some relevant information from our internal documentation to help you: "
                f"{kendra_answer}. "
                "At the end of your response, include a 'References' section that cites the URLs associated with the information."
                "Use this information as a basis for your response."
                "Generate a response that is clear, concise, and well-organized. Provide only the essential steps, "
                "and offer to provide more details if the user needs them."
            )
        else:
            system_message_content = (
                "You are a virtual assistant specializing in helping users with technical tasks related to Outlook. "
                "Generate a response that is clear, concise, and well-organized. Provide only the essential steps, "
                "and offer to provide more details if the user needs them."
            )
        
        # Define a system message that sets the role of the AI
        system_message = {
            "role": "system",
            "content": system_message_content
        }
        
        # Define the user message for the LLM
        user_message = {
            "role": "user",
            "content": user_query
        }
        
        # print(f"User Message: {user_query} \n")
        # print(f"System Message: {system_message_content} \n")
        
        llm_answer = query_llm(system_message, user_message)
        
        guide_message = llm_answer
        return guide_message
    
    
    guide_message="This is not one of the predifned tasks that I can help with. Please, provide a description and I will try to help"
    
    return guide_message
    
# Helper functions

def query_llm(system_message, user_message):
     # Construct the base URL using the DNS
    base_url = f'http://{LLM_Server_Public_IP}:3000/v1'

    # Initialize the OpenAI client with the base URL of your hosted model and a dummy API key
    client = OpenAI(base_url=base_url, api_key='na')
    
    # # Modify the system message to instruct the LLM to divide the answer into sections
    # system_message['content'] += (
    #     " Please divide your answer into sections and separate each section with three asterisks (***)."
    # )
    
    # Modify the system message to instruct the LLM to divide the answer into smaller sections
    system_message['content'] += (
        " Please divide your answer into smaller parts, each containing no more than 100 words, and separate each part with three asterisks (***)."
    )
    
    # Create a chat completion request
    LLM_response = client.chat.completions.create(
        model="hugging-quants/Meta-Llama-3.1-8B-Instruct-AWQ-INT4",
        messages=[system_message, user_message],
    )
    
    user_query=user_message['content']
    LLM_answer = LLM_response.choices[0].message.content
    
    # print(f"User query: {user_query}")
    # print(f"LLM answer: {LLM_answer}")
    return LLM_answer

def query_kendra(query_text):
    index_id = KENDRA_INDEX_ID
    # Initialize the Kendra client
    kendra_client = boto3.client('kendra')

    try:
        # Perform the query
        response = kendra_client.query(
            IndexId=index_id,
            QueryText=query_text
        )
        return response

        # # Process and print the query results
        # if 'ResultItems' in response:
        #     print("Results found: \n")
        #     for item in response['ResultItems']:
        #         # Print out the result type and content
        #         if 'DocumentExcerpt' in item:
        #             print("Result Type:", item['Type'])
        #             print("Document Title:", item.get('DocumentTitle', {}).get('Text', 'N/A'))
        #             print("Document Excerpt:", item['DocumentExcerpt']['Text'])
        #             print("Document URI:", item.get('DocumentURI', 'N/A'))
        #             print("\n")
        # else:
        #     print("No results found for the query.")
    
    except Exception as e:
        print(f"An error occurred: {e}")

def process_kendra_response(response, top_n=1):
    """
    Process the response from Amazon Kendra and extract the most relevant passage.
    """
    # Check if the response contains result items
    if 'ResultItems' in response and len(response['ResultItems']) > 0:
        # Collect all excerpts with their confidence scores
        excerpts_with_urls  = []
        
        # Iterate through the result items
        for item in response['ResultItems']:
            # Look for a passage type result (Kendra returns different types like 'Answer', 'Document', etc.)
            if 'DocumentExcerpt' in item:
                excerpt_text = item['DocumentExcerpt']['Text']
                document_url = item['DocumentURI']
                 # Get ScoreConfidence from ScoreAttributes
                score_confidence = item.get('ScoreAttributes', {}).get('ScoreConfidence', 'LOW')
                
                # Assign a numeric score based on the confidence level
                confidence_score = 0  # Default to 0 for unknown or 'LOW' confidence
                if score_confidence == 'HIGH':
                    confidence_score = 3
                elif score_confidence == 'MEDIUM':
                    confidence_score = 2
                elif score_confidence == 'LOW':
                    confidence_score = 1

                excerpts_with_urls.append((excerpt_text, document_url, confidence_score))
        
        # Sort excerpts by confidence score (descending)
        excerpts_with_urls.sort(key=lambda x: x[2], reverse=True)
        
        # Get up to 'top_n' excerpts
        top_excerpts_with_urls = excerpts_with_urls[:top_n]
        
        # Format the top excerpts and URLs into a single string
        formatted_excerpts = [
            f"Excerpt: {excerpt}\nURL: {url}"
            for excerpt, url, _ in top_excerpts_with_urls
        ]
        
        # Join the formatted excerpts into a single string, separating them with double newlines
        return "\n\n".join(formatted_excerpts) if formatted_excerpts else False
        
    # If no relevant passage is found, return False or a default message
    return False
        
        
def build_validation_result(is_valid, violated_slot, message_content):
    return {
        'isValid': is_valid,
        'violatedSlot': violated_slot,
        'message': {'contentType': 'PlainText', 'content': message_content}
    }

def elicit_slot(session_attributes, intent_name, slots, slot_to_elicit, message):
    return {
        'sessionState': {
            'sessionAttributes': session_attributes,
            'dialogAction': {
                'type': 'ElicitSlot',
                'slotToElicit': slot_to_elicit
            },
            'intent': {
                'name': intent_name,
                'slots': slots,
                'state': 'InProgress'
            }
        },
        'messages': [message]
    }

def delegate(session_attributes, intent_name, slots):
    return {
        'sessionState': {
            'sessionAttributes': session_attributes,
            'dialogAction': {
                'type': 'Delegate'
            },
            'intent': {
                'name': intent_name,
                'slots': slots,
                'state': 'InProgress'
            }
        }
    }

def close(session_attributes, intent_name, slots, fulfillment_state, dialogAction, messages):
    follow_up_message = {'contentType': 'PlainText', 'content': "I hope this was helpful!"}
    # more_help_message = {'contentType': 'PlainText', 'content': "Can I assist you with something else?"}
    
    if fulfillment_state == 'Fulfilled':
        # Append the follow-up message after all fulfillment messages
        messages.append(follow_up_message)
        
    return {
        'sessionState': {
            'sessionAttributes': session_attributes,
            'dialogAction': {
                'type': dialogAction
            },
            'intent': {
                'name': intent_name,
                'slots': slots,
                'state': fulfillment_state
            }
        },
        'messages': messages
    }

