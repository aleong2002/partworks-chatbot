import os
import re
import time
from flask import Flask, jsonify, request, url_for
from flask_cors import CORS
from dotenv import load_dotenv
import openai
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from playwright.sync_api import sync_playwright
from langchain_community.document_loaders import WebBaseLoader
from pinecone import ServerlessSpec, Pinecone
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_pinecone import PineconeVectorStore
from langchain.schema import (SystemMessage, HumanMessage, AIMessage)

load_dotenv()

# Initialize Flask app
app = Flask(__name__)
CORS(app)
openai.api_key = os.getenv('OPENAI_API_KEY')
api_key = os.getenv('PINECONE_API_KEY')
pc = Pinecone(api_key=api_key)

url = ""
search_keyword = ""

llm = ChatOpenAI(
    openai_api_key=openai.api_key,
    model_name='gpt-3.5-turbo'
)

messages = [
    SystemMessage(content="""You are a helpful webcrawling assistant specializing 
                  in Refrigerator and Dishwasher parts on the PartSelect website. Ignore inquiries
                   that do not relate to these machines, parts, or helping with transactions. Use prior
                   questions and answers from user input to guide assistant's follow-up questions and 
                  answers. If unable to answer, prompt from more information.
                   Questions about installing/replacing products should additionally tell users about installation videos on the product page. Don't mention 
                  context in your answers. Remember to ignore questsions unrelated to fridges, dishwashers, their parts, or transactions for Part Select."""),
    HumanMessage(content="Hi AI, how are you today?"),
    AIMessage(content="I'm great thank you. How can I help you?")
]

def generate_answer(user_query):
    try:
        prompt = HumanMessage(
            content=user_query
        )
        messages.append(prompt)
        ai_res = llm(messages)
        print(f"generated answer: {ai_res.content}")
        return ai_res.content
    except Exception as e:
        print(f"Exception occured in generate_answer: {e}")
        return "I am not equipped to answer this question."

def set_up_rag(url):
    index_name = "serverless-index"
    spec = ServerlessSpec(
        cloud='aws',
        region='us-east-1'
    )

    existing_indexes = [
        index_info["name"] for index_info in pc.list_indexes()
    ]

    if index_name not in existing_indexes:
        pc.create_index(
            index_name,
            dimension=1536,
            metric='dotproduct',
            spec=spec
        )
        while not pc.describe_index(index_name).status['ready']:
            time.sleep(1)
        
    index = pc.Index(index_name)
    time.sleep(1)

    loader = WebBaseLoader(url) #'https://www.partselect.com/PS11752778-Whirlpool-WPW10321304-Refrigerator-Door-Shelf-Bin.htm')
    data = loader.load()

    for document in data:
        if hasattr(document, 'page_content'):
            # cut down as much of the formatting and non-essential characters as i can
            cleaned_page_content = document.page_content.replace('\n', ' ').replace('\t', '').replace('\r', '').replace('                            ', ' ').replace('        ', ' ').replace('★', '').replace('X', '')
            document.page_content = cleaned_page_content

    #print(data)
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=400, chunk_overlap=200)
    all_splits = text_splitter.split_documents(data)
    all_splits = all_splits[18:24] #gets the product description
    #print(all_splits)

    vectorstore = PineconeVectorStore.from_documents(
        documents=all_splits,
        embedding=OpenAIEmbeddings(),
        index_name=index_name
    )

    #retriever = vectorstore.as_retriever()
    print("set up rag")
    return vectorstore

def augment_prompt(vectorstore, user_query):
    results = vectorstore.similarity_search(user_query, 3)
    while not results:
        results = vectorstore.similarity_search(user_query,3)
    
    #print(f"results: {results}")
    context = " ".join([x.page_content for x in results])
    augmented_prompt = f"""Using the context below, answer the query. Verify the answer with the context to make sure product and answer is true. 
    Don't make anything up. Identify the product identity and details from the context and use that information to inform answers. Remember refrigerator parts cannot be used with dishwashers and vice versa.
    Questions about compatability with models should follow up and ask if it is a fridge or dishwasher part to see if it will work with a fridge or dishwasher. 

    Contexts: {context}
    Query: {user_query}"""
    return augmented_prompt

# get the part number (Starts with PS) or the model -- has to be 'aksjfhkahfa' model when inputted
def extract_keyword(user_query):
    # Define regex patterns for part number, make, and model
    part_number_pattern = r'(ps\w+)'
    make_model_pattern = r' (\w+) (model)'

    # Search for part number, make, or model in the user query
    part_number_match = re.search(part_number_pattern, user_query, re.IGNORECASE)
    make_model_match = re.search(make_model_pattern, user_query, re.IGNORECASE)

    # If part number is found, use it as the search keyword
    if part_number_match:
        return part_number_match.group(1)
    # If make or model is found, use it as the search keyword
    elif make_model_match:
        return make_model_match.group(1)
    else:
        return None  # No relevant information found

# search for the part/model using playwright in background
def search_with_playwright(search_keyword):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        #browser = p.chromium.connect_over_websocket("ws://localhost:9222/devtools/browser")
        page = browser.new_page()
        page.goto('https://www.partselect.com/Dishwasher-Parts.htm')
        page.fill('input.js-headerNavSearch', search_keyword)
        page.keyboard.press('Enter')
        page.wait_for_timeout(5000)
        url = page.url
        #print(url)
        page.wait_for_timeout(2000)
        return url
    
def process_query(user_query):
    search_keyword = extract_keyword(user_query)
    print(f"extracted search keyword: {search_keyword}")
    if search_keyword:
        url = search_with_playwright(search_keyword)
        print(url)
        retriever = set_up_rag(url)
        prompt = augment_prompt(retriever, user_query)
        print(prompt)
        ai_res = generate_answer(prompt)
        #print(f"ai_res: {ai_res}")
        return ai_res
    else:
        return None
    
@app.route('/api', methods=['POST'])
def template_backend():
    user_query = request.json.get("query")
    print(user_query)
    assistant_response = None
    try:
        result = process_query(user_query)
        print(f"result: {result}")
        if result:
            assistant_response = {
            'content': result
        }
        else:
            assistant_response = {
                'content': generate_answer(user_query)
            }
    except Exception as e:
        print("Unable to search")
    return jsonify(assistant_response)


@app.route('/api/initial', methods=['GET'])
def initial_message():
    return jsonify({"role": "assistant", "content": "Hello! How can I assist you today with your refrigerator and dishwasher needs?"})

if __name__ == '__main__':
    app.run(port=5000,debug=True)

    """""" 

""" 
# Example user queries
user_queries = [
    "How can I install PS11752778?",
    "Is this part compatible with my WDT780SAEM1 model?",
    "The ice maker on my Whirlpool fridge is not working. How can I fix it?",
]
"""
