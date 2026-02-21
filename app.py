from dotenv import load_dotenv
load_dotenv() # load .env file to get the secrets credentials
import streamlit as st
import google.generativeai as genai
import os

genai.configure(api_key=os.getenv("GOOGLE_API_KEY")) 

model = genai.GenerativeModel("gemini-2.5-flash")

def my_output(query) -> None:
    response = model.generate_content(query)
    return response.text


# for streamlit ui
st.set_page_config(page_title="Google Gen AI Chatbot", page_icon=":robot_face:")
st.header("Google Gen AI Chatbot")
input_text = st.text_input("Ask me anything!")
submit_button = st.button("Ask your question")

if submit_button:
    response = my_output(input_text)
    st.header("Response is here :")
    st.write(response)
    