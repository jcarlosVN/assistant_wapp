from openai import OpenAI
import os
import time
import json
from dotenv import load_dotenv
import openai_consult
import wapp_scraper
import wapp_response_sender

load_dotenv()
api_key = os.getenv('OPENAI_API_KEY')
client = OpenAI(api_key=api_key)

def run_assistant_fcalling(thread, assistant):

    # Run the assistant
    run = client.beta.threads.runs.create(
        thread_id=thread.id,
        assistant_id=assistant.id,
    )
    print(run.id, thread.id, assistant.id)
    # Wait for completion
    while run.status not in ["requires_action", "completed"]:
        # Be nice to the API
        time.sleep(0.5)
        run = client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
        print(run.status)

    # Retrieve the Messages
    messages = client.beta.threads.messages.list(thread_id=thread.id)
    new_message = messages.data[0].content[0].text.value
    #print(new_message, run.status)
    if run.status == "completed":
        return new_message, run.status

    elif run.status == "requires_action":
        return run, run.status
    else:
        return "error"

mensaje, numero_wapp = wapp_scraper.scraping_whatsapp()
print(mensaje, numero_wapp)
assistant = client.beta.assistants.retrieve('asst_XJ746NdCGqcDBr8GIiXcKSkm')
thread = client.beta.threads.retrieve('thread_WiyGjgUXR87OcAJkWNAqZhp9')

# Add message to thread
message = client.beta.threads.messages.create(
    thread_id=thread.id,
    role="user",
    content=mensaje
    )

value1, value2 = run_assistant_fcalling(thread, assistant)
if value2 == "completed":
    new_message = value1
    print(f'SIMPLE>> mensaje para {numero_wapp}: {new_message}')
elif value2 == "requires_action":
    run = value1

    tool_outputs = []

    # Loop through each tool in the required action section
    for tool_call in run.required_action.submit_tool_outputs.tool_calls:
        if tool_call.function.name == "get_current_price":
            arguments = json.loads(tool_call.function.arguments)
            output = arguments['product']
            print(arguments, output)
            tool_outputs.append({
                "tool_call_id": tool_call.id,
                "output": openai_consult.get_current_price(output)
            })

    # Submit all tool outputs at once after collecting them in a list
    if tool_outputs:
        try:
            run = client.beta.threads.runs.submit_tool_outputs_and_poll(
                thread_id=thread.id,
                run_id=run.id,
                tool_outputs=tool_outputs
            )
            print("Tool outputs submitted successfully.")
            print("-----------------------")
        except Exception as e:
            print("Failed to submit tool outputs:", e)
            print("-----------------------")
    else:
        print("No tool outputs to submit.")

    if run.status == 'completed':
        messages = client.beta.threads.messages.list(
            thread_id=thread.id
        )
        #print(messages)
        #print("-----------------------")
        if messages.data:
            new_message = messages.data[0].content[0].text.value
            #print(new_message)
            print(f'COMPLEJA>> mensaje para {numero_wapp}: {new_message}')
    else:
        print(run.status)


wapp_response_sender.enviar_mensaje_whatsapp(numero_wapp, new_message)
