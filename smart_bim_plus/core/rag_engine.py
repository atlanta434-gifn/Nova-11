import os
import logging
from pathlib import Path

logger = logging.getLogger("SmartBIM.RAG")

class RAGEngine:
    """محرك Retrieval-Augmented Generation (RAG) لاستشارة الأكواد الهندسية"""

    def __init__(self, data_dir: str = "rag_data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.vector_store = None
        self.qa_chain = None
        self.is_ready = False
        self.has_api_key = "GOOGLE_API_KEY" in os.environ
        self.doc_count = 0

    def initialize_rag(self):
        if not self.has_api_key:
            logger.warning("GOOGLE_API_KEY not found. RAG will be disabled.")
            return

        try:
            from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
            from langchain_community.document_loaders import PyPDFDirectoryLoader
            from langchain_community.vectorstores import FAISS
            from langchain.text_splitter import RecursiveCharacterTextSplitter
            from langchain.chains import create_retrieval_chain
            from langchain.chains.combine_documents import create_stuff_documents_chain
            from langchain.prompts import ChatPromptTemplate
            
            logger.info(f"Loading documents from {self.data_dir}...")
            loader = PyPDFDirectoryLoader(str(self.data_dir))
            docs = loader.load()
            self.doc_count = len(docs)
            
            if not docs:
                logger.warning("No PDF documents found in rag_data. Add PDFs to enable RAG.")
                return
                
            text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
            splits = text_splitter.split_documents(docs)
            
            logger.info(f"Creating vector store for {len(splits)} chunks using Gemini Embeddings...")
            embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
            self.vector_store = FAISS.from_documents(splits, embeddings)
            
            llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0.2)
            
            prompt = ChatPromptTemplate.from_template(
                """أنت مهندس استشاري خبير في تطبيق NOVA BIM.
استخدم السياق التالي المستخرج من الأكواد الهندسية للإجابة على السؤال بدقة هندسية عالية.
إذا لم تكن الإجابة في السياق، اعتمد على المعايير الهندسية العالمية مثل (ASHRAE, NEC, IBC) ووضح ذلك.
أجب دائماً باللغة العربية.

السياق:
{context}

السؤال: {input}

الإجابة الهندسية:"""
            )
            
            combine_docs_chain = create_stuff_documents_chain(llm, prompt)
            self.qa_chain = create_retrieval_chain(
                self.vector_store.as_retriever(search_kwargs={"k": 4}), 
                combine_docs_chain
            )
            
            self.is_ready = True
            logger.info(f"RAG Engine initialized successfully with {self.doc_count} pages.")
            
        except Exception as e:
            logger.error(f"Failed to initialize RAG: {e}")
            
    def query(self, question: str) -> str:
        if not self.has_api_key:
            return "يرجى إضافة مفتاح GOOGLE_API_KEY للبيئة (Environment Variables) لتفعيل الذكاء الاصطناعي."
        if not self.is_ready:
            return "نظام (RAG) غير مفعل. تأكد من وضع ملفات PDF هندسية في مجلد rag_data وأعد تشغيل التطبيق."
        
        try:
            response = self.qa_chain.invoke({"input": question})
            return response.get("answer", "لم أتمكن من إيجاد إجابة.")
        except Exception as e:
            logger.error(f"RAG query failed: {e}")
            return f"حدث خطأ أثناء الاستعلام: {e}"
