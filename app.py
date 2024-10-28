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
    "total_fat": 0,
    "total_fiber": 0,  # New field for fiber tracking
    "prompts": []  # Store user inputs for reference
}

# Nutrition goals (can be made user-configurable)
nutrition_goals = {
    "calories": 2000,
    "protein": 150,  # grams
    "carbs": 250,    # grams
    "fat": 70,       # grams
    "fiber": 40      # grams
}

# Prompt the LLM to extract nutrition data
def get_nutrition_info(food_description):
    try:
        # Use ChatGPT to extract nutrition data
        response = openai.ChatCompletion.create(
            model="gpt-4",  # Or use gpt-4-turbo for cost-effective requests
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a nutrition expert. Given a food description, "
                        "return the calories, protein, carbs, fat, and fiber in the following format: "
                        "Calories: X kcal, Protein: X g, Carbs: X g, Fat: X g, Fiber: X g."
                    )
                },
                {"role": "user", "content": food_description}
            ]
        )

        # Extract and parse the response
        content = response.choices[0].message.content
        nutrition_data = parse_nutrition_response(content)

        return nutrition_data

    except Exception as e:
        print(f"Error with OpenAI API call: {e}")
        return None

def parse_nutrition_response(response):
    try:
        # Parse the structured response from ChatGPT
        lines = response.split(", ")
        return {
            "calories": int(lines[0].split(": ")[1].split()[0]),
            "protein": float(lines[1].split(": ")[1].split()[0]),
            "carbs": float(lines[2].split(": ")[1].split()[0]),
            "fat": float(lines[3].split(": ")[1].split()[0]),
            "fiber": float(lines[4].split(": ")[1].split()[0])
        }
    except Exception as e:
        print(f"Error parsing response: {e}")
        return None

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        # Handle user input submission
        food_description = request.form["food_input"]
        nutrition = get_nutrition_info(food_description)

        if nutrition:
            # Update totals
            user_data["total_calories"] += nutrition["calories"]
            user_data["total_protein"] += nutrition["protein"]
            user_data["total_carbs"] += nutrition["carbs"]
            user_data["total_fat"] += nutrition["fat"]
            user_data["total_fiber"] += nutrition["fiber"]

            # Log the user's input
            user_data["prompts"].append(food_description)

        return redirect(url_for("index"))

    # Calculate remaining goals
    remaining = {
        key: max(0, nutrition_goals[key] - user_data[f"total_{key}"])
        for key in nutrition_goals
    }

    return render_template("index.html", user_data=user_data, remaining=remaining)

@app.route("/clear", methods=["POST"])
def clear_data():
    # Reset user data and log
    global user_data
    user_data = {
        "total_calories": 0,
        "total_protein": 0,
        "total_carbs": 0,
        "total_fat": 0,
        "total_fiber": 0,
        "prompts": []
    }
    return redirect(url_for("index"))

if __name__ == "__main__":
    # Check if the app is running on Render (or any deployment environment)
    if os.getenv("RENDER"):
        # Render uses '0.0.0.0' and port 5000 (or environment-provided port)
        port = int(os.getenv("PORT", 5000))
        app.run(host="0.0.0.0", port=port)
    else:
        # Local development uses default localhost and port 5000
        app.run(host="127.0.0.1", port=5000, debug=True)