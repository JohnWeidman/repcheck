from django.shortcuts import render
from google import genai
import os 
from dotenv import load_dotenv
from google import genai
import os 
from dotenv import load_dotenv

# Create your views here.
load_dotenv()
def citizen_home(request):
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

    response = client.models.generate_content(
        model="gemini-2.0-flash", contents="Explain the concept of democracy in simple terms for an 8th grader."
    )
    
    return render(request, "citizens/index.html", {"response": response.text})

def citizen_resources(request):
    return render(request, "citizens/citizen_resources.html")