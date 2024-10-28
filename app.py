import os
import openai
from flask import Flask, request, redirect, url_for, render_template, session
from flask_session import Session

# Initialize the Flask app
app = Flask(__name__)

# Configure Flask-Session to store sessions server-side (in the filesystem)
app.config["SESSION_TYPE"] = "filesystem"
app.secret_key = os.urandom(24)  # Generate a random secret key
Session(app)  # Initialize the session

# Nutrition goals
nutrition_goals = {
    "calories": 2000,
    "protein": 150,  # grams
    "carbs": 250,    # grams
    "fat": 70,       # grams
    "fiber": 40      # grams
}

# OpenAI API setup
openai.api_key = os.getenv("OPENAI_API_KEY")  # Load the API key from environment variables

def get_nutrition_info(food_description):
    """Use OpenAI to get nutrition data from the user's food description."""
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4-turbo",  # You can also use gpt-4 if available
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a nutrition expert. Given a food description, "
                        "return the calories, protein, carbs, fat, and fiber in the format: "
                        "'Calories: X kcal, Protein: X g, Carbs: X g, Fat: X g, Fiber: X g.'"
                    )
                },
                {"role": "user", "content": food_description}
            ]
        )
        return parse_nutrition_response(response.choices[0].message.content)
    except Exception as e:
        print(f"Error with OpenAI API call: {e}")
        return None

def parse_nutrition_response(response):
    """Parse the response from the OpenAI API."""
    try:
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
    """Render the homepage and handle user inputs."""
    # Initialize session data if not already set
    if "user_data" not in session:
        session["user_data"] = {
            "total_calories": 0,
            "total_protein": 0,
            "total_carbs": 0,
            "total_fat": 0,
            "total_fiber": 0,
            "prompts": []
        }

    if request.method == "POST":
        # Process user input
        food_description = request.form.get("food_input")
        if food_description:
            nutrition = get_nutrition_info(food_description)

            if nutrition:
                # Update user's session data
                user_data = session["user_data"]
                user_data["total_calories"] += nutrition["calories"]
                user_data["total_protein"] += nutrition["protein"]
                user_data["total_carbs"] += nutrition["carbs"]
                user_data["total_fat"] += nutrition["fat"]
                user_data["total_fiber"] += nutrition["fiber"]
                user_data["prompts"].append(food_description)
                session["user_data"] = user_data  # Save back to session

        return redirect(url_for("index"))

    # Calculate remaining nutrition goals
    user_data = session["user_data"]
    remaining = {
        key: max(0, nutrition_goals[key] - user_data.get(f"total_{key}", 0))
        for key in nutrition_goals
    }

    return render_template("index.html", user_data=user_data, remaining=remaining)

@app.route("/clear", methods=["POST"])
def clear_data():
    """Clear the current user's session data."""
    session.pop("user_data", None)
    return redirect(url_for("index"))

if __name__ == "__main__":
    # Detect if the app is running on Render or locally
    if os.getenv("RENDER"):  # This variable is only set in Render
        host = "0.0.0.0"
        port = int(os.getenv("PORT", 5000))
        debug = False
    else:  # For local development
        host = "127.0.0.1"
        port = 5000
        debug = True

    app.run(host=host, port=port, debug=debug)
