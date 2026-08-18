from langchain_community.document_loaders import TextLoader, PyMuPDFLoader, Docx2txtLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pathlib import Path
from langchain_community.document_loaders.parsers import RapidOCRBlobParser
from langchain_core.documents import Document
import re
import unicodedata
from ftfy import fix_text
from logger import logger
from config import config as cfg


def load_file(path):
    path = str(path)
    match Path(path).suffix.lower():
        case ".txt" | ".md":
            loader = TextLoader(path, encoding="utf-8",
                                autodetect_encoding=True)
        case ".pdf":
            loader = PyMuPDFLoader(path, mode="page", extract_tables="markdown",
                                   images_parser=RapidOCRBlobParser(), sort=True)
        case ".docx":
            loader = Docx2txtLoader(path)
        case ext:
            raise ValueError(f"Unsupported file type: {ext}")
    return loader.load()


def load_dir(folder, exts=(".txt", ".md", ".pdf", ".docx")):
    docs = []
    for p in Path(folder).rglob("*"):
        if p.is_file() and p.suffix.lower() in exts:
            try:
                docs.extend(load_file(p))
            except Exception as e:
                logger.warning("Skipped %s: %s", p, e)
    return docs


def load_and_split(path) -> list[Document]:
    docs = load_file(path)

    for d in docs:
        d.page_content = normalize_for_rag(fix_text(d.page_content))
        d.metadata["source"] = Path(path).name
        d.metadata["normalization"] = "nfkc-rag-v1"

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=cfg.chunk_size,
        chunk_overlap=cfg.chunk_overlap,
        separators=["\n\n", "\n", " ", ""],   # default
        length_function=len,
        add_start_index=True
    )

    # list[Document] -> list[Document]

    chunks = splitter.split_documents(docs)

    for i, c in enumerate(chunks):
        c.metadata["chunk_index"] = i

    return chunks


def normalize_for_rag(text: str) -> str:
    # Unicode compatibility normalization
    text = unicodedata.normalize("NFKC", text)

    # Convert NBSP to ordinary space
    text = text.replace("\u00a0", " ")
    text = text.replace("\t", " ")

    # Remove invisible / zero-width characters
    for char in ("\u200b", "\u200c", "\u200d", "\ufeff"):
        text = text.replace(char, "")

    # Standardize line endings
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # Remove control and format characters, except real newlines
    text = "".join(
        char
        for char in text
        if char == "\n" or unicodedata.category(char) not in {"Cc", "Cf"}
    )

    # Collapse spaces and tabs, but preserve newlines / paragraph boundaries
    text = re.sub(r"[^\S\n]+", " ", text)
    text = re.sub(r" *\n *", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


if __name__ == "__main__":
    logger.info("Running ingestion.py directly!")

    chunks = load_and_split(
        './docs/IIT Patna AIML Project Guidelines (1) (1).pdf')

    logger.info("Produced %d chunks", len(chunks))

    for c in chunks:
        logger.debug("chunk %s meta=%s content=%.100s",
                     c.metadata.get("chunk_index"), c.metadata, c.page_content)
