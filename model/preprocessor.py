from langchain.schema import Document
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings,HuggingFaceEndpoint,ChatHuggingFace
import requests
from langchain_core.prompts import PromptTemplate
from transformers import pipeline
from dotenv import load_dotenv
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableParallel

load_dotenv()

API_KEY = "b7e6c4a2784d4360a655f50b2eaa008b"

max_result = 15
def build_articles(query,max_results = 15):
    url = f"https://newsapi.org/v2/everything?q={query}&pageSize={max_results}&apiKey={API_KEY}"
    responses = requests.get(url).json()
    return responses['articles']

def build_documents(articles):
    return [
        Document(
           page_content = article['content'] or article['description'] or '',
           metadata={'title': article['title'], 'url': article['url'], 'source': article['source']['name']}

        )
        for article in articles
    ]

def build_vectorstore(docs):
    embedding = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    return FAISS.from_documents(
        docs,embedding
    )

llm = HuggingFaceEndpoint(
    repo_id="meta-llama/Meta-Llama-3-8B-Instruct",
    task="text-generation",
)
chat_model  = ChatHuggingFace(llm=llm)

prompt = PromptTemplate(
    template = """
    You are an expert news analyst.
    Analyze the following articles about: {query}

    Context:
    {context}

    Provide a summary and key insights.
    """,
    input_variables=['query','context']
)

parser = StrOutputParser()

classifier = pipeline("text-classification", model="roberta-base-openai-detector")

def detect_fake(text):
    result = classifier(text)  # avoid truncation
    return result

def summarize(query,retriever):
    context = "\n\n".join(doc.page_content for doc in retriever.get_relevant_documents(query))
    chain_inputs = RunnableParallel(
    {
        "query": lambda x: x["query"],
        "context": lambda x: context,
    }
    )
    chain = chain_inputs | prompt | chat_model | parser
    result = chain.invoke({'query':query})
    detection = detect_fake(context)
    return {'summary':result,'fake_news_detection':detection}