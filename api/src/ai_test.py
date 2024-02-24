from langchain.prompts import PromptTemplate
from langchain.schema import StrOutputParser
from langchain.schema.prompt_template import format_document
from langchain_community.document_loaders import WebBaseLoader
from langchain_google_genai import ChatGoogleGenerativeAI

from dotenv import load_dotenv

import json
import io


# TODO: handle error if API key is not found or is invalid
load_dotenv()


def get_url_from_json(json_file):
    with open(json_file, "r") as f:
        data = json.load(f)
        url = data["url"]
    return url

url = get_url_from_json("8e9fab5b92ad5b69bc90dd1af2df2bbdb775d38849bbfa852acca21d282937d5.json")
url2 = get_url_from_json("8cb1a0c96d04c3cc8d4c5dad1a9a40a7bf8235539543f8d4fd1814e9fcf93e90.json")

"""
Potential error
requests.exceptions.SSLError: HTTPSConnectionPool(host='wics.ics.uci.edu', port=443): Max retries exceeded with url: /wics-2018-bytes-of-code/ (Caused by SSLError(SSLCertVerificationError(1, '[SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: unable to get local issuer certificate (_ssl.c:1122)')))
"""
loader = WebBaseLoader(url2)
docs = loader.load()

# print(docs)

llm = ChatGoogleGenerativeAI(model="gemini-pro", temperature=0.1, top_p=0.5)

# To extract data from WebBaseLoader
doc_prompt = PromptTemplate.from_template("{page_content}")


# Prompt and chain adapted from
# https://github.com/google/generative-ai-docs/blob/main/examples/gemini/python/langchain/Gemini_LangChain_Summarization_WebLoad.ipynb

llm_prompt_template = """Write a concise summary of the following webpage:
"{text}"
CONCISE SUMMARY:"""
llm_prompt = PromptTemplate.from_template(llm_prompt_template)

# print(llm_prompt)

# Create Stuff documents chain using LCEL.
# This is called a chain because you are chaining
# together different elements with the LLM.
# In the following example, to create stuff chain,
# you will combine content, prompt, LLM model and
# output parser together like a chain using LCEL.
#
# The chain implements the following pipeline:
# 1. Extract data from documents and save to variable `text`.
# 2. This `text` is then passed to the prompt and input variable
#    in prompt is populated.
# 3. The prompt is then passed to the LLM (Gemini).
# 4. Output from the LLM is passed through an output parser
#    to structure the model response.

stuff_chain = (
    # Extract data from the documents and add to the key `text`.
    {"text": lambda docs: "\n\n".join(format_document(doc, doc_prompt) for doc in docs)}
    | llm_prompt  # Prompt for Gemini
    | llm  # Gemini function
    | StrOutputParser()  # output parser
)

output = stuff_chain.invoke(docs)
print(output)
