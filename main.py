from flask import Flask, render_template, request, send_from_directory
import genanki
import os
import openai
import json
from typing import List, Tuple
from pydantic import BaseModel

app = Flask(__name__)

# Initialize OpenAI API
openai.api_key = 'YOUR_OPENAI_API_KEY'  # Set your API key here

class AnkiCard(BaseModel):
    question: str
    answer: str

class AnkiDeckResponse(BaseModel):
    title: str
    cards: List[AnkiCard]

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        data = request.form["data"]
        
        # Use OpenAI function calling with the specific format
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo-0613",
            messages=[
                {"role": "user", "content": "Generate Anki cards for the following content: " + data}
            ],
            functions=[
                {
                    "name": "generate_anki_deck",
                    "description": "Transform content into a series of Anki cards.",
                    "parameters": AnkiDeckResponse.schema()
                }
            ],
            function_call={"name": "generate_anki_deck"}
        )

        output = json.loads(response.choices[0]["message"]["function_call"]["arguments"])
        
        # Process the 'output' to extract structured data for Anki cards
        cards_data = process_output_to_cards(output)

        # Create anki model
        model = genanki.Model(
            1607392319,
            "Simple Model",
            fields=[
                {"name": "Question"},
                {"name": "Answer"},
            ],
            templates=[
                {
                    "name": "Card 1",
                    "qfmt": "{{Question}}",
                    "afmt": "{{Answer}}",
                },
            ],
        )

        # Create anki deck
        deck = genanki.Deck(2059400110, output["title"])

        # Add cards to deck
        for question, answer in cards_data:
            note = genanki.Note(
                model=model,
                fields=[question, answer],
            )
            deck.add_note(note)

        # Save to .apkg file
        genanki.Package(deck).write_to_file("output_deck.apkg")
        return send_from_directory(os.getcwd(), "output_deck.apkg", as_attachment=True)

    return '''
    <h2>Anki Deck Generator</h2>
    <form method="post">
        <textarea name="data" rows="15" cols="50" placeholder="Enter any free form text"></textarea><br><br>
        <input type="submit" value="Generate Anki Deck">
    </form>
    '''

def process_output_to_cards(output):
    return [(card["question"], card["answer"]) for card in output["cards"]]

if __name__ == "__main__":
    app.run(debug=True)
