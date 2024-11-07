import os
import sys
from cryptography.fernet import Fernet
import google.generativeai as genai

def get_base_path():
    # Get the base path for bundled resources
    if getattr(sys, 'frozen', False):
        return sys._MEIPASS
    else:
        return os.path.dirname(os.path.abspath(__file__))

def upload_to_gemini(path, mime_type=None):
  
  file = genai.upload_file(path, mime_type=mime_type)
#   print(f"Uploaded file '{file.display_name}' as: {file.uri}")
  return file

def setup_model(sys_instruction, temperature, model_name, output_format):
    try:
        base_path = get_base_path()
        
        # Update file paths to use base_path
        key_path = os.path.join(base_path, 'secret.key')
        api_key_path = os.path.join(base_path, 'encrypted_api_key.json')
        
        # Load the encryption key
        with open(key_path, 'rb') as key_file:
            key = key_file.read()
        cipher_suite = Fernet(key)

        # Decrypt the API key
        with open(api_key_path, 'rb') as f:
            encrypted_api_key = f.read()
        GID = cipher_suite.decrypt(encrypted_api_key).decode()

        genai.configure(api_key=GID)

        # Create the model
        generation_config = {
            "temperature": temperature,
            "top_p": 0.95,
            "top_k": 40,
            "max_output_tokens": 8192,
            "response_mime_type": output_format,
        }

        safety_settings = [
            {
                "category": "HARM_CATEGORY_HARASSMENT",
                "threshold": "BLOCK_NONE"
            },
            {
                "category": "HARM_CATEGORY_HATE_SPEECH",
                "threshold": "BLOCK_NONE"
            },
            {
                "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                "threshold": "BLOCK_NONE"
            },
            {
                "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                "threshold": "BLOCK_NONE"
            },
        ]

        model = genai.GenerativeModel(
            model_name=model_name,
            generation_config=generation_config,
            safety_settings=safety_settings,
            system_instruction=sys_instruction,
        )

        return model
    
    except Exception as e:
        print(f"Error in setup_model: {e}")
        return None

def get_gemini_response_for_image(img_list, context_content, prompt, temperature, model_name, output_format):
    try:
        if model_name == 'pro':
            model_name = "gemini-1.5-pro-002"
        else:
            model_name = "gemini-1.5-flash-002"
        
        if output_format == 'text':
            output_format = "text/plain"
        else:
            output_format = "application/json"
        
        model = setup_model(prompt, temperature, model_name, output_format)
        if model is None:
            print("Failed to setup model")
            return None
        
        files = []
        for img_path in img_list:
            try:
                file = upload_to_gemini(img_path, mime_type="image/jpeg")
                files.append(file)
            except Exception as e:
                print(f"Error uploading image: {e}")
                return None
        
        if not files:
            print("No files were uploaded successfully")
            return None
            
        parts_list = [files[0]]
        if context_content:
            parts_list.append(context_content)
        
        # print (f"chat_parts: {parts_list}")

        chat_session = model.start_chat(
            history=[
                {
                    "role": "user",
                    "parts": parts_list,
                },
            ]
        )

        response = chat_session.send_message(prompt)
        return response.text

    except Exception as e:
        print(f"Error in get_gemini_response_for_image: {e}")
        return None
