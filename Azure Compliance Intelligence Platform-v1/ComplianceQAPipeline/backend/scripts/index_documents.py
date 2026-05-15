import hashlib
import logging
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, List

from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import AzureSearch
from langchain_core.documents import Document
from langchain_openai import AzureOpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter


load_dotenv(override=True)

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger("indexer")


@dataclass(frozen=True)
class Settings:
    azure_openai_endpoint: str
    azure_openai_api_key: str
    azure_openai_api_version: str
    azure_openai_embedding_deployment: str
    azure_search_endpoint: str
    azure_search_api_key: str
    azure_search_index_name: str
    data_folder: Path
    chunk_size: int = 1200
    chunk_overlap: int = 200
    batch_size: int = 100


def required_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def load_settings() -> Settings:
    current_dir = Path(__file__).resolve().parent

    return Settings(
        azure_openai_endpoint=required_env("AZURE_OPENAI_ENDPOINT"),
        azure_openai_api_key=required_env("AZURE_OPENAI_API_KEY"),
        azure_openai_api_version=required_env("AZURE_OPENAI_API_VERSION"),
        azure_openai_embedding_deployment=os.getenv(
            "AZURE_OPENAI_EMBEDDING_DEPLOYMENT",
            "text-embedding-3-large",
        ),
        azure_search_endpoint=required_env("AZURE_SEARCH_ENDPOINT"),
        azure_search_api_key=required_env("AZURE_SEARCH_API_KEY"),
        azure_search_index_name=required_env("AZURE_SEARCH_INDEX_NAME"),
        data_folder=Path(
            os.getenv("PDF_DATA_FOLDER", current_dir / "../../backend/data")
        ).resolve(),
        chunk_size=int(os.getenv("CHUNK_SIZE", "1000")),
        chunk_overlap=int(os.getenv("CHUNK_OVERLAP", "200")),
        batch_size=int(os.getenv("INDEX_BATCH_SIZE", "100")),
    )


def find_pdfs(data_folder: Path) -> List[Path]:
    if not data_folder.exists():
        raise RuntimeError(f"Data folder does not exist: {data_folder}")

    pdfs = sorted(data_folder.glob("*.pdf"))

    if not pdfs:
        logger.warning(f"No PDFs found in {data_folder}. Please add files.")
    else:
        logger.info(f"Found {len(pdfs)} PDFs to process: {[p.name for p in pdfs]}")

    return pdfs


def hash_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def load_and_split_pdf(
    pdf_path: Path,
    splitter: RecursiveCharacterTextSplitter,
) -> List[Document]:
    logger.info(f"Loading: {pdf_path.name}...")

    loader = PyPDFLoader(str(pdf_path))
    raw_docs = loader.load()

    splits = splitter.split_documents(raw_docs)
    indexed_at = datetime.now(timezone.utc).isoformat()

    for index, doc in enumerate(splits):
        page = doc.metadata.get("page")

        doc.metadata.update(
            {
                "source": pdf_path.name,
                "source_path": str(pdf_path),
                "page": page,
                "chunk_index": index,
                "content_hash": hash_text(doc.page_content),
                "indexed_at": indexed_at,
            }
        )

        # Optional stable ID if your Azure Search schema supports it.
        doc.metadata["chunk_id"] = (
            f"{pdf_path.stem}-p{page}-c{index}-{doc.metadata['content_hash']}"
        )

    logger.info(f" -> Split into {len(splits)} chunks.")
    return splits


def batched(items: List[Document], batch_size: int) -> Iterable[List[Document]]:
    for start in range(0, len(items), batch_size):
        yield items[start : start + batch_size]


def build_embeddings(settings: Settings) -> AzureOpenAIEmbeddings:
    logger.info("Initializing Azure OpenAI Embeddings...")
    embeddings = AzureOpenAIEmbeddings(
        azure_deployment=settings.azure_openai_embedding_deployment,
        azure_endpoint=settings.azure_openai_endpoint,
        api_key=settings.azure_openai_api_key,
        api_version=settings.azure_openai_api_version,
    )
    logger.info("✓ Embeddings model initialized successfully")
    return embeddings


def build_vector_store(
    settings: Settings,
    embeddings: AzureOpenAIEmbeddings,
) -> AzureSearch:
    logger.info("Initializing Azure AI Search vector store...")
    vector_store = AzureSearch(
        azure_search_endpoint=settings.azure_search_endpoint,
        azure_search_key=settings.azure_search_api_key,
        index_name=settings.azure_search_index_name,
        embedding_function=embeddings.embed_query,
    )
    logger.info(f"✓ Vector store initialized for index: {settings.azure_search_index_name}")
    return vector_store


def index_documents() -> None:
    try:
        settings = load_settings()
    except RuntimeError as e:
        logger.error(str(e))
        logger.error("Please check your .env file and ensure all variables are set.")
        return

    logger.info("=" * 60)
    logger.info("Environment Configuration Check:")
    logger.info(f"AZURE_OPENAI_ENDPOINT: {settings.azure_openai_endpoint}")
    logger.info(f"AZURE_OPENAI_API_VERSION: {settings.azure_openai_api_version}")
    logger.info(f"Embedding Deployment: {settings.azure_openai_embedding_deployment}")
    logger.info(f"AZURE_SEARCH_ENDPOINT: {settings.azure_search_endpoint}")
    logger.info(f"AZURE_SEARCH_INDEX_NAME: {settings.azure_search_index_name}")
    logger.info("=" * 60)

    try:
        embeddings = build_embeddings(settings)
    except Exception as e:
        logger.error(f"Failed to initialize embeddings: {e}")
        logger.error("Please verify your Azure OpenAI deployment name and endpoint.")
        return

    try:
        vector_store = build_vector_store(settings, embeddings)
    except Exception as e:
        logger.error(f"Failed to initialize Azure Search: {e}")
        logger.error("Please verify your Azure Search endpoint, API key, and index name.")
        return

    try:
        pdfs = find_pdfs(settings.data_folder)
    except RuntimeError as e:
        logger.warning(str(e))
        return

    if not pdfs:
        return

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
    )

    all_documents: List[Document] = []

    for pdf in pdfs:
        try:
            all_documents.extend(load_and_split_pdf(pdf, splitter))
        except Exception as e:
            logger.error(f"Failed to process {pdf.name}: {e}")

    if not all_documents:
        logger.warning("No documents were processed.")
        return

    logger.info(f"Uploading {len(all_documents)} chunks to Azure AI Search Index '{settings.azure_search_index_name}'...")

    uploaded = 0

    try:
        for batch_number, batch in enumerate(
            batched(all_documents, settings.batch_size),
            start=1,
        ):
            vector_store.add_documents(batch)
            uploaded += len(batch)
            
        logger.info("=" * 60)
        logger.info("✅ Indexing Complete! The Knowledge Base is ready.")
        logger.info(f"Total chunks indexed: {uploaded}")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"Failed to upload documents to Azure Search: {e}")
        logger.error("Please check your Azure Search configuration and try again.")


if __name__ == "__main__":
    index_documents()