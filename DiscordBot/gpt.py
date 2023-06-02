# This is example code using GPT-4 to do a basic classification of a text string
# It is super basic, your milestone 3 should do better than this
# This is a live API key that should be used only for the CS 152 project
# Please do not check the API key into a public GitHub repo or share it with anybody outside of your group


import os
import json
import openai

# print(openai.Model.list()) # Can be used to verify GPT-4 access

# There should be a file called 'tokens.json' inside the same folder as this file
token_path = "tokens.json"
if not os.path.isfile(token_path):
    raise Exception(f"{token_path} not found!")
with open(token_path) as f:
    # If you get an error here, it means your token is formatted incorrectly. Did you put it in quotes?
    tokens = json.load(f)
    openai.organization = tokens["openai-org"]
    openai.api_key = tokens["openai-key"]

class GPTClassification:
    NOT_SEXTORTION = "Not Sextortion"
    MAYBE_SEXTORTION = "Potentially Sextortion"
    YES_SEXTORTION = "Sextortion"

def ask_gpt(message: str):
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {
                "role": "system",
                "content": f"You are a content moderation system. Classify the input message as either '{GPTClassification.YES_SEXTORTION}', '{GPTClassification.MAYBE_SEXTORTION}', or '{GPTClassification.NOT_SEXTORTION}'.",
            },
            {"role": "user", "content": "I found naked pictures of you."},
            {"role": "assistant", "content": GPTClassification.MAYBE_SEXTORTION},
            {"role": "user", "content": "I love you"},
            {"role": "assistant", "content": GPTClassification.NOT_SEXTORTION},
            {"role": "user", "content": "Send me nudes."},
            {"role": "assistant", "content": GPTClassification.MAYBE_SEXTORTION},
            {"role": "user", "content": "Send me nudes or I'll post your photos online"},
            {"role": "assistant", "content": GPTClassification.YES_SEXTORTION},
            {"role": "user", "content": "I found some senstive photos of you. Maybe we could work out a deal?"},
            {"role": "assistant", "content": GPTClassification.YES_SEXTORTION},
            {"role": "user", "content": "Your boyfriend sent me some sensitive photos of you."},
            {"role": "assistant", "content": GPTClassification.MAYBE_SEXTORTION},
            {"role": "user", "content": "Your boyfriend sent me some sensitive photos of you. What's stopping me from posting them online?"},
            {"role": "assistant", "content": GPTClassification.YES_SEXTORTION},
            {"role": "user", "content": message},
        ],
    )
    return response["choices"][0]["message"]["content"]

if __name__ == "__main__":
    print(ask_gpt("Hello, I have sensitive financial information"))
