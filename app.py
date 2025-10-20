import os
from fastapi import FastAPI
from fastapi.responses import JSONResponse,FileResponse
from model import preprocessor
from pydantic import BaseModel


app = FastAPI(title = "News Summarization and Detection")

@app.get("/")
def read_index():
    return FileResponse(os.path.join(os.path.dirname(__file__), "templates/index.html"))



class Query(BaseModel):
    query:str

@app.post('/ask')
def ask(data:Query):
    articles = preprocessor.build_articles(data.query, max_results=10)
    docs = preprocessor.build_documents(articles)
    vc = preprocessor.build_vectorstore(docs)
    retriever = vc.as_retriever(search_type='similarity', search_kwargs={'k': 4})
    result = preprocessor.summarize(query = data.query,retriever = retriever)
    return JSONResponse(status_code = 200, content = result)