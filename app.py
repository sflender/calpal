import os
from flask import Flask, request, jsonify, render_template, redirect, url_for
import openai

# Initialize Flask app and OpenAI API key
app = Flask(__name__)
openai.api_key = os.getenv("OPENAI_API_KEY")

# Store daily macro totals (for simplicity, using in-memory storage)
user_data = {
    "total_calories": 0,
    "total_protein": 0,
    "total_carbs": 0,
    "total_fat": 0
}

# Nutrition goals (can be made user-configurable)
nutrition_goals = {
    "calories": 2000,
    "protein": 150,  # grams
    "carbs": 250,    # grams
    "fat": 70        # grams
}

# Prompt the LLM to extract nutrition data
def get_nutrition_info(food_description):
    response = openai.ChatCompletion.create(
        #model="gpt-4o-mini",
        model="gpt-3.5-turbo",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a nutrition expert. Given a food description, "
                    "return an analysis with the calories, protein, carbs, and fat in the following format: "
                    "Calories: X kcal, Protein: X g, Carbs: X g, Fat: X g."
                )
            },
            {"role": "user", "content": food_description}
        ]
    )
    content = response.choices[0].message.content
    return parse_nutrition_response(content)

# Parse the LLM response to extract numeric values
def parse_nutrition_response(response):
    try:
        lines = response.split(", ")
        nutrition_data = {
            "calories": int(lines[0].split(": ")[1].split()[0]),
            "protein": float(lines[1].split(": ")[1].split()[0]),
            "carbs": float(lines[2].split(": ")[1].split()[0]),
            "fat": float(lines[3].split(": ")[1].split()[0])
        }
        return nutrition_data
    except Exception as e:
        print(f"Error parsing response: {e}")
        return None

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        food_description = request.form["food_input"]
        nutrition = get_nutrition_info(food_description)

        if nutrition:
            # Update totals
            user_data["total_calories"] += nutrition["calories"]
            user_data["total_protein"] += nutrition["protein"]
            user_data["total_carbs"] += nutrition["carbs"]
            user_data["total_fat"] += nutrition["fat"]
        
        return redirect(url_for("index"))

    # Calculate remaining macros to meet goals
    remaining = {
        "calories": max(0, nutrition_goals["calories"] - user_data["total_calories"]),
        "protein": max(0, nutrition_goals["protein"] - user_data["total_protein"]),
        "carbs": max(0, nutrition_goals["carbs"] - user_data["total_carbs"]),
        "fat": max(0, nutrition_goals["fat"] - user_data["total_fat"])
    }

    return render_template("index.html", user_data=user_data, remaining=remaining)

if __name__ == "__main__":
    app.run(debug=True)
