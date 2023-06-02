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

    NO_HISTORY = "None"
    SOME_HISTORY = f"Flagged: {MAYBE_SEXTORTION}"
    HAS_HISTORY = f"Flagged: {YES_SEXTORTION}"

    f_to_h = {
        NOT_SEXTORTION: NO_HISTORY,
        MAYBE_SEXTORTION: SOME_HISTORY,
        YES_SEXTORTION: HAS_HISTORY
    }

    def convert_to_hist(flag: str) -> str:
        return GPTClassification.f_to_h.get(flag, GPTClassification.NO_HISTORY)

def ask_gpt(message: str, history: str = GPTClassification.NO_HISTORY):
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {
                "role": "system",
                "content": f"You are a content moderation system designed for Instagram. "\
                    f"Classify the input message as either '{GPTClassification.YES_SEXTORTION}', '{GPTClassification.MAYBE_SEXTORTION}', or '{GPTClassification.NOT_SEXTORTION}'. " \
                    f"It is possible that a message might have come from a conversation that was previously flagged for sextortion. You will be provided the flag in that case. " \
                    f"Possible flags are '{GPTClassification.NO_HISTORY}', '{GPTClassification.SOME_HISTORY}', and '{GPTClassification.HAS_HISTORY}'."
                    
            },
            {"role": "user", "content": f"History: '{GPTClassification.NO_HISTORY}' Message: "\
             "I found naked pictures of you."},
            {"role": "assistant", "content": GPTClassification.MAYBE_SEXTORTION},

            {"role": "user", "content": f"History: '{GPTClassification.NO_HISTORY}' Message: "\
             "I love you"},
            {"role": "assistant", "content": GPTClassification.NOT_SEXTORTION},

            {"role": "user", "content": f"History: '{GPTClassification.NO_HISTORY}' Message: "\
             "give me money"},
            {"role": "assistant", "content": GPTClassification.NOT_SEXTORTION},

            {"role": "user", "content": f"History: '{GPTClassification.SOME_HISTORY}' Message: "\
             "give me money"},
            {"role": "assistant", "content": GPTClassification.YES_SEXTORTION},
            
            {"role": "user", "content": f"History: '{GPTClassification.NO_HISTORY}' Message: "\
             "Send me nudes."},
            {"role": "assistant", "content": GPTClassification.MAYBE_SEXTORTION},

            {"role": "user", "content": f"History: '{GPTClassification.MAYBE_SEXTORTION}' Message: "\
             "Send me nudes."},
            {"role": "assistant", "content": GPTClassification.YES_SEXTORTION},

            {"role": "user", "content": f"History: '{GPTClassification.NO_HISTORY}' Message: "\
             "Send me nudes or I'll post your photos online"},
            {"role": "assistant", "content": GPTClassification.YES_SEXTORTION},

            {"role": "user", "content": f"History: '{GPTClassification.NO_HISTORY}' Message: "\
             "I found some sensitive photos of you."},
            {"role": "assistant", "content": GPTClassification.MAYBE_SEXTORTION},

            {"role": "user", "content": f"History: '{GPTClassification.SOME_HISTORY}' Message: "\
             "I found some sensitive photos of you."},
            {"role": "assistant", "content": GPTClassification.MAYBE_SEXTORTION},

            {"role": "user", "content": f"History: '{GPTClassification.HAS_HISTORY}' Message: "\
             "I found some sensitive photos of you."},
            {"role": "assistant", "content": GPTClassification.YES_SEXTORTION},

            {"role": "user", "content": f"History: '{GPTClassification.NO_HISTORY}' Message: "\
             "I found some sensitive photos of you. Maybe we could work out a deal?"},
            {"role": "assistant", "content": GPTClassification.YES_SEXTORTION},

            {"role": "user", "content": f"History: '{GPTClassification.NO_HISTORY}' Message: "\
             "Your boyfriend sent me some sensitive photos of you."},
            {"role": "assistant", "content": GPTClassification.MAYBE_SEXTORTION},

            {"role": "user", "content": f"History: '{GPTClassification.SOME_HISTORY}' Message: "\
             "Your boyfriend sent me some sensitive photos of you."},
            {"role": "assistant", "content": GPTClassification.YES_SEXTORTION},

            {"role": "user", "content": f"History: '{GPTClassification.NO_HISTORY}' Message: "\
             "Your boyfriend sent me some sensitive photos of you. What's stopping me from posting them online?"},
            {"role": "assistant", "content": GPTClassification.YES_SEXTORTION},
            
            {"role": "user", "content": f"History: '{history}' Message: {message}"},
        ],
    )
    return response["choices"][0]["message"]["content"]

if __name__ == "__main__":
    print(ask_gpt("History: 'None' Message: I found some sensitive information about you. Pay me bitcoin or I'll release it."))
