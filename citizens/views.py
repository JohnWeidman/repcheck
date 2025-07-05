from django.shortcuts import render
from google import genai
import os 
from dotenv import load_dotenv

# Create your views here.
load_dotenv()
def citizen_home(request):
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

    response = client.models.generate_content(
        model="gemini-2.5-flash", contents="Explain how AI works in a few words"
    )
    print(response.text)
    return render(request, "citizens/index.html")

def citizen_resources(request):
    return render(request, "citizens/citizen_resources.html")