import base64
import requests
import os

def get_more_info(filepath, dis):
    # Read and encode the image
    with open(filepath, 'rb') as image_file:
        encoded_image = base64.b64encode(image_file.read()).decode('utf-8')

    # Gemini 1.5 Pro API endpoint and key
    endpoint = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-pro:generateContent"
    api_key = "AIzaSyDLryzPzgltN6XffTSv-_85mZUig6bwgbg"  # Store your API key in an environment variable


    url = f"{endpoint}?key={api_key}"

    headers = {
        "Content-Type": "application/json"
    }

    # Payload for Gemini 1.5 Pro
    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "inlineData": {
                            "mimeType": "image/jpeg",
                            "data": encoded_image
                        }
                    },
                    {
                        "text": "Analyze this image and detect plant disease. Provide the response with crop name, disease, and suggestions for treatment or management. If the image is not clear or you are uncertain, return only 'unable to fetch'."
                    }
                ]
            }
        ]
    }

    # Send request to Gemini API
    response = requests.post(url, headers=headers, json=payload)

    if response.status_code == 200:
        result = response.json()
        # Extract the generated text from Gemini's response
        return result['candidates'][0]['content']['parts'][0]['text']
    else:
        return f"Error: {response.status_code}, {response.text}"